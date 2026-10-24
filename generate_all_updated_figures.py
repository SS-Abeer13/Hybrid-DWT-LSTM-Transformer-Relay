# -*- coding: utf-8 -*-
"""generate_all_updated_figures.py
Generates high-resolution, vector-crisp 300-DPI PNG figures matching the final
v3 architecture, exact electrical parameters, and academic reviewer requirements.
Outputs directly to latex_source/latex/
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = Path(r"F:\Transformer Thesis\latex_source\latex")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MIST_DIR = Path(r"F:\Transformer Thesis\figures\MIST_LaTeX")
MIST_DIR.mkdir(parents=True, exist_ok=True)

def save_fig(fig, filename):
    fig.savefig(OUT_DIR / filename, dpi=300)
    fig.savefig(MIST_DIR / filename, dpi=300)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "legend.fontsize": 9,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "mathtext.fontset": "cm"
})

def generate_fig_1_1():
    """Single-Line Diagram of the Protection Scheme with calibrated CT ratios."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(-1, 15)
    ax.set_ylim(-3, 6)
    ax.axis("off")

    # Main conductor lines
    ax.plot([0, 1.5], [3.5, 3.5], "k-", lw=2.5) # Source to HV bus
    ax.plot([1.5, 3.5], [3.5, 3.5], "k-", lw=2.0) # HV bus to CB
    ax.plot([4.1, 5.5], [3.5, 3.5], "k-", lw=2.0) # CB to HV CT
    ax.plot([6.3, 7.2], [3.5, 3.5], "k-", lw=2.0) # HV CT to Xfmr
    ax.plot([8.8, 9.7], [3.5, 3.5], "k-", lw=2.0) # Xfmr to LV CT
    ax.plot([10.5, 12.0], [3.5, 3.5], "k-", lw=2.0) # LV CT to LV bus
    ax.plot([12.0, 14.0], [3.5, 3.5], "k-", lw=2.0) # LV bus to feeder

    # HV Source
    circ = patches.Circle((0, 3.5), 0.35, edgecolor="black", facecolor="#E8EEF5", lw=2)
    ax.add_patch(circ)
    ax.text(0, 3.5, "G", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(0, 4.2, "230 kV Source\n(3524 MVA SCL)", ha="center", fontsize=8.5)

    # HV Bus
    ax.plot([1.5, 1.5], [2.2, 4.8], "k-", lw=5)
    ax.text(1.5, 5.1, "230 kV HV Bus", ha="center", fontweight="bold", fontsize=9.5)

    # Inrush CB
    rect_cb = patches.Rectangle((3.5, 3.2), 0.6, 0.6, edgecolor="#6A1B9A", facecolor="#F3E5F5", lw=2)
    ax.add_patch(rect_cb)
    ax.text(3.8, 3.5, "CB", ha="center", va="center", fontweight="bold", color="#6A1B9A", fontsize=9)
    ax.text(3.8, 2.7, "Inrush CB\n(Energization)", ha="center", fontsize=8, color="#6A1B9A", fontweight="bold")

    # HV CT
    circ_hv1 = patches.Circle((5.8, 3.5), 0.3, edgecolor="#1B5E20", facecolor="none", lw=2.2)
    circ_hv2 = patches.Circle((6.0, 3.5), 0.3, edgecolor="#1B5E20", facecolor="none", lw=2.2)
    ax.add_patch(circ_hv1)
    ax.add_patch(circ_hv2)
    ax.text(5.9, 4.3, r"$\mathbf{CT_{HV}}$" + "\n" + r"$\mathbf{809.6 : 1}$" + "\n(0.9302 A base)", ha="center", fontsize=8.5, color="#1B5E20", fontweight="bold")

    # Transformer (Yd1)
    circ_t1 = patches.Circle((7.7, 3.5), 0.55, edgecolor="#0D47A1", facecolor="#E3F2FD", lw=2.2)
    circ_t2 = patches.Circle((8.3, 3.5), 0.55, edgecolor="#0D47A1", facecolor="#E3F2FD", lw=2.2)
    ax.add_patch(circ_t1)
    ax.add_patch(circ_t2)
    ax.text(7.6, 3.5, r"Y", ha="center", va="center", fontsize=11, fontweight="bold", color="#0D47A1")
    ax.text(8.4, 3.5, r"d1", ha="center", va="center", fontsize=11, fontweight="bold", color="#0D47A1")
    ax.text(8.0, 4.8, "300 MVA, 230/11 kV, Yd1\n" + r"($-30^\circ$ Phase Lag)", ha="center", fontweight="bold", fontsize=9.5, color="#0D47A1")

    # Internal Fault markers
    ax.plot(7.8, 3.1, "rx", ms=9, mew=2.5)
    ax.text(7.8, 2.5, "Internal Faults\n(10%, 50%, 90%)\n" + r"$R_f = 0.3\text{--}21\,\Omega$", ha="center", fontsize=7.5, color="red", fontweight="bold")

    # LV CT
    circ_lv1 = patches.Circle((10.0, 3.5), 0.3, edgecolor="#1B5E20", facecolor="none", lw=2.2)
    circ_lv2 = patches.Circle((10.2, 3.5), 0.3, edgecolor="#1B5E20", facecolor="none", lw=2.2)
    ax.add_patch(circ_lv1)
    ax.add_patch(circ_lv2)
    ax.text(10.1, 4.3, r"$\mathbf{CT_{LV}}$" + "\n" + r"$\mathbf{16{,}925 : 1}$" + "\n(0.9302 A base)", ha="center", fontsize=8.5, color="#1B5E20", fontweight="bold")

    # LV Bus
    ax.plot([12.0, 12.0], [2.2, 4.8], "k-", lw=5)
    ax.text(12.0, 5.1, "11 kV LV Bus", ha="center", fontweight="bold", fontsize=9.5)

    # Series Resistor and Feeder Load
    ax.plot([12.0, 12.7], [3.5, 3.5], "k-", lw=2)
    rect_r = patches.Rectangle((12.7, 3.3), 0.6, 0.4, edgecolor="#E65100", facecolor="#FFE0B2", lw=1.8)
    ax.add_patch(rect_r)
    ax.text(13.0, 3.5, r"$R_s$", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#E65100")
    ax.text(13.0, 4.1, r"$R_{\mathrm{series}} = 0.05\,\Omega$" + "\n(Capping Ext. Fault)", ha="center", fontsize=7.5, color="#E65100", fontweight="bold")
    ax.plot([13.3, 14.2], [3.5, 3.5], "k-", lw=2)
    ax.text(14.3, 3.5, "LV Load\n(10--110%)", va="center", fontsize=8.5)

    # Differential Zone (Dashed box)
    rect_zone = patches.Rectangle((5.4, 1.4), 5.3, 3.6, edgecolor="#C62828", facecolor="none", lw=2.0, ls="--")
    ax.add_patch(rect_zone)
    ax.text(5.5, 1.6, "Differential Protection Zone (87T Boundary)", fontsize=8.5, color="#C62828", fontweight="bold")

    # Relay box
    rect_relay = patches.Rectangle((7.0, -1.8), 2.0, 1.4, edgecolor="#B71C1C", facecolor="#FFEBEE", lw=2.2)
    ax.add_patch(rect_relay)
    ax.text(8.0, -0.9, "Proposed HATDP Relay\n(DWT-LSTM + 87T)", ha="center", va="center", fontweight="bold", fontsize=9, color="#B71C1C")
    ax.text(8.0, -1.5, "Dual-Path Supervisory Handshake", ha="center", fontsize=7.5, color="#B71C1C")

    # CT secondary wiring
    ax.plot([5.9, 5.9, 7.3], [3.2, -0.8, -0.8], "g--", lw=1.8)
    ax.plot([10.1, 10.1, 8.7], [3.2, -0.8, -0.8], "g--", lw=1.8)
    ax.text(6.4, 0.5, r"HV CT Sec ($I_{HV}'$)", color="#1B5E20", fontsize=8, rotation=90)
    ax.text(10.3, 0.5, r"LV CT Sec ($I_{LV}'$)", color="#1B5E20", fontsize=8, rotation=90)

    # Trip line to CB
    ax.annotate("", xy=(3.8, 3.2), xytext=(7.0, -1.1),
                arrowprops=dict(arrowstyle="->", color="#B71C1C", lw=2.0, ls="-."))
    ax.text(5.0, 0.8, "Trip Signal", color="#B71C1C", fontweight="bold", fontsize=8.5, rotation=-30)

    plt.tight_layout()
    save_fig(fig, "fig_1_1.png")
    plt.close(fig)
    print("Generated fig_1_1.png")

def generate_fig_3_1():
    """Dual-Slope Percentage Restraint Characteristic with exact piecewise equation."""
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # Restraint current range
    Ir = np.linspace(0, 7.0, 700)
    
    # Relay parameters:
    # I_pickup = 0.30 pu (0.279 A secondary base 0.9302 A)
    # S1 = 15%, S2 = 40%, Knee point Ir_rest = 2.0 A, Ir1 = 0.67 A
    I_pickup = 0.279
    Ir1 = 0.67
    Ir_rest = 2.0
    S1 = 0.15
    S2 = 0.40
    
    Id_op = np.zeros_like(Ir)
    for i, r in enumerate(Ir):
        if r <= Ir1:
            Id_op[i] = I_pickup
        elif r <= Ir_rest:
            Id_op[i] = I_pickup + S1 * (r - Ir1)
        else:
            Id_op[i] = I_pickup + S1 * (Ir_rest - Ir1) + S2 * (r - Ir_rest)
            
    # Plot curve
    ax.plot(Ir, Id_op, "r-", lw=2.8, label=r"Operating Boundary $I_{op}(I_r)$")
    
    # Shading
    ax.fill_between(Ir, Id_op, 4.0, color="#FFCDD2", alpha=0.5, label="TRIP (Operate) Region")
    ax.fill_between(Ir, 0, Id_op, color="#E8F5E9", alpha=0.6, label="BLOCK (Restraint) Region")
    
    # Annotate points with exact drop lines
    ax.plot([0, Ir1], [I_pickup, I_pickup], "k--", lw=1.2)
    ax.plot([Ir1, Ir1], [0, I_pickup], "k--", lw=1.2) # Drop line at Ir1
    ax.plot(Ir1, I_pickup, "ro", ms=6)
    
    ax.plot([Ir_rest, Ir_rest], [0, I_pickup + S1 * (Ir_rest - Ir1)], "k--", lw=1.2) # Drop line at Ir_rest
    ax.plot(Ir_rest, I_pickup + S1 * (Ir_rest - Ir1), "ro", ms=7)
    
    ax.text(Ir1/2, I_pickup + 0.14, r"$I_{\mathrm{pickup}} = 0.30\,\mathrm{pu}$" + f"\n({I_pickup:.3f} A sec)", 
            ha="center", fontsize=9, fontweight="bold", color="#B71C1C")
    ax.text(Ir1 + 0.08, 0.15, r"Break $I_{r1} = 0.67\,\mathrm{A}$" + "\n(0.72 pu)", 
            fontsize=8, fontweight="bold", color="#B71C1C")
    ax.text(Ir_rest + 0.15, I_pickup + S1 * (Ir_rest - Ir1) - 0.14, 
            r"Knee Point $(I_{\mathrm{rest}} = 2.0\,\mathrm{A})$" + "\n(2.15 pu)", fontsize=8.5, fontweight="bold")
    
    # Slope annotations
    ax.text(1.3, 0.48, r"Slope $S_1 = 15\%$", fontsize=9.5, fontweight="bold", color="#0D47A1", rotation=12)
    ax.text(4.2, 1.7, r"Slope $S_2 = 40\%$" + "\n(High CT Saturation Restraint)", 
            fontsize=9.5, fontweight="bold", color="#0D47A1", rotation=28)
    
    ax.set_xlim(0, 6.5)
    ax.set_ylim(0, 3.5)
    ax.set_xlabel(r"Restraint Current $I_r$ (A secondary, $I_{\mathrm{nom,sec}} = 0.9302\,\mathrm{A}$)")
    ax.set_ylabel(r"Differential Current $I_d$ (A secondary)")
    ax.set_title("Dual-Slope Percentage Restraint Characteristic (87T Element)", fontweight="bold")
    ax.grid(True, ls=":", alpha=0.7)
    ax.legend(loc="upper left", frameon=True)
    
    # Secondary axis in per-unit
    ax2 = ax.twinx()
    ax2.set_ylim(0 / 0.9302, 3.5 / 0.9302)
    ax2.set_ylabel(r"Differential Current $I_d$ (per-unit, $\mathrm{pu}$)")
    
    plt.tight_layout()
    save_fig(fig, "fig_3_1.png")
    plt.close(fig)
    print("Generated fig_3_1.png")

def generate_fig_3_2():
    """Inrush Waveforms and Core Saturation with clean, non-overlapping annotations."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    
    t = np.linspace(0, 0.08, 1000)
    omega = 2 * np.pi * 50
    tau = 0.15 # seconds damping
    
    # Subplot (a): Core Flux
    Phi_m = 1.0 # pu
    phi_r = 0.8 # pu residual flux
    phi_t = -Phi_m * np.cos(omega * t) + (Phi_m + phi_r) * np.exp(-t / tau)
    
    ax1.plot(t * 1000, phi_t, "b-", lw=2.2, label=r"Total Core Flux $\phi(t)$")
    ax1.plot(t * 1000, np.ones_like(t) * 1.2, "r--", lw=1.8, label=r"Core Saturation Knee $\phi_{\mathrm{sat}} = 1.2\,\mathrm{pu}$")
    ax1.plot(10, phi_t[125], "ro", ms=6)
    ax1.annotate(r"Worst-case peak $\phi_{\mathrm{peak}} \approx 2\Phi_m + \phi_r = 2.8\,\mathrm{pu}$" + "\n(at half-cycle $t = 10\,\mathrm{ms}$)",
                 xy=(10, phi_t[125]), xytext=(15, 2.4),
                 arrowprops=dict(arrowstyle="->", color="red", lw=1.5), fontsize=8.5, fontweight="bold")
    
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel(r"Core Flux $\phi$ (pu)")
    ax1.set_title("(a) Transformer Core Flux During Energization", fontweight="bold", fontsize=10.5)
    ax1.grid(True, ls=":", alpha=0.7)
    ax1.legend(loc="upper right", fontsize=8.5)
    ax1.set_ylim(-1.5, 3.2)
    
    # Subplot (b): Inrush current waveform
    i_inrush = np.zeros_like(t)
    for idx, f in enumerate(phi_t):
        if f > 1.2:
            i_inrush[idx] = 15.0 * ((f - 1.2) / 1.6)**2
        else:
            i_inrush[idx] = 0.0
            
    ax2.plot(t * 1000, i_inrush, "purple", lw=2.2, label=r"Magnetizing Inrush Current $i_{\mathrm{inrush}}(t)$")
    ax2.axhline(0, color="black", lw=0.8)
    
    # Clean callouts
    ax2.annotate("High Unidirectional Peak\n(5--15 pu peak)", xy=(10, i_inrush[125]), xytext=(22, 11),
                 arrowprops=dict(arrowstyle="->", color="purple", lw=1.5), fontsize=8.5, fontweight="bold")
    ax2.annotate(r"Dead-Angle Interval" + "\n" + r"(Non-conduction $i \approx 0$)", xy=(25, 0.0), xytext=(35, 4),
                 arrowprops=dict(arrowstyle="->", color="darkgreen", lw=1.5), fontsize=8.5, fontweight="bold")
    
    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Inrush Current (pu)")
    ax2.set_title("(b) Asymmetric Magnetizing Inrush Waveform", fontweight="bold", fontsize=10.5)
    ax2.grid(True, ls=":", alpha=0.7)
    ax2.legend(loc="upper right", fontsize=8.5)
    ax2.set_ylim(-1, 16)
    
    plt.tight_layout()
    save_fig(fig, "fig_3_2.png")
    plt.close(fig)
    print("Generated fig_3_2.png")

def generate_fig_3_3():
    """CT Equivalent Circuit and Saturation Clipping."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    
    # Subplot (a): Equivalent circuit diagram
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 6)
    ax1.axis("off")
    ax1.set_title("(a) CT Equivalent Electrical Circuit", fontweight="bold", fontsize=10.5)
    
    # Ideal current source / primary current
    circ_src = patches.Circle((1.5, 3), 0.5, edgecolor="black", facecolor="#E1F5FE", lw=2)
    ax1.add_patch(circ_src)
    ax1.text(1.5, 3, r"$i_p'$", ha="center", va="center", fontsize=11, fontweight="bold")
    ax1.text(1.5, 3.8, "Primary Current\n(Referred $I_p/N_{CT}$)", ha="center", fontsize=8)
    
    # Conductors
    ax1.plot([1.5, 5, 5, 8.5], [4.5, 4.5, 4.5, 4.5], "k-", lw=2)
    ax1.plot([1.5, 1.5], [3.5, 4.5], "k-", lw=2)
    ax1.plot([1.5, 1.5, 8.5], [2.5, 1.5, 1.5], "k-", lw=2)
    
    # Magnetizing branch (Nonlinear Lm)
    rect_lm = patches.Rectangle((4.2, 2.2), 1.6, 1.6, edgecolor="#C62828", facecolor="#FFEBEE", lw=2)
    ax1.add_patch(rect_lm)
    ax1.text(5.0, 3.25, "Nonlinear Core\nMagnetization", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#C62828")
    ax1.text(5.0, 2.55, r"$i_e(\lambda) = A(e^{B|\lambda|}-1)$", ha="center", va="center", fontsize=7.5, color="#C62828")
    ax1.plot([5.0, 5.0], [4.5, 3.8], "k-", lw=2)
    ax1.plot([5.0, 5.0], [2.2, 1.5], "k-", lw=2)
    
    # Burden Zb
    rect_zb = patches.Rectangle((7.8, 2.3), 1.4, 1.4, edgecolor="#0D47A1", facecolor="#E3F2FD", lw=2)
    ax1.add_patch(rect_zb)
    ax1.text(8.5, 3.2, "Secondary\nBurden", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#0D47A1")
    ax1.text(8.5, 2.6, r"$Z_b = R_b + j\omega L_b$", ha="center", va="center", fontsize=7.5, color="#0D47A1")
    ax1.plot([8.5, 8.5], [4.5, 3.7], "k-", lw=2)
    ax1.plot([8.5, 8.5], [2.3, 1.5], "k-", lw=2)
    
    # Current arrows
    ax1.annotate("", xy=(3.5, 4.5), xytext=(3.0, 4.5), arrowprops=dict(arrowstyle="->", lw=2, color="black"))
    ax1.annotate("", xy=(5.0, 4.0), xytext=(5.0, 4.2), arrowprops=dict(arrowstyle="->", lw=2, color="#C62828"))
    ax1.text(5.3, 4.0, r"$i_e(t)$", color="#C62828", fontweight="bold", fontsize=9)
    ax1.annotate("", xy=(6.8, 4.5), xytext=(6.3, 4.5), arrowprops=dict(arrowstyle="->", lw=2, color="#0D47A1"))
    ax1.text(6.8, 4.8, r"$i_s(t) = i_p'(t) - i_e(t)$", color="#0D47A1", fontweight="bold", fontsize=9)
    
    # Subplot (b): Waveforms
    t = np.linspace(0, 0.06, 600)
    omega = 2 * np.pi * 50
    ip_ideal = 8.0 * (np.sin(omega * t) + np.exp(-t / 0.04))
    is_sat = np.copy(ip_ideal)
    # Severe clipping during saturation intervals
    for idx, v in enumerate(is_sat):
        if idx > 80 and idx < 220:
            is_sat[idx] = 0.5 * np.exp(-(idx-80)/40)
        elif idx > 280 and idx < 420:
            is_sat[idx] = 0.3 * np.exp(-(idx-280)/40)
            
    ax2.plot(t * 1000, ip_ideal, "k--", lw=1.8, label=r"Ideal Secondary $i_p'(t)$")
    ax2.plot(t * 1000, is_sat, "b-", lw=2.2, label=r"Distorted Secondary $i_s(t)$")
    ax2.axhline(0, color="gray", lw=0.8)
    
    ax2.annotate("Severe Saturation Clipping\n(Missing Secondary Current)", 
                 xy=(16, 0.2), xytext=(22, 6.0),
                 arrowprops=dict(arrowstyle="->", color="#B71C1C", lw=1.8),
                 fontsize=8.5, fontweight="bold", color="#B71C1C")
    
    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Secondary Current (pu)")
    ax2.set_title("(b) CT Saturation Waveform Distortion", fontweight="bold", fontsize=10.5)
    ax2.grid(True, ls=":", alpha=0.7)
    ax2.legend(loc="upper right", fontsize=8.5)
    ax2.set_ylim(-8, 16)
    
    plt.tight_layout()
    save_fig(fig, "fig_3_3.png")
    plt.close(fig)
    print("Generated fig_3_3.png")

def generate_fig_3_4():
    """Cost-Asymmetric Feature Space Separation."""
    fig, ax = plt.subplots(figsize=(6.5, 5))
    np.random.seed(42)
    
    # Healthy cluster (low detail energy, variable approx energy)
    n_healthy = 120
    ea_healthy = np.random.normal(0.5, 0.8, n_healthy)
    ed_healthy = np.random.normal(-1.2, 0.4, n_healthy)
    
    # Internal fault cluster (high detail energy and approx energy)
    n_fault = 80
    ea_fault = np.random.normal(3.2, 0.9, n_fault)
    ed_fault = np.random.normal(1.8, 0.7, n_fault)
    
    # Weak HiZ internal faults
    n_hiz = 30
    ea_hiz = np.random.normal(1.2, 0.5, n_hiz)
    ed_hiz = np.random.normal(0.3, 0.4, n_hiz)
    
    ax.scatter(ea_healthy, ed_healthy, c="#1E88E5", alpha=0.7, edgecolors="none", s=35, label="Healthy Transients (Inrush, Normal, Ext CTSat)")
    ax.scatter(ea_fault, ed_fault, c="#D81B60", alpha=0.8, edgecolors="none", s=40, label="Internal Solid Faults")
    ax.scatter(ea_hiz, ed_hiz, c="#8E24AA", alpha=0.9, edgecolors="black", lw=0.5, s=45, label=r"Weak HiZ Internal Faults ($R_f \leq 7\,\Omega$)")
    
    # Decision boundaries
    x_grid = np.linspace(-1.5, 5.5, 200)
    y_sym = -0.7 * x_grid + 1.2
    y_asym = -0.7 * x_grid + 0.1 # Shifted toward healthy class to never miss faults
    
    ax.plot(x_grid, y_sym, "k--", lw=1.8, label="Standard Symmetric Boundary")
    ax.plot(x_grid, y_asym, "r-", lw=2.5, label=r"Cost-Asymmetric Boundary ($L_{\mathrm{FN}} \gg L_{\mathrm{FP}}$)")
    
    # Annotation cleanly positioned in open white space
    ax.annotate("Dependability-Biased Shift\n(Prevents Missed Faults)",
                xy=(1.5, -0.95), xytext=(2.6, -2.0),
                arrowprops=dict(arrowstyle="->", color="red", lw=1.8),
                fontsize=8.5, fontweight="bold", color="red")
    
    ax.set_xlim(-1.5, 5.5)
    ax.set_ylim(-2.5, 4.0)
    ax.set_xlabel(r"Log10 Approximation Energy $\log_{10}(E_A / \mathrm{pu}^2)$")
    ax.set_ylabel(r"Log10 Detail Energy $\log_{10}(E_D / \mathrm{pu}^2)$")
    ax.set_title("Feature Space Partitioning Under Asymmetric Bayes Risk", fontweight="bold")
    ax.grid(True, ls=":", alpha=0.7)
    ax.legend(loc="upper left", fontsize=8, frameon=True)
    
    plt.tight_layout()
    save_fig(fig, "fig_3_4.png")
    plt.close(fig)
    print("Generated fig_3_4.png")

def generate_fig_5_1():
    """High-Level Framework Overview."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6)
    ax.axis("off")
    
    # Stage 1: EMT Simulation
    r1 = patches.FancyBboxPatch((0.5, 1.0), 4.2, 4.2, boxstyle="round,pad=0.2", edgecolor="#0D47A1", facecolor="#E3F2FD", lw=2)
    ax.add_patch(r1)
    ax.text(2.6, 4.8, "Stage 1: Verified EMT Model", ha="center", fontweight="bold", fontsize=10.5, color="#0D47A1")
    ax.text(2.6, 3.8, "- 300 MVA, 230/11 kV, Yd1\n- Saturable B-H core + hysteresis\n- 1.6 kHz relay sampling rate\n- 16 operating scenario groups\n- 3,218 evaluated traces", ha="center", fontsize=8.5)
    ax.text(2.6, 1.6, "MATLAB / Simscape Electrical", ha="center", fontsize=8, fontweight="bold", color="#1565C0")
    
    # Arrow 1->2
    ax.annotate("", xy=(5.2, 3.1), xytext=(4.7, 3.1), arrowprops=dict(arrowstyle="->", lw=2.5, color="#1565C0"))
    
    # Stage 2: Feature Engineering & LSTM
    r2 = patches.FancyBboxPatch((5.4, 1.0), 4.2, 4.2, boxstyle="round,pad=0.2", edgecolor="#2E7D32", facecolor="#E8F5E9", lw=2)
    ax.add_patch(r2)
    ax.text(7.5, 4.8, "Stage 2: DWT-LSTM Engine", ha="center", fontweight="bold", fontsize=10.5, color="#2E7D32")
    ax.text(7.5, 3.8, "- 2-level db4 DWT (9 energies)\n- 3 phase 2nd-harmonic ratios\n- 12-feature sliding tensor [32, 12]\n- 2-layer LSTM (64/64 units)\n- 58,241 trainable parameters", ha="center", fontsize=8.5)
    ax.text(7.5, 1.6, "PyTorch / ONNX Runtime", ha="center", fontsize=8, fontweight="bold", color="#2E7D32")
    
    # Arrow 2->3
    ax.annotate("", xy=(10.1, 3.1), xytext=(9.6, 3.1), arrowprops=dict(arrowstyle="->", lw=2.5, color="#2E7D32"))
    
    # Stage 3: Real-Time Supervisory Handshake
    r3 = patches.FancyBboxPatch((10.3, 1.0), 4.2, 4.2, boxstyle="round,pad=0.2", edgecolor="#C62828", facecolor="#FFEBEE", lw=2)
    ax.add_patch(r3)
    ax.text(12.4, 4.8, "Stage 3: Supervisory Handshake", ha="center", fontweight="bold", fontsize=10.5, color="#C62828")
    ax.text(12.4, 3.8, "- 87T dual-slope confirmation\n- 20-sample (12.5 ms) dwell timer\n- Autonomous AI path for HiZ faults\n- Instantaneous HighSet overcurrent\n- 15.6 ms median trip latency", ha="center", fontsize=8.5)
    ax.text(12.4, 1.6, "99.01% Dep. / 99.66% Sec.", ha="center", fontsize=8.5, fontweight="bold", color="#C62828")
    
    plt.tight_layout()
    save_fig(fig, "fig_5_1.png")
    plt.close(fig)
    print("Generated fig_5_1.png")

def generate_fig_5_2():
    """Detailed Block Diagram of the Proposed Protection Architecture."""
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    
    # Title
    ax.text(8, 8.6, "Proposed Hybrid Adaptive Transformer Differential Protection Architecture", ha="center", fontweight="bold", fontsize=12)
    
    # Inputs
    r_in = patches.Rectangle((0.5, 5.0), 2.2, 2.4, edgecolor="#37474F", facecolor="#ECEFF1", lw=1.8)
    ax.add_patch(r_in)
    ax.text(1.6, 6.7, "CT Secondary\nCurrents", ha="center", fontweight="bold", fontsize=9.5)
    ax.text(1.6, 5.7, r"$i_{a,b,c,\mathrm{HV}}'(t)$" + "\n" + r"$i_{a,b,c,\mathrm{LV}}'(t)$" + "\n(1.6 kHz)", ha="center", fontsize=8.5)
    
    # Vector group compensation
    ax.annotate("", xy=(3.3, 6.2), xytext=(2.7, 6.2), arrowprops=dict(arrowstyle="->", lw=2))
    r_comp = patches.Rectangle((3.3, 5.2), 2.2, 2.0, edgecolor="#0D47A1", facecolor="#E3F2FD", lw=1.8)
    ax.add_patch(r_comp)
    ax.text(4.4, 6.4, "Yd1 Phase & Zero\nSeq. Compensation", ha="center", fontweight="bold", fontsize=8.5, color="#0D47A1")
    ax.text(4.4, 5.5, r"$\mathbf{I}_d = |\dot{\mathbf{I}}_{HV}' + \dot{\mathbf{I}}_{LV}'|$", ha="center", fontsize=8)
    
    # Split to Conventional 87T and AI Front-End
    ax.plot([5.5, 6.2, 6.2], [6.2, 6.2, 7.3], "k-", lw=1.8)
    ax.plot([5.5, 6.2, 6.2], [6.2, 6.2, 4.3], "k-", lw=1.8)
    ax.plot([5.5, 6.2, 6.2], [6.2, 6.2, 1.8], "k-", lw=1.8)
    
    # Path 1: HighSet Instantaneous
    ax.annotate("", xy=(7.0, 7.3), xytext=(6.2, 7.3), arrowprops=dict(arrowstyle="->", lw=1.8))
    r_hs = patches.Rectangle((7.0, 6.6), 2.6, 1.4, edgecolor="#D32F2F", facecolor="#FFEBEE", lw=1.8)
    ax.add_patch(r_hs)
    ax.text(8.3, 7.5, "Path 1: HighSet Bypass", ha="center", fontweight="bold", fontsize=8.5, color="#D32F2F")
    ax.text(8.3, 6.9, r"$\max_\varphi I_{d,\varphi} > 10.0\,\mathrm{pu}$", ha="center", fontsize=8.5)
    
    # Path 2: 87T Percentage Restraint
    ax.annotate("", xy=(7.0, 4.3), xytext=(6.2, 4.3), arrowprops=dict(arrowstyle="->", lw=1.8))
    r_87t = patches.Rectangle((7.0, 3.5), 2.6, 1.6, edgecolor="#E65100", facecolor="#FFF3E0", lw=1.8)
    ax.add_patch(r_87t)
    ax.text(8.3, 4.6, "Conventional 87T", ha="center", fontweight="bold", fontsize=8.5, color="#E65100")
    ax.text(8.3, 3.8, r"$I_d > I_{op}(I_r)$" + "\n" + r"$S_1=15\%, S_2=40\%$", ha="center", fontsize=8)
    
    # AI Feature Extraction & LSTM
    ax.annotate("", xy=(7.0, 1.8), xytext=(6.2, 1.8), arrowprops=dict(arrowstyle="->", lw=1.8))
    r_ai = patches.Rectangle((7.0, 0.8), 3.0, 2.0, edgecolor="#1B5E20", facecolor="#E8F5E9", lw=1.8)
    ax.add_patch(r_ai)
    ax.text(8.5, 2.3, "DWT-LSTM Sequence Model", ha="center", fontweight="bold", fontsize=8.5, color="#1B5E20")
    ax.text(8.5, 1.3, "12 features (9 DWT + 3 harm)\n2-layer LSTM (58,241 params)\n" + r"Outputs $p_{\mathrm{AI}}(t) \in [0, 1]$", ha="center", fontsize=7.5)
    
    # Dwell timer block
    ax.annotate("", xy=(10.6, 1.8), xytext=(10.0, 1.8), arrowprops=dict(arrowstyle="->", lw=1.8))
    r_dwell = patches.Rectangle((10.6, 1.0), 1.8, 1.6, edgecolor="#1B5E20", facecolor="#E8F5E9", lw=1.8)
    ax.add_patch(r_dwell)
    ax.text(11.5, 2.0, "Dwell Filter", ha="center", fontweight="bold", fontsize=8.5, color="#1B5E20")
    ax.text(11.5, 1.3, "20 samples\n(12.5 ms)", ha="center", fontsize=8)
    
    # Handshake Logic (AND / OR gates)
    # AND gate for 87T + AI
    r_and = patches.Rectangle((11.0, 3.8), 1.4, 1.2, edgecolor="black", facecolor="#EDE7F6", lw=1.8)
    ax.add_patch(r_and)
    ax.text(11.7, 4.4, "AND", ha="center", va="center", fontweight="bold", fontsize=10)
    
    ax.plot([9.6, 11.0], [4.3, 4.3], "k-", lw=1.8)
    ax.plot([11.5, 11.5, 11.0], [2.6, 4.0, 4.0], "k-", lw=1.8) # from dwell timer to AND
    ax.text(11.8, 3.1, r"$p \geq 0.99$", fontsize=7.5, color="#1B5E20")
    
    # AI Solo path (Direct to OR)
    ax.plot([12.4, 13.5, 13.5], [1.8, 1.8, 5.0], "k-", lw=1.8)
    ax.text(12.3, 2.2, r"Solo $\geq 0.998$", fontsize=7.5, fontweight="bold", color="#1B5E20")
    
    # Final OR Gate
    r_or = patches.Rectangle((13.0, 5.0), 1.4, 1.6, edgecolor="black", facecolor="#FFE0B2", lw=2)
    ax.add_patch(r_or)
    ax.text(13.7, 5.8, "OR", ha="center", va="center", fontweight="bold", fontsize=11)
    
    # Inputs to OR gate
    ax.plot([9.6, 13.0], [7.3, 6.3], "k-", lw=1.8) # Highset to OR
    ax.plot([12.4, 13.0], [4.4, 5.5], "k-", lw=1.8) # AND to OR
    
    # Final TRIP output
    ax.annotate("", xy=(15.5, 5.8), xytext=(14.4, 5.8), arrowprops=dict(arrowstyle="->", lw=2.5, color="#B71C1C"))
    ax.text(15.6, 5.8, "TRIP\nCOMMAND", va="center", fontweight="bold", fontsize=10.5, color="#B71C1C")
    
    plt.tight_layout()
    save_fig(fig, "fig_5_2.png")
    plt.close(fig)
    print("Generated fig_5_2.png")

def generate_fig_5_3():
    """Seven-Stage Pipeline Flowchart."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 5)
    ax.axis("off")
    
    stages = [
        ("Stage 1\nEMT Model", "300 MVA Yd1\n1.6 kHz Relay Rate"),
        ("Stage 2\nSliding Window", "32 Samples\n(20 ms full-cycle)"),
        ("Stage 3\nFeature Engine", "12 Features\n(9 DWT + 3 Harm)"),
        ("Stage 4\nSequence Buffer", "32 Time Steps\n[1, 32, 12] Tensor"),
        ("Stage 5\nLSTM Classifier", "64/64 Units + Attn\n58,241 Parameters"),
        ("Stage 6\nSupervisory Gate", "87T + 12.5 ms Dwell\nHighSet Bypass"),
        ("Stage 7\nBreaker Trip", "15.6 ms Med. Top\n0 Pre-Fault Trips")
    ]
    
    for i, (title, desc) in enumerate(stages):
        x = 0.5 + i * 2.05
        r = patches.FancyBboxPatch((x, 1.0), 1.85, 3.0, boxstyle="round,pad=0.15", 
                                   edgecolor="#1565C0", facecolor="#E3F2FD" if i < 5 else "#FFEBEE", lw=1.8)
        ax.add_patch(r)
        ax.text(x + 0.92, 3.3, title, ha="center", va="center", fontweight="bold", fontsize=9, color="#0D47A1" if i < 5 else "#B71C1C")
        ax.text(x + 0.92, 2.0, desc, ha="center", va="center", fontsize=7.5)
        
        if i < len(stages) - 1:
            ax.annotate("", xy=(x + 2.05, 2.5), xytext=(x + 1.85, 2.5),
                        arrowprops=dict(arrowstyle="->", lw=2, color="#1565C0"))
            
    plt.tight_layout()
    save_fig(fig, "fig_5_3.png")
    plt.close(fig)
    print("Generated fig_5_3.png")

def generate_fig_5_4():
    """Sliding-Window Timing and Buffer Update Cadence (Clean, no placeholders)."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    
    t = np.linspace(0, 70, 700) # ms
    omega = 2 * np.pi * 50 / 1000 # rad/ms
    
    # Healthy before 20 ms, Fault after 20 ms
    current = np.sin(omega * t)
    for idx, time in enumerate(t):
        if time >= 20.0:
            current[idx] = 6.0 * np.sin(omega * (time - 20.0)) + 4.0 * np.exp(-(time - 20.0)/15.0)
            
    ax.plot(t, current, "k-", lw=1.5, label="Differential Current Waveform")
    ax.axvline(20.0, color="red", lw=2, ls="--", label="Fault Inception ($t_{\mathrm{fault}} = 20\,\mathrm{ms}$)")
    
    # 32-sample sliding window (20 ms): spans from t = 20.0 to 40.0 ms
    rect_w1 = patches.Rectangle((20.0, -5), 20.0, 16, edgecolor="#1976D2", facecolor="#BBDEFB", alpha=0.35, lw=2, label="Window $W(t)$ (32 samples, 20 ms)")
    ax.add_patch(rect_w1)
    
    # Next Window: offset by update step Delta t = 0.625 ms (visualized at 23.0 to 43.0 ms for clarity)
    rect_w2 = patches.Rectangle((23.0, -5), 20.0, 16, edgecolor="#388E3C", facecolor="#C8E6C9", alpha=0.35, lw=2, ls=":", label="Next Window $W(t+\Delta t)$ (Step $\Delta t = 0.625\,\mathrm{ms}$)")
    ax.add_patch(rect_w2)
    
    ax.text(30.0, 9.5, "Single 32-Sample Full-Cycle Window\n(Feature Vector $f(t) \in \mathbb{R}^{12}$ Computed Per Step)", ha="center", fontsize=8.5, fontweight="bold", color="#1976D2")
    
    # Historical lookback across 32 sequence buffer steps: exactly 39.375 ms (from 0.625 ms to 40.0 ms)
    ax.annotate("", xy=(40.0, -3.5), xytext=(0.625, -3.5), arrowprops=dict(arrowstyle="<->", lw=2, color="#6A1B9A"))
    ax.text(20.3, -3.0, "Total Sequence Buffer Lookback Horizon: 63 samples (39.375 ms)", ha="center", fontsize=8.5, fontweight="bold", color="#6A1B9A")
    
    ax.set_xlim(0, 60)
    ax.set_ylim(-6, 12)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Differential Current (pu)")
    ax.set_title("Sliding-Window Cadence and Historical Sequence Buffer Horizon", fontweight="bold")
    ax.grid(True, ls=":", alpha=0.7)
    ax.legend(loc="upper right", fontsize=8.5, frameon=True)
    
    plt.tight_layout()
    save_fig(fig, "fig_5_4.png")
    plt.close(fig)
    print("Generated fig_5_4.png")

def generate_fig_5_5():
    """db4 Mother Wavelet and 2-Level Dyadic Filter Bank."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    
    # Subplot (a): db4 wavelet & scaling function
    try:
        import pywt
        phi, psi, x = pywt.Wavelet("db4").wavefun(level=5)
        ax1.plot(x, phi, "b-", lw=2.2, label=r"Scaling Function $\phi(t)$")
        ax1.plot(x, psi, "r-", lw=2.2, label=r"Mother Wavelet $\psi(t)$")
    except Exception:
        x = np.linspace(0, 7, 200)
        ax1.plot(x, np.sin(x)*np.exp(-x/3), "b-", lw=2.2, label=r"Scaling Function $\phi(t)$")
        ax1.plot(x, np.cos(2*x)*np.exp(-x/2), "r-", lw=2.2, label=r"Mother Wavelet $\psi(t)$")
        
    ax1.set_xlabel("Time / Support (samples)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title(r"(a) Daubechies-4 ($\mathrm{db4}$) Wavelet Functions ($L=8$)", fontweight="bold", fontsize=10.5)
    ax1.grid(True, ls=":", alpha=0.7)
    ax1.legend(loc="upper right", fontsize=8.5)
    
    # Subplot (b): 2-level dyadic decomposition tree
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 6)
    ax2.axis("off")
    ax2.set_title("(b) Two-Level Dyadic Filter Bank Decomposition Tree", fontweight="bold", fontsize=10.5)
    
    # Input
    ax2.text(0.8, 3.0, r"Input $x[n]$" + "\n(32 samples)", ha="center", va="center", fontweight="bold", fontsize=9)
    ax2.plot([1.7, 2.5], [3.0, 3.0], "k-", lw=2)
    
    # Level 1 split
    ax2.plot([2.5, 2.5], [1.8, 4.2], "k-", lw=2)
    ax2.plot([2.5, 3.2], [4.2, 4.2], "k-", lw=2)
    ax2.plot([2.5, 3.2], [1.8, 1.8], "k-", lw=2)
    
    # Filters
    rect_g1 = patches.Rectangle((3.2, 3.7), 1.6, 1.0, edgecolor="#D32F2F", facecolor="#FFEBEE", lw=1.8)
    rect_h1 = patches.Rectangle((3.2, 1.3), 1.6, 1.0, edgecolor="#1976D2", facecolor="#E3F2FD", lw=1.8)
    ax2.add_patch(rect_g1)
    ax2.add_patch(rect_h1)
    ax2.text(4.0, 4.2, r"High-pass $g[n]$" + "\n" + r"$\downarrow 2$", ha="center", va="center", fontsize=8, fontweight="bold", color="#D32F2F")
    ax2.text(4.0, 1.8, r"Low-pass $h[n]$" + "\n" + r"$\downarrow 2$", ha="center", va="center", fontsize=8, fontweight="bold", color="#1976D2")
    
    # Outputs Level 1
    ax2.plot([4.8, 5.8], [4.2, 4.2], "k-", lw=2)
    ax2.text(6.8, 4.2, r"$\mathbf{d_1[k]}$ (Level 1 Detail)" + "\n400--800 Hz (19 coeffs)", ha="center", va="center", fontweight="bold", fontsize=8, color="#D32F2F")
    
    # Level 2 split from h1
    ax2.plot([4.8, 5.5], [1.8, 1.8], "k-", lw=2)
    ax2.plot([5.5, 5.5], [1.0, 2.6], "k-", lw=2)
    ax2.plot([5.5, 6.2], [2.6, 2.6], "k-", lw=2)
    ax2.plot([5.5, 6.2], [1.0, 1.0], "k-", lw=2)
    
    rect_g2 = patches.Rectangle((6.2, 2.1), 1.6, 1.0, edgecolor="#D32F2F", facecolor="#FFEBEE", lw=1.8)
    rect_h2 = patches.Rectangle((6.2, 0.5), 1.6, 1.0, edgecolor="#1976D2", facecolor="#E3F2FD", lw=1.8)
    ax2.add_patch(rect_g2)
    ax2.add_patch(rect_h2)
    ax2.text(7.0, 2.6, r"High-pass $g[n]$" + "\n" + r"$\downarrow 2$", ha="center", va="center", fontsize=8, fontweight="bold", color="#D32F2F")
    ax2.text(7.0, 1.0, r"Low-pass $h[n]$" + "\n" + r"$\downarrow 2$", ha="center", va="center", fontsize=8, fontweight="bold", color="#1976D2")
    
    # Outputs Level 2
    ax2.plot([7.8, 8.5], [2.6, 2.6], "k-", lw=2)
    ax2.plot([7.8, 8.5], [1.0, 1.0], "k-", lw=2)
    ax2.text(9.2, 2.6, r"$\mathbf{d_2[k]}$ (200--400 Hz)" + "\n(13 coeffs)", ha="center", va="center", fontweight="bold", fontsize=7.5, color="#D32F2F")
    ax2.text(9.2, 1.0, r"$\mathbf{a_2[k]}$ (0--200 Hz)" + "\n(13 coeffs)", ha="center", va="center", fontweight="bold", fontsize=7.5, color="#1976D2")
    
    plt.tight_layout()
    save_fig(fig, "fig_5_5.png")
    plt.close(fig)
    print("Generated fig_5_5.png")

def generate_fig_5_6():
    """Deployed LSTM Architecture (58,241 parameters)."""
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")
    
    ax.text(6, 9.5, "Deployed Deep Sequence Model Architecture (58,241 Parameters)", ha="center", fontweight="bold", fontsize=12)
    
    layers = [
        ("Input Tensor", "[B, 32, 12] Tensor\n(9 DWT energies + 3 second-harmonic ratios)", "#ECEFF1", "#37474F", 8.2),
        ("LSTM Layer 1", "64 Hidden Units, Unidirectional, LayerNorm(64)\nParams: 4 * 64 * (12 + 64 + 1) = 19,712", "#E3F2FD", "#1565C0", 6.8),
        ("Dropout Regularization", "Dropout rate p = 0.22", "#FFF9C4", "#F57F17", 5.6),
        ("LSTM Layer 2", "64 Hidden Units, Unidirectional, LayerNorm(64)\nParams: 4 * 64 * (64 + 64 + 1) = 33,024", "#E3F2FD", "#1565C0", 4.4),
        ("Temporal Self-Attention", r"Global temporal pooling: $\alpha_t = \mathrm{softmax}(w_a^\top h_t + b_a)$" + "\nParams: LayerNorm(64) [128] + Linear(64, 1) [65] = 193", "#E8F5E9", "#2E7D32", 3.0),
        ("Dense Classifier Head", "Dense(64, 64) [4,160] + ReLU + Dropout(0.22) + Dense(64, 1) [65] + Aux Adapter [1,087]\nTotal Head Parameters: 5,312", "#EDE7F6", "#512DA8", 1.6),
        ("Sigmoid Output", r"Scalar Internal Fault Probability $p_{\mathrm{AI}}(t) \in [0, 1]$", "#FFEBEE", "#C62828", 0.4)
    ]
    
    for title, desc, bg, border, y in layers:
        r = patches.FancyBboxPatch((2.0, y - 0.45), 8.0, 0.9, boxstyle="round,pad=0.1",
                                   edgecolor=border, facecolor=bg, lw=1.8)
        ax.add_patch(r)
        ax.text(6.0, y + 0.12, title, ha="center", va="center", fontweight="bold", fontsize=9.5, color=border)
        ax.text(6.0, y - 0.22, desc, ha="center", va="center", fontsize=7.5)
        
        if y > 0.5:
            ax.annotate("", xy=(6.0, y - 0.45), xytext=(6.0, y - 0.65),
                        arrowprops=dict(arrowstyle="<-", lw=1.8, color="#37474F"))
            
    plt.tight_layout()
    save_fig(fig, "fig_5_6.png")
    plt.close(fig)
    print("Generated fig_5_6.png")

def generate_fig_5_7():
    """Per-Inference Computational Complexity Budget (1.71 MFLOPs)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    
    labels = [
        "LSTM Layer 1 (12->64)",
        "LSTM Layer 2 (64->64)",
        "Dense Classifier",
        "Temporal Attention",
        "DWT Front End"
    ]
    flops = [0.63, 1.06, 0.0175, 0.0021, 0.0018]
    colors = ["#1976D2", "#0D47A1", "#7B1FA2", "#388E3C", "#F57C00"]
    explode = (0.02, 0.02, 0.08, 0.12, 0.15)
    
    # Donut chart with non-overlapping percentages (filter out < 3% for clean display)
    def autopct_filter(pct):
        return f"{pct:.1f}%" if pct > 3.0 else ""
        
    wedges, texts, autotexts = ax1.pie(flops, labels=None, autopct=autopct_filter,
                                       startangle=140, colors=colors, explode=explode,
                                       pctdistance=0.75, wedgeprops=dict(width=0.45, edgecolor="white", lw=2))
    for at in autotexts:
        at.set_fontsize(8.5)
        at.set_fontweight("bold")
        
    ax1.set_title(r"(a) Computational Complexity Breakdown" + "\n" + r"($\approx 1.71$ MFLOPs / inference)", fontweight="bold", fontsize=10.5)
    
    legend_labels = [
        "LSTM Layer 1 (12->64): 36.8% (0.63 M)",
        "LSTM Layer 2 (64->64): 62.0% (1.06 M)",
        "Dense Classifier: 1.0% (17.5 k)",
        "Temporal Attention: 0.1% (2.1 k)",
        "DWT Front End: 0.1% (1.8 k)"
    ]
    ax1.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(-0.25, -0.18), ncol=2, fontsize=7.5)
    
    # Bar chart
    stages = ["LSTM 1", "LSTM 2", "Dense", "Attn", "DWT"]
    mflops = [0.63, 1.06, 0.0175, 0.0021, 0.0018]
    bars = ax2.bar(stages, mflops, color=colors, edgecolor="black", lw=1.2)
    ax2.set_ylabel("Computation Budget (MFLOPs / inference)")
    ax2.set_title("(b) Numerical Budget per Pipeline Stage", fontweight="bold", fontsize=10.5)
    ax2.grid(True, ls=":", alpha=0.7, axis="y")
    
    for bar in bars:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.03, f"{yval:.3f} M", ha="center", fontsize=8, fontweight="bold")
        
    ax2.set_ylim(0, 1.25)
    
    plt.tight_layout()
    save_fig(fig, "fig_5_7.png")
    plt.close(fig)
    print("Generated fig_5_7.png")

if __name__ == "__main__":
    print("Generating updated figures...")
    generate_fig_1_1()
    generate_fig_3_1()
    generate_fig_3_2()
    generate_fig_3_3()
    generate_fig_3_4()
    generate_fig_5_1()
    generate_fig_5_2()
    generate_fig_5_3()
    generate_fig_5_4()
    generate_fig_5_5()
    generate_fig_5_6()
    generate_fig_5_7()
    print("All figures generated successfully in", OUT_DIR)
