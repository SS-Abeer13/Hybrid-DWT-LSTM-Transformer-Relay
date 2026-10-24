# -*- coding: utf-8 -*-
"""apply_academic_remediations.py
Applies all technical and editorial refinements from the Round 3 Reviewer Report
to rebuild_thesis_manuscript.py and syncs update_rebuild_script.py.
"""
import re
from pathlib import Path

REBUILD_SCRIPT = Path(r"F:\Transformer Thesis\rebuild_thesis_manuscript.py")
UPDATE_SCRIPT = Path(r"F:\Transformer Thesis\update_rebuild_script.py")

text = REBUILD_SCRIPT.read_text(encoding="utf-8")

# 1. Table A.1 Filter Coefficients
old_table_a1 = r"""0 & $+0.230377813308896$ & $-0.010597401785069$\\
1 & $+0.714846570552915$ & $+0.032883011666885$\\
2 & $+0.630880767937402$ & $+0.030841381835561$\\
3 & $-0.027983769416860$ & $-0.187034811719093$\\
4 & $-0.187034811719093$ & $-0.027983769416860$\\
5 & $+0.030841381835561$ & $+0.630880767937402$\\
6 & $+0.032883011666885$ & $-0.714846570552915$\\
7 & $-0.010597401785069$ & $+0.230377813308896$\\"""

new_table_a1 = r"""0 & $+0.230377813308896$ & $-0.010597401785069$\\
1 & $+0.714846570552915$ & $-0.032883011666885$\\
2 & $+0.630880767937402$ & $+0.030841381835561$\\
3 & $-0.027983769416860$ & $+0.187034811719093$\\
4 & $-0.187034811719093$ & $-0.027983769416860$\\
5 & $+0.030841381835561$ & $-0.630880767937402$\\
6 & $+0.032883011666885$ & $+0.714846570552915$\\
7 & $-0.010597401785069$ & $-0.230377813308896$\\"""

assert old_table_a1 in text, "old_table_a1 not found"
text = text.replace(old_table_a1, new_table_a1)
print("1. Replaced Table A.1 QMF coefficients.")

# 2. Appendix B.2 Standards compliance (IEC 60255-187-1:2021)
old_iec = r"""\item \textbf{IEC 60255-149:2013:} \textit{Measuring Relays and Protection Equipment -- Part 149: Functional Requirements for Thermal Electrical Relays}."""
new_iec = r"""\item \textbf{IEC 60255-187-1:2021:} \textit{Measuring Relays and Protection Equipment -- Part 187-1: Functional Requirements for Differential Protection -- AC Motors, Generators and Transformers}."""

assert old_iec in text, "old_iec not found"
text = text.replace(old_iec, new_iec)
print("2. Updated Appendix B.2 to IEC 60255-187-1:2021.")

# 3. Front-Matter TOC uppercase headings
old_toc = r"""\addcontentsline{toc}{chapter}{Contents}
\tableofcontents

\clearpage\phantomsection
\addcontentsline{toc}{chapter}{List of Figures}
\listoffigures

\clearpage\phantomsection
\addcontentsline{toc}{chapter}{List of Tables}
\listoftables"""

new_toc = r"""\addcontentsline{toc}{chapter}{CONTENTS}
\tableofcontents

\clearpage\phantomsection
\addcontentsline{toc}{chapter}{LIST OF FIGURES}
\listoffigures

\clearpage\phantomsection
\addcontentsline{toc}{chapter}{LIST OF TABLES}
\listoftables"""

assert old_toc in text, "old_toc not found"
text = text.replace(old_toc, new_toc)

assert r"\addcontentsline{toc}{chapter}{References}" in text, "References TOC not found"
text = text.replace(r"\addcontentsline{toc}{chapter}{References}", r"\addcontentsline{toc}{chapter}{REFERENCES}")

assert r"\addcontentsline{toc}{chapter}{List of Publications}" in text, "Publications TOC not found"
text = text.replace(r"\addcontentsline{toc}{chapter}{List of Publications}", r"\addcontentsline{toc}{chapter}{LIST OF PUBLICATIONS}")
print("3. Standardized TOC front-matter headings to uppercase.")

# 4. List of Symbols Units
old_sym = r"""$I_d$ & Differential current & A\\
$I_r$ & Restraint (bias) current & A\\
$I_{pickup}$ & Minimum pickup current setting & A\\
$I_{d,fund}$ & Fundamental frequency differential current component & A\\
$I_{d,2nd}$ & Second harmonic differential current component & A\\"""

new_sym = r"""$I_d$ & Differential current & A (or pu)\\
$I_r$ & Restraint (bias) current & A (or pu)\\
$I_{pickup}$ & Minimum pickup current setting & A (or pu)\\
$I_{d,fund}$ & Fundamental frequency differential current component & A (or pu)\\
$I_{d,2nd}$ & Second harmonic differential current component & A (or pu)\\"""

assert old_sym in text, "old_sym not found"
text = text.replace(old_sym, new_sym)
print("4. Updated current units in List of Symbols to A (or pu).")

# 5. Fix unescaped tilde in Figure 5.7 caption
old_fig57_cap = r"\caption{Per-inference computational cost distribution across pipeline stages (~1.71 MFLOPs total).}\label{fig:5.7}"
new_fig57_cap = r"\caption{Per-inference computational cost distribution across pipeline stages ($\approx$1.71\,MFLOPs total).}\label{fig:5.7}"
assert old_fig57_cap in text, "old_fig57_cap not found"
text = text.replace(old_fig57_cap, new_fig57_cap)
print("5. Fixed Figure 5.7 caption unescaped tilde.")

# 6. Table 6.3 Separation into Panels
old_tab63 = r"""\begin{table}[H]\centering\caption{Retraining impact: performance on realistic stress cases.}\label{tab:6.3}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcc@{}}\toprule
\textbf{Scenario Category} & \textbf{Light-Load Baseline Model (\%)} & \textbf{Retrained v3 Model (\%)}\\ \midrule
External Fault with CT Saturation & 60.2 & \textbf{99.2}\\
Over-Excitation (V/f saturation) & 41.4 & \textbf{100.0}\\
Recovery Inrush & 65.0 & \textbf{97.5}\\
Loaded Magnetizing Inrush & 86.7 & \textbf{99.9}\\
Internal Fault during Inrush & 84.1 & \textbf{100.0}\\ \midrule
\textbf{Overall Security} & \textbf{84.1\% (298 false trips)} & \textbf{99.7\% (6 false trips)}\\ \bottomrule
\end{tabular}%
}
\end{table}"""

new_tab63 = r"""\begin{table}[H]\centering\caption{Retraining impact: performance on realistic stress cases.}\label{tab:6.3}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcc@{}}\toprule
\textbf{Scenario Category} & \textbf{Light-Load Baseline Model (\%)} & \textbf{Retrained v3 Model (\%)}\\ \midrule
\multicolumn{3}{@{}l}{\textit{Panel A: Non-Fault Transient Security (Healthy Regimes, Expected BLOCK)}} \\ \midrule
External Fault with CT Saturation & 60.2 & \textbf{99.2}\\
Over-Excitation (V/f saturation) & 41.4 & \textbf{100.0}\\
Recovery Inrush & 65.0 & \textbf{97.5}\\
Loaded Magnetizing Inrush & 86.7 & \textbf{99.9}\\ \midrule
\textbf{Overall Security} & \textbf{84.1\% (298 false trips)} & \textbf{99.7\% (6 false trips)}\\ \midrule
\multicolumn{3}{@{}l}{\textit{Panel B: Internal Fault Dependability (Fault Regimes, Expected TRIP)}} \\ \midrule
Internal Fault during Inrush & 84.1 & \textbf{100.0}\\ \bottomrule
\end{tabular}%
}
\end{table}"""

assert old_tab63 in text, "old_tab63 not found"
text = text.replace(old_tab63, new_tab63)
print("6. Separated Table 6.3 into Security and Dependability Panels.")

# 7. Section 2.2.2 Explicit citation of Ref. [35]
old_s222 = r"""Dead-angle and waveform correlation methods classify events based on waveshape features. Lin et al.~\cite{ref37} studied improved correlation algorithms to identify inrush waveforms, but such techniques remain sensitive to threshold selection and noise. Kang et al.~\cite{ref36} developed CT saturation compensation algorithms utilizing third-derivative secondary current functions. Noshad et al.~\cite{ref26} investigated algorithms under ultra-saturation conditions. Equivalent-circuit methods detect internal faults when terminal measurements violate core magnetic flux equations~\cite{ref26,ref28}, but require high-accuracy voltage transducers and detailed manufacturer design constants~\cite{ref30}."""

new_s222 = r"""Dead-angle and waveform correlation methods classify events based on waveshape features. Lin et al.~\cite{ref37} studied improved correlation algorithms to identify inrush waveforms, but such techniques remain sensitive to threshold selection and noise. Kang et al.~\cite{ref36} developed CT saturation compensation algorithms utilizing third-derivative secondary current functions. Noshad et al.~\cite{ref26} investigated algorithms under ultra-saturation conditions. Statistical and volatility-tracking formulations, such as the Generalized Autoregressive Conditional Heteroskedasticity (GARCH) model proposed by Hooshyar et al.~\cite{ref35}, characterize the time-varying variance of differential currents under non-fault transients. Equivalent-circuit methods detect internal faults when terminal measurements violate core magnetic flux equations~\cite{ref26,ref28}, but require high-accuracy voltage transducers and detailed manufacturer design constants~\cite{ref30}."""

assert old_s222 in text, "old_s222 not found"
text = text.replace(old_s222, new_s222)
print("7. Explicitly cited Hooshyar et al. [35] in Section 2.2.2.")

# 8. Section 3.2.1 Phasor currents notation and Clarke/Yd1 clarification
old_s321 = r"""\subsection{Differential and Restraint Currents}
For a three-phase power transformer, let $\dot{\mathbf{I}}_{HV}'$ and $\dot{\mathbf{I}}_{LV}'$ denote the secondary line currents referred to a common base and corrected for the Yd1 vector group phase displacement:
\begin{equation}
\mathbf{I}_d = \left|\dot{\mathbf{I}}_{HV}' + \dot{\mathbf{I}}_{LV}'\right|,\qquad
\mathbf{I}_r = \frac{1}{2}\left(\left|\dot{\mathbf{I}}_{HV}'\right| + \left|\dot{\mathbf{I}}_{LV}'\right|\right).
\end{equation}"""

new_s321 = r"""\subsection{Differential and Restraint Currents}
For a three-phase power transformer, let $\dot{\mathbf{I}}_{HV}'$ and $\dot{\mathbf{I}}_{LV}'$ denote the secondary line currents referred to the calibrated secondary base current ($I_{nom,sec} = 0.9302$\,A, or $1.0$\,pu) and corrected for the Yd1 vector group $-30^\circ$ phase displacement and zero-sequence elimination:
\begin{equation}
\mathbf{I}_d = \left|\dot{\mathbf{I}}_{HV}' + \dot{\mathbf{I}}_{LV}'\right|,\qquad
\mathbf{I}_r = \frac{1}{2}\left(\left|\dot{\mathbf{I}}_{HV}'\right| + \left|\dot{\mathbf{I}}_{LV}'\right|\right).
\end{equation}"""

assert old_s321 in text, "old_s321 not found"
text = text.replace(old_s321, new_s321)
print("8. Refined Section 3.2.1 differential and restraint current formulations.")

# 9. Section 4.4 Series Limiting Resistor explanation
old_s44 = r"""A series limiting resistance of $R_{series} = 0.05\,\Omega$ is inserted in the external LV bus feeder network, capping external through-fault currents to $\approx 1.5$\,pu rms ($23.6$\,kA primary) to reflect stiff utility-feeder current limits and ensure that CT saturation is rigorously driven by burden and remanence sweeps."""

new_s44 = r"""A series limiting resistance of $R_{series} = 0.05\,\Omega$ is inserted in the external LV bus feeder network in series with the downstream utility branch impedance ($Z_{feeder} \approx 0.03 + j0.25\,\Omega$), establishing an effective through-fault path impedance of $\approx 0.67$\,pu ($0.27\,\Omega$ primary). This caps external through-fault currents to $\approx 1.5$\,pu rms ($23.6$\,kA primary line current) to reflect stiff utility-feeder current limits and ensure that CT saturation is rigorously driven by burden ($4\times\text{--}16\times$) and remanence sweeps rather than uncontrolled primary overcurrent."""

assert old_s44 in text, "old_s44 not found"
text = text.replace(old_s44, new_s44)
print("9. Clarified Section 4.4 external LV feeder topology and R_series current limiting.")

# 10. Section 6.8 & Table 6.6 High-Impedance Fault Accounting
old_s68 = r"""In the simulation sweep of internal high-impedance faults ($R_f = 0.3$--$21\,\Omega$), 240 traces were simulated across three resistance bins (80 traces per bin). Exactly 153 traces produce a differential current rise $\ge 0.05$\,pu (80 in Bin~1, 72 in Bin~2, and 1 in Bin~3), which constitute the 153 evaluated traces in Table~\ref{tab:4.3} and Table~\ref{tab:6.2}. The remaining 87 traces produce differential current below the 0.05\,pu physical noise threshold and are tracked separately. Table~\ref{tab:6.6} and Figure~\ref{fig:6.2} examine relay dependability across the three resistance bins. While conventional 87T relays fail to pick up above $R_f \approx 1.2\,\Omega$, the proposed AI-alone path maintains 71.2\% dependability in the AI-only zone ($1.2$--$7.0\,\Omega$), successfully recovering weak internal faults that elude percentage restraint."""

new_s68 = r"""In the simulation sweep of internal high-impedance faults ($R_f = 0.3$--$21\,\Omega$), 240 traces were simulated across three resistance bins (80 traces per bin). Exactly 153 traces produce a differential current rise $\ge 0.05$\,pu (80 in Bin~1, 72 in Bin~2, and 1 in Bin~3), which constitute the 153 evaluated detectable traces in Table~\ref{tab:4.3} and Table~\ref{tab:6.2}. The remaining 87 traces produce differential current below the 0.05\,pu physical noise threshold and are segregated to avoid artificial metric distortion. Table~\ref{tab:6.6} and Figure~\ref{fig:6.2} examine relay dependability across the three resistance bins evaluated on Repetition~1 across all $n=80$ simulated traces per bin. In Bin~1 ($0.3\text{--}1.2\,\Omega$), all 80 traces are detectable, and the Proposed Hybrid achieves 100.0\% ($80/80$) while 87T alone achieves 96.2\% ($77/80$). In Bin~2 ($1.2\text{--}7.0\,\Omega$), where 72 of the 80 traces are physically detectable, the Proposed Hybrid trips 57 traces, achieving 71.2\% dependability across all 80 traces (or 79.2\% among detectable traces), whereas 87T alone trips only 3 traces (3.8\% across all traces, or 4.2\% of detectable traces). In Bin~3 ($7.0\text{--}21.0\,\Omega$), 79 of 80 traces are sub-noise floor ($<0.05$\,pu), yielding 0.0\% across all methods. Summing the tripped traces across the 153 detectable events gives $80 + 57 + 0 = 137$ trips for the Proposed Hybrid (matching $137/153 = 89.5\%$ in Repetition~1 in Table~\ref{tab:6.2}, with a 3-repetition mean of 93.0\%) and $77 + 3 + 0 = 80$ trips for 87T alone (matching $80/153 = 52.3\%$)."""

assert old_s68 in text, "old_s68 not found"
text = text.replace(old_s68, new_s68)
print("10. Reconciled Section 6.8 HiZ fault bin accounting with Table 6.2 and Table 6.6.")

# 11. Bibliography Entries Update
# Ref 1
text = text.replace(
    r"""\bibitem{ref1} Q. Alhamd, M. Saniei, S. G. Seifossadat, and E. Mashhour, ``A novel transformer differential protection based on deep learning and wavelet transform,'' \textit{Algorithms}, vol.~17, no.~9, art.~397, 2024.""",
    r"""\bibitem{ref1} Q. Alhamd, M. Saniei, S. G. Seifossadat, and E. Mashhour, ``Advanced fault detection in power transformers using improved wavelet analysis and LSTM networks considering current transformer saturation and uncertainties,'' \textit{Algorithms}, vol.~17, no.~9, art.~397, 2024."""
)

# Ref 11
text = text.replace(
    r"""\bibitem{ref11} M. Abdusalam, K. F. Ali, and W. M. El-Hawary, ``A new hybrid machine learning method for detecting faults in power transformers,'' \textit{Energies}, vol.~15, no.~5, p.~1672, 2022.""",
    r"""\bibitem{ref11} M. Abdusalam, K. F. Ali, and W. M. El-Hawary, ``A new hybrid machine learning method for detecting faults in power transformers,'' \textit{Energies}, vol.~15, no.~18, art.~6758, 2022."""
)

# Ref 12
text = text.replace(
    r"""\bibitem{ref12} J. Wang, Y. Liu, Z. Li, and B. Wang, ``Deep reinforcement learning for early classification of power transformer transients,'' \textit{Expert Syst.\ Appl.}, vol.~258, p.~124521, 2025.""",
    r"""\bibitem{ref12} J. Wang, Y. Liu, Z. Li, and B. Wang, ``Early classification for power transformer fault detection using reinforcement learning,'' \textit{Expert Syst.\ Appl.}, vol.~240, art.~122550, 2024."""
)

# Ref 13
text = text.replace(
    r"""\bibitem{ref13} L. D. Sim\~{o}es, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, and A. S. Bretas, ``Transformer differential protection using support vector machine and wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~197, p.~107307, Aug. 2021.""",
    r"""\bibitem{ref13} L. D. Sim\~{o}es, H. J. D. Costa, M. N. O. Aires, R. P. Medeiros, F. B. Costa, and A. S. Bretas, ``A power transformer differential protection based on support vector machine and wavelet transform,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~197, art.~107297, Aug. 2021."""
)

# Ref 24
text = text.replace(
    r"""\bibitem{ref24} M. Oztekin, S. Karagol, and O. Ozgonenel, ``Power transformer differential protection with wavelet transform and difference function,'' \textit{Electr.\ Power Syst.\ Res.}, vol.~238, p.~111158, 2025.""",
    r"""\bibitem{ref24} M. Oztekin, S. Karagol, and O. Ozgonenel, ``Power transformer differential protection with wavelet transform and difference function,'' \textit{Eng.\ Sci.\ Technol.\ Int.\ J.}, vol.~70, art.~102144, 2025."""
)

# Ref 25
text = text.replace(
    r"""\bibitem{ref25} P. Chiradeja, A. Ngaopitakkul, and C. Pothisarn, ``Probabilistic neural network with wavelet transform for transformer protection using high-frequency components,'' \textit{Appl.\ Sci.}, vol.~11, no.~6, p.~2633, 2021.""",
    r"""\bibitem{ref25} P. Chiradeja, C. Pothisarn, and A. Ngaopitakkul, ``Identification of inrush current and internal faults in power transformers using probabilistic neural network and discrete wavelet transform,'' \textit{Appl.\ Sci.}, vol.~11, no.~22, art.~10619, 2021."""
)

# Ref 29
text = text.replace(
    r"""\bibitem{ref29} S. B. A. Bukhari, A. Wadood, T. Khurshaid, K. K. Mehmood, S. Rhee, and C. H. Kim, ``Empirical wavelet transform based intelligent protection scheme for microgrids,'' \textit{Energies}, vol.~15, no.~14, art.~5095, 2022.""",
    r"""\bibitem{ref29} S. B. A. Bukhari, A. Wadood, T. Khurshaid, K. K. Mehmood, S. Rhee, and C. H. Kim, ``Empirical wavelet transform based intelligent protection scheme for microgrids,'' \textit{Energies}, vol.~15, no.~21, art.~7995, 2022."""
)

# Ref 33
text = text.replace(
    r"""\bibitem{ref33} Z. Gajic, I. Brnivic, and R. Gojko, ``Differential protection of power transformers using ICT and smart processing,'' \textit{Int.\ J.\ Electr.\ Power Energy Syst.}, vol.~110, pp.~582--592, 2019.""",
    r"""\bibitem{ref33} Z. Gajic, I. Brn\v{c}i\'{c}, and R. Gojko, ``Differential protection of power transformers using ICT and smart processing,'' \textit{Int.\ J.\ Electr.\ Power Energy Syst.}, vol.~110, pp.~582--592, 2019."""
)

# Ref 35
text = text.replace(
    r"""\bibitem{ref35} A. Hooshyar, M. A. Azzouz, and E. F. El-Saadany, ``Transformer differential protection based on GARCH modelling of differential current,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~1, pp.~127--136, 2016.""",
    r"""\bibitem{ref35} A. Hooshyar, M. Sanaye-Pasand, and M. Davarpanah, ``GARCH differential current modeling for power transformer protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~2, pp.~642--652, Apr. 2016."""
)

# Ref 38
text = text.replace(
    r"""\bibitem{ref38} R. P. Medeiros, F. B. Costa, and K. M. Silva, ``Power transformer differential protection using the boundary discrete wavelet transform,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~5, pp.~2083--2092, Oct. 2016.""",
    r"""\bibitem{ref38} R. P. Medeiros, F. B. Costa, and K. M. Silva, ``Power transformer differential protection using the boundary discrete wavelet transform,'' \textit{IEEE Trans.\ Power Del.}, vol.~31, no.~5, pp.~2083--2095, Oct. 2016."""
)

# Ref 39
text = text.replace(
    r"""\bibitem{ref39} R. P. Medeiros, F. B. Costa, K. M. Silva, J. J. Chavez, J. R. Lima Junior, and M. Popov, ``A Clarke-wavelet-based time-domain power transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~37, no.~4, pp.~2971--2981, Aug. 2022.""",
    r"""\bibitem{ref39} R. P. Medeiros, F. B. Costa, K. M. Silva, J. J. Chavez, J. R. Lima Junior, and M. Popov, ``A Clarke-wavelet-based time-domain power transformer differential protection,'' \textit{IEEE Trans.\ Power Del.}, vol.~37, no.~1, pp.~317--328, Feb. 2022."""
)
print("11. Audited and corrected all bibliographic entries.")

# Write updated script
REBUILD_SCRIPT.write_text(text, encoding="utf-8")
print(f"Successfully updated {REBUILD_SCRIPT}")

# Also sync update_rebuild_script.py
# The content of update_rebuild_script.py wraps rebuild_thesis_manuscript.py
update_content = '# -*- coding: utf-8 -*-\n"""update_rebuild_script.py\nConstructs the pristine rebuild_thesis_manuscript.py containing all remediations\nand executes it to rebuild latex_source/latex/main.tex.\n"""\nfrom pathlib import Path\n\nOUT_FILE = Path(r"F:\\Transformer Thesis\\rebuild_thesis_manuscript.py")\n\nscript_content = r\'\'\'' + text + '\'\'\'\n\ndef main():\n    OUT_FILE.write_text(script_content, encoding="utf-8")\n    print(f"Updated {OUT_FILE} successfully.")\n\nif __name__ == "__main__":\n    main()\n'
UPDATE_SCRIPT.write_text(update_content, encoding="utf-8")
print(f"Successfully synced {UPDATE_SCRIPT}")
