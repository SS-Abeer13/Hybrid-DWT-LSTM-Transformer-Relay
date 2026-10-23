# Limitations and scope of the claims (thesis chapter draft, E3)

Every statement below is backed by a log entry in `IMPLEMENTATION_PLAN.md` (dated) and by a saved output file. Numbers are quoted from `tables.md`.

## 1. Simulation only, one plant
- All evidence comes from one Simulink / SimPowerSystems model: a 300 MVA, 230/11 kV, Y-Δ1 transformer behind a stiff source, with a constant-impedance load. There are no field recordings and no second transformer rating.
- The relay is evaluated at 1600 Hz sampling, 50 Hz nominal, source frequency 49.8–50.2 Hz in the main set and 49.5 / 50.5 Hz in the OOD set. Other sampling rates, 60 Hz systems and larger frequency excursions were not tested.
- The transformer model has terminal faults only (LV and HV winding terminals); there are no turn-to-turn or winding-internal faults, and one saturation characteristic.

## 2. Plant properties that shape the results (found during the work, not assumed)
- **Rated CT-secondary current is 0.9302 A on both sides.** The effective CT ratios (HV 809.6:1, LV 16,925:1) are 2.024 × the winding-voltage ratios written in the model; the original relay chart used neither this base nor the correct Yd1 matrix (it applied the transpose), so its 87T path voted "trip" on 91 % of healthy traces. The relay chart was corrected twice (log 2026-10-20 and 2026-10-21) and all results use the corrected calibration.
- **Weak external faults and LV voltage sag.** Three 0.5 Ω resistors sit in the LV line between the transformer terminals and the CT / load node and are part of how the LV CT subsystems are driven (lowering them to 0.02 Ω destroyed the LV CT output and was reverted). Consequences: external faults reach only ~1.5 pu rms at the CTs and the LV bus voltage falls to 0.84 pu at 30 % and 0.35 pu at 110 % of rated current. The relay only sees currents, but heavy-load cases are not realistic operating points, and "external fault with CT saturation" needed 4–10 × CT burden to reach a > 10 % ratio error.
- **CT remanence is not modelled.** The CT core-loss branch decays any initial flux in about 25 ms, long before the 0.30 s fault times (identical results for 0 and 0.6 pu). CT saturation therefore comes from burden, fault current and DC offset only.
- **Sympathetic inrush is not covered** (needs a second transformer); recovery (voltage-recovery) inrush is covered through a new HV-bus fault block, and its severity depends strongly on the clearing angle (0.1 to 1.9 pu differential for the same fault).
- The HV-side internal fault block and the HV-bus fault block were added to the model for this work (backups and pristine-reload procedure in the log).

## 3. Evaluation design
- **Cross-validation on one plant:** the 5-fold CV tests unseen traces, not unseen plants or unseen scenario families. The OOD set (300 traces) probes parameter ranges outside training (load, source strength, frequency, CT burden, over-excitation level, residual flux, noise, CT mismatch) but not new scenario types.
- **Undetectable faults are excluded from the headline numbers** (94 traces whose corrected differential rise is < 0.05 pu, mostly internal HiZ faults with Rf above ~7 Ω); they are reported separately (about 7 % trip).
- **Generator checks:** 99.2 % of traces pass the strict checks; two benign failure types (timing detected 12.5–20 ms late on very large currents; a noise-check artefact in over-excitation) are accepted by a documented rule (`v3_checks.py`), giving 99.9 % usable traces.
- **Small categories:** several categories have only 80–240 traces, so their Wilson intervals are wide (e.g. recovery inrush 93.8 % [86.2, 97.3] in one repetition; the three repetitions differ by up to 6 points). Quote the interval and the three-repetition mean, not a single value.
- **Thresholds** come from a validation-trace plateau rule and differ between folds (AI 0.950–0.997, solo 0.980–1.000); the final model uses AI 0.99 and solo 0.998.
- **The 12-case closed-loop benchmark is hand-picked**; its purpose is to show the deployed Simulink relay behaves like the Python mirror, the statistical evidence is the CV / OOD / D4 comparison.

## 4. Where the relay is weaker (measured)
- **High-impedance internal faults** (Rf 1.2–7 Ω, differential 0.05–0.30 pu, below the 87T pickup, found only through the AI-alone path): 71 % dependability in repetition 1 (95 % Wilson [60.5, 80.0]), against 80 % for the LSTM alone. This misses the ≥ 90 % target set before training. Below the detection limit (Rf 7–21 Ω) the relay does not operate (about 0–1 %), as expected.
- **Recovery inrush** is the weakest healthy category: 97.5 % mean over three repetitions (worst 93.8 %) against a ≥ 99 % target.
- **Operate time:** median 15.6 ms and 97 % within two cycles overall, but weak or masked faults are slower: in the closed-loop benchmark the HiZ fault in the AI-only band trips after 47.5 ms and a fault during inrush after 41.3 ms (criterion ≤ 30 ms met by 10 of 12 cases).
- **OOD (extreme CT burden 12–16 ×):** internal-fault dependability falls to 68 % (7 of 25 missed), a drop of more than the 5 points allowed without comment; security stays 100 %. Over-excitation 1.5–1.6 pu and residual flux 0.9 pu: dependability 93.3 %, security 100 %.
- **The AI-alone trip path** makes the relay AI-primary for faults the 87T cannot see; its false-trip risk on CT-saturated external faults is directly exposed (External CT-sat 98.8 – 100 % correct in the CV).
