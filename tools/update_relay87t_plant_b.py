"""Update relay87t.py to add Plant B configuration and support."""
from pathlib import Path

p = Path("F:/Transformer Thesis/lstm_models/relay87t.py")
text = p.read_text(encoding="utf-8")

old_block = """# v4 calibrated values (series CT wiring, simulations/ct_calibration_v4.txt)
CT_RATIO_HV_V4, CT_RATIO_LV_V4 = 404.7288, 8460.0372
I_NOM_V4 = 1.8610                                         # = 1.8610 A

# Active calibration default (v4)
CT_RATIO_HV, CT_RATIO_LV = CT_RATIO_HV_V4, CT_RATIO_LV_V4
I_NOM = I_NOM_V4
M_PLANT = (1 / np.sqrt(3)) * np.array([[1, 0, -1], [-1, 1, 0], [0, -1, 1]])   # column-vector form
I_PICKUP, I_HIGH_SET, SLOPE_1, SLOPE_2, BREAKPOINT = 0.30, 10.0, 0.25, 0.60, 3.0   # unchanged chart settings"""

new_block = """# v4 calibrated values (series CT wiring, simulations/ct_calibration_v4.txt)
CT_RATIO_HV_V4, CT_RATIO_LV_V4 = 404.7288, 8460.0372
I_NOM_V4 = 1.8610                                         # = 1.8610 A

# Plant B calibrated values (simulations/plant_b_checks.txt)
CT_RATIO_HV_PLANT_B, CT_RATIO_LV_PLANT_B = 202.0119, 808.8849
I_NOM_PLANT_B = 0.8232

# Active calibration default (Plant A, v4)
CT_RATIO_HV, CT_RATIO_LV = CT_RATIO_HV_V4, CT_RATIO_LV_V4
I_NOM = I_NOM_V4
M_PLANT = (1 / np.sqrt(3)) * np.array([[1, 0, -1], [-1, 1, 0], [0, -1, 1]])   # column-vector form
I_PICKUP, I_HIGH_SET, SLOPE_1, SLOPE_2, BREAKPOINT = 0.30, 10.0, 0.25, 0.60, 3.0   # unchanged chart settings


def get_plant_config(plant: str = "A") -> dict:
    \"\"\"Returns calibration and compensation matrix configuration for Plant A or Plant B.\"\"\"
    p_name = plant.upper()
    if p_name == "A":
        return {
            "name": "Plant A",
            "rating_mva": 300.0,
            "v_hv_kv": 230.0,
            "v_lv_kv": 11.0,
            "vector_group": "YNd1",
            "i_nom": I_NOM_V4,
            "ct_ratio_hv": CT_RATIO_HV_V4,
            "ct_ratio_lv": CT_RATIO_LV_V4,
            "m_hv": (1 / np.sqrt(3)) * np.array([[1, 0, -1], [-1, 1, 0], [0, -1, 1]]),
            "m_lv": np.eye(3),
        }
    elif p_name == "B":
        return {
            "name": "Plant B",
            "rating_mva": 40.0,
            "v_hv_kv": 132.0,
            "v_lv_kv": 33.0,
            "vector_group": "Dyn11",
            "i_nom": I_NOM_PLANT_B,
            "ct_ratio_hv": CT_RATIO_HV_PLANT_B,
            "ct_ratio_lv": CT_RATIO_LV_PLANT_B,
            "m_hv": np.eye(3),
            "m_lv": (1 / np.sqrt(3)) * np.array([[1, -1, 0], [0, 1, -1], [-1, 0, 1]]),
        }
    else:
        raise ValueError(f"Unknown plant '{plant}'; expected 'A' or 'B'.")"""

assert old_block in text, "old_block not found"
text = text.replace(old_block, new_block)

old_analyse = """def analyse(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP, i_nom: float = I_NOM) -> dict:
    \"\"\"primary/secondary: [T x 3] CT-secondary amps (HV, LV). Returns per-sample boolean 'vote' (any-phase 87T trip
    condition), 'highset' (Id > 10 pu, bypasses the AI) and the per-phase Id/Ir RMS in pu.\"\"\"
    hv = (primary / i_nom) @ M_PLANT.T
    lv = secondary / i_nom"""

new_analyse = """def analyse(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP, i_nom: float | None = None,
            plant: str = "A") -> dict:
    \"\"\"primary/secondary: [T x 3] CT-secondary amps (HV, LV). Returns per-sample boolean 'vote' (any-phase 87T trip
    condition), 'highset' (Id > 10 pu, bypasses the AI) and the per-phase Id/Ir RMS in pu.\"\"\"
    cfg = get_plant_config(plant)
    base = i_nom if i_nom is not None else cfg["i_nom"]
    hv = (primary / base) @ cfg["m_hv"].T
    lv = (secondary / base) @ cfg["m_lv"].T"""

assert old_analyse in text, "old_analyse not found"
text = text.replace(old_analyse, new_analyse)

old_fault_rise = """def fault_rise_pu(primary: np.ndarray, secondary: np.ndarray, onset: int, i_nom: float = I_NOM) -> float:
    \"\"\"Detectability: rise of the per-phase differential RMS (pu) 40-60 ms after the fault vs 10-30 ms before (as the generator did).\"\"\"
    d = (secondary / i_nom) - (primary / i_nom) @ M_PLANT.T"""

new_fault_rise = """def fault_rise_pu(primary: np.ndarray, secondary: np.ndarray, onset: int, i_nom: float | None = None,
                  plant: str = "A") -> float:
    \"\"\"Detectability: rise of the per-phase differential RMS (pu) 40-60 ms after the fault vs 10-30 ms before (as the generator did).\"\"\"
    cfg = get_plant_config(plant)
    base = i_nom if i_nom is not None else cfg["i_nom"]
    d = (secondary / base) @ cfg["m_lv"].T - (primary / base) @ cfg["m_hv"].T"""

assert old_fault_rise in text, "old_fault_rise not found"
text = text.replace(old_fault_rise, new_fault_rise)

old_harmonic = """def analyse_harmonic(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP,
                     k2_thresh: float = 0.15, k5_thresh: float = 0.35, mode: str = "per_phase",
                     i_nom: float = I_NOM) -> dict:"""

new_harmonic = """def analyse_harmonic(primary: np.ndarray, secondary: np.ndarray, pickup: float = I_PICKUP,
                     k2_thresh: float = 0.15, k5_thresh: float = 0.35, mode: str = "per_phase",
                     i_nom: float | None = None, plant: str = "A") -> dict:"""

assert old_harmonic in text, "old_harmonic not found"
text = text.replace(old_harmonic, new_harmonic)

old_harm_body = """    res = analyse(primary, secondary, pickup=pickup, i_nom=i_nom)
    hv = (primary / i_nom) @ M_PLANT.T
    lv = secondary / i_nom"""

new_harm_body = """    res = analyse(primary, secondary, pickup=pickup, i_nom=i_nom, plant=plant)
    cfg = get_plant_config(plant)
    base = i_nom if i_nom is not None else cfg["i_nom"]
    hv = (primary / base) @ cfg["m_hv"].T
    lv = (secondary / base) @ cfg["m_lv"].T"""

assert old_harm_body in text, "old_harm_body not found"
text = text.replace(old_harm_body, new_harm_body)

p.write_text(text, encoding="utf-8")
print("Successfully updated lstm_models/relay87t.py with Plant B support!")
