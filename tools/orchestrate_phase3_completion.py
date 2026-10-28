"""Phase 3 & Publication Pipeline Automated Orchestrator.

Continuously monitors Plant B main generation, and upon completion automatically executes:
1. Plant B Out-of-Distribution (OOD) generation (150 traces).
2. Coverage verification (coverage_report_v4.py).
3. Plant B closed-loop 12-case suite in Simulink with active LSTM.
4. All three Plant B generalization experiments (Zero-shot, Cross-plant, Leave-one-out).
5. Compilation of all 8 LaTeX publication tables (build_publication_tables.py).
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = ROOT / "datasets"
SIM_DIR = ROOT / "simulations"
TOOLS_DIR = ROOT / "tools"


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(ROOT / "phase3_orchestrator.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_cmd(cmd: str | list[str], desc: str) -> int:
    log(f"Starting: {desc}")
    log(f"Command: {cmd}")
    t0 = time.time()
    res = subprocess.run(cmd, shell=True, cwd=str(ROOT))
    elapsed = time.time() - t0
    log(f"Finished: {desc} in {elapsed:.1f} s with return code {res.returncode}")
    if res.returncode != 0:
        log(f"ERROR: {desc} failed with exit code {res.returncode}")
    return res.returncode


def get_main_run_id() -> str | None:
    id_file = DATASETS_DIR / "stress_plant_b_main_runid.txt"
    if id_file.is_file():
        return id_file.read_text(encoding="utf-8").strip()
    return None


def wait_for_main_dataset() -> Path:
    log("Waiting for Plant B main dataset generation to complete...")
    run_id = get_main_run_id()
    while not run_id:
        time.sleep(10)
        run_id = get_main_run_id()
    
    final_file = DATASETS_DIR / f"StressDataset_PlantB_{run_id}.mat"
    log(f"Tracking final file: {final_file}")

    last_log_line = ""
    while not final_file.is_file():
        log_file = DATASETS_DIR / "stress_plant_b_main_generate_log.txt"
        if log_file.is_file():
            try:
                lines = log_file.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                if lines:
                    recent = lines[-1]
                    if recent != last_log_line:
                        last_log_line = recent
                        log(f"Progress: {recent}")
            except Exception:
                pass
        time.sleep(30)

    log(f"SUCCESS: Found finalized Plant B dataset: {final_file} ({final_file.stat().st_size} bytes)")
    # Brief pause to ensure MATLAB process has fully terminated
    time.sleep(10)
    return final_file


def generate_ood_dataset() -> Path:
    log("=" * 80)
    log("STEP 1: Generating Plant B Out-of-Distribution (OOD) Dataset (150 traces)...")
    log("=" * 80)
    cmd = r".\run_stress_plant_b_generate.bat 150 OOD"
    rc = run_cmd(cmd, "Plant B OOD generation (150 traces)")
    if rc != 0:
        raise RuntimeError("Plant B OOD generation failed.")
    
    # Locate generated OOD file
    ood_files = sorted(DATASETS_DIR.glob("StressDataset_PlantBOOD_*.mat"), key=os.path.getmtime)
    if not ood_files:
        raise FileNotFoundError("Could not find generated StressDataset_PlantBOOD_*.mat file.")
    ood_file = ood_files[-1]
    log(f"Plant B OOD dataset generated: {ood_file}")
    time.sleep(5)
    return ood_file


def verify_coverage(main_mat: Path):
    log("=" * 80)
    log("STEP 2: Verifying Coverage Criteria on Plant B Main Dataset...")
    log("=" * 80)
    cmd = f'python lstm_models/coverage_report_v4.py "{main_mat}"'
    rc = run_cmd(cmd, "Plant B Coverage Verification")
    if rc != 0:
        log("WARNING: Coverage report returned non-zero code; proceeding with caution.")


def run_closed_loop():
    log("=" * 80)
    log("STEP 3: Running Plant B 12-Case Dynamic Closed-Loop Simulink Validation...")
    log("=" * 80)
    cmd = 'matlab -batch "cd(\'simulations\'); generate_stress_dataset_plant_b(\'closedloop\'); exit;"'
    rc = run_cmd(cmd, "Plant B 12-case closed-loop test")
    if rc != 0:
        raise RuntimeError("Plant B closed-loop validation failed.")


def run_generalization():
    log("=" * 80)
    log("STEP 4: Running Three Publication Generalization Experiments...")
    log("=" * 80)
    cmd = "python tools/run_plant_b_generalization.py --mode all"
    rc = run_cmd(cmd, "Plant B Generalization Experiments (Zero-shot, Cross-plant, Leave-one-out)")
    if rc != 0:
        raise RuntimeError("Plant B generalization experiments failed.")


def compile_tables():
    log("=" * 80)
    log("STEP 5: Compiling All 8 LaTeX Publication Tables...")
    log("=" * 80)
    cmd = "python tools/build_publication_tables.py"
    rc = run_cmd(cmd, "LaTeX Publication Tables Compilation")
    if rc != 0:
        raise RuntimeError("Publication tables compilation failed.")


def main():
    log("PHASE 3 & PUBLICATION AUTOMATED ORCHESTRATOR STARTED.")
    main_mat = wait_for_main_dataset()
    ood_mat = generate_ood_dataset()
    verify_coverage(main_mat)
    run_closed_loop()
    run_generalization()
    compile_tables()
    log("=" * 80)
    log("ALL PHASES UP TO PUBLICATION TABLES COMPLETE! READY FOR FINAL MANUSCRIPT REVIEW.")
    log("=" * 80)


if __name__ == "__main__":
    main()
