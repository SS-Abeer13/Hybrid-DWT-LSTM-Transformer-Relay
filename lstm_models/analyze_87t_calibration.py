"""Quantifies the conventional 87T path of the Simulink relay on the v2 stress dataset: relay compensation as coded (A), matrix fixed only (B),
matrix fixed + common per-unit base estimated from healthy traces (C). Per-sample 1-cycle RMS (32 samples; the RMS block window was not
verified in the .slx), trip vote = Hybrid_87T_Decision logic (pickup 0.3, slopes 0.25/0.6, breakpoint 3, high-set 10). Run from the project root:
    set PYTHONPATH=.pylibs  &&  python lstm_models/analyze_87t_calibration.py
"""
import sys; sys.path.insert(0,'lstm_models')
import numpy as np
from pathlib import Path
from collections import defaultdict
from stress_dataset import load_traces
import features12 as F
Tr=[t for t in load_traces(Path('datasets/StressDataset_v2_20261020_005715.mat')) if t.get('checkPassed',1)]
M=F.M_YD1; W=32; FS=1600
# estimate true nominal secondary amps from healthy Normal traces: rms(sec)/loadPu
est=[]
for t in Tr:
    if t['scenarioName']=='Normal':
        s=t['secondary'][800:]; est.append(np.sqrt((s**2).mean())/t['loadPu'])
Inom=float(np.median(est)); print('estimated true nominal CT-secondary amps (1 pu load): %.3f A (spread %.3f-%.3f) | relay assumes HV %.3f / LV %.3f'%(Inom,np.percentile(est,10),np.percentile(est,90),F.I_NOM_HV,F.I_NOM_LV))
def rms(x):
    c=np.cumsum(np.vstack([np.zeros((1,3)),x**2]),0); n=len(x); out=np.full((n,3),np.nan)
    out[W-1:]=np.sqrt((c[W:]-c[:-W])/W); return out
def vote(Id,Ir):
    Ip,hs,s1,s2,bp=0.30,10.0,0.25,0.60,3.0
    dyn=np.where(Ir<=bp,s1*Ir,s2*(Ir-bp)+s1*bp)
    v=(Id>Ip)&(Id>dyn)
    return np.nan_to_num(v.any(1)), np.nan_to_num((Id>hs).any(1))
def variants(p,s):
    out={}
    hv=p/F.I_NOM_HV; lv=s/F.I_NOM_LV
    hvc=hv@M.T; d=lv-hvc; ir=0.5*(np.abs(hvc)+np.abs(lv)); out['A relay as coded']=(d,ir)
    # B: plant matrix, relay's bases
    hvc=hv@M; d=lv-hvc; ir=0.5*(np.abs(hvc)+np.abs(lv)); out['B matrix fixed only']=(d,ir)
    # C: plant matrix + common base
    hvc=(p@M)/Inom; lvn=s/Inom; d=lvn-hvc; ir=0.5*(np.abs(hvc)+np.abs(lvn)); out['C matrix + common base']=(d,ir)
    return out
res=defaultdict(lambda: defaultdict(list))
for t in Tr:
    p,s=t['primary'],t['secondary']; cat=t['scenarioName'].split('_')[0]
    on=int(round(t['inceptionTime']*FS)) if t['should_trip'] and np.isfinite(t.get('inceptionTime',np.nan)) else -1
    for k,(d,ir) in variants(p,s).items():
        v,hs=vote(rms(d),rms(ir))
        v=v|hs
        n=len(v)
        if t['should_trip']:
            if t.get('faultDiffPu',1)<0.05: continue
            pre=v[W:max(on,W+1)].any() if on>W else False
            post=v[on:on+2*W].any()     # within 2 cycles
            res[k]['fault_pre'].append(pre); res[k]['fault_det2cyc'].append(post)
        else:
            res[k]['healthy_any_vote'].append(v[W:].any())
            res[k]['healthy_frac_time'].append(v[W:].mean())
            if cat=='Normal': res[k]['normal_vote'].append(v[W:].any())
for k,d in res.items():
    print(f"\n{k}")
    print(f"  healthy traces with ANY 87T vote : {100*np.mean(d['healthy_any_vote']):5.1f}%  (n={len(d['healthy_any_vote'])}) | mean fraction of time voting {100*np.mean(d['healthy_frac_time']):.1f}%")
    print(f"  Normal traces with a vote        : {100*np.mean(d['normal_vote']):5.1f}%")
    print(f"  faults voting BEFORE onset       : {100*np.mean(d['fault_pre']):5.1f}%")
    print(f"  faults detected by 87T <=2 cycles: {100*np.mean(d['fault_det2cyc']):5.1f}%  (n={len(d['fault_det2cyc'])})")

print("\n=== variant C, healthy traces with any 87T vote by category, and base-current sensitivity ===")
def runC(base):
    byc=defaultdict(list); fdet=[]
    for t in Tr:
        p,s=t['primary'],t['secondary']
        d=(s-p@M)/base; ir=0.5*(np.abs(p@M)/base+np.abs(s)/base)
        v,hs=vote(rms(d),rms(ir)); v=v|hs
        if not t['should_trip']: byc[t['scenarioName'].split('_')[0]+('' if not t['scenarioName'].startswith('Stress') else '*')].append(v[W:].any())
        elif t.get('faultDiffPu',1)>=0.05 and np.isfinite(t.get('inceptionTime',np.nan)):
            on=int(round(t['inceptionTime']*FS)); fdet.append(v[on:on+2*W].any())
    return byc,np.mean(fdet)
for base in (Inom,0.55,0.84):
    byc,fd=runC(base)
    print(f"base {base:.3f} A: faults det <=2cyc {100*fd:.1f}% | "+", ".join(f"{k} {100*np.mean(v):.0f}% (n={len(v)})" for k,v in sorted(byc.items())))
