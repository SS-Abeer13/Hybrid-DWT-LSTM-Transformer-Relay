from pathlib import Path
p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
old = s[s.index("if any(loadWin)\n    rec.loadRealisedPct"):s.index("% detectability: rise of the relay's compensated")]
new = """if any(loadWin)
    % TRUE line currents (V-I measurement blocks): independent of CT saturation / burden / mismatch
    lsg0 = out.get('logsout');
    [iP0, tP0] = loggedSignal(lsg0, 'TruePrimI'); [iS0, ~] = loggedSignal(lsg0, 'TrueSecI');
    tHi = t(find(loadWin, 1, 'first')); tLo = t(find(loadWin, 1, 'last'));
    wT = tP0 >= tHi & tP0 <= tLo;
    pH = mean(sqrt(mean(iP0(wT, :) .^ 2, 1))) / 753.06; pL = mean(sqrt(mean(iS0(wT, :) .^ 2, 1))) / 15745.9;
    rec.loadRealisedPct = 100 * 0.5 * (pH + pL);
    target = 100 * p.loadPu;
    rec.loadOK = double(abs(rec.loadRealisedPct - target) <= max(cfg.loadTolPct / 100 * target, 2));
end

"""
s = s.replace(old, new)
s = s.replace("cfg.version   = 'v3-2026-10-21-A3';", "cfg.version   = 'v3-2026-10-21-A3b';")
p.write_text(s, encoding="utf-8"); print("A3b applied")
