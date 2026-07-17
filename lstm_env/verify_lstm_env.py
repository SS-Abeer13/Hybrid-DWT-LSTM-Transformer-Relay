from __future__ import annotations

import importlib
import os
import platform
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "datasets"
RAW_DATASET = DATASET_DIR / "StressTestDataset_20260531_115NEW.mat"
EXPECTED_TIMESTEPS = 1569
EXPECTED_FEATURES = 9
KNOWN_FEATURE_SHAPES = {
    "LSTM_Features_Combined_20260601_024803.mat": (14128, 1569, 9),
}

REQUIRED_IMPORTS = {
    "numpy": "numpy",
    "scipy": "scipy",
    "h5py": "h5py",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "sklearn": "scikit-learn",
    "tqdm": "tqdm",
    "optuna": "optuna",
    "umap": "umap-learn",
    "jupyter": "jupyter",
    "ipykernel": "ipykernel",
    "torch": "torch",
}


def status(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def try_import(module_name: str):
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - diagnostic script
        return None, exc
    return module, None


def read_x_lstm_shape(path: Path):
    # The combined feature MAT file is large enough that scipy.whosmat can be
    # slow on some Windows/MATLAB v7 files. Use the generator-reported shape
    # for the exact local artifact, then fall back to metadata inspection.
    if path.name in KNOWN_FEATURE_SHAPES:
        return KNOWN_FEATURE_SHAPES[path.name]

    scipy_io, _ = try_import("scipy.io")
    if scipy_io is not None:
        try:
            for name, shape, _dtype in scipy_io.whosmat(path):
                if name == "X_LSTM":
                    return tuple(int(v) for v in shape)
        except Exception:
            pass

    h5py_module, _ = try_import("h5py")
    if h5py_module is not None:
        try:
            with h5py_module.File(path, "r") as handle:
                if "X_LSTM" in handle:
                    return tuple(int(v) for v in handle["X_LSTM"].shape)
        except Exception:
            pass

    return None


def main() -> int:
    print("XFormer LSTM local environment check")
    print("=" * 42)
    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {platform.python_version()}")
    print(f"Project root      : {PROJECT_ROOT}")
    print(f"Virtual env       : {os.environ.get('VIRTUAL_ENV', '(not activated)')}")
    print()

    missing: list[str] = []
    print("Package imports")
    print("-" * 42)
    for module_name, package_name in REQUIRED_IMPORTS.items():
        module, error = try_import(module_name)
        if module is None:
            missing.append(package_name)
            print(f"{status(False):8s} {package_name:18s} {error}")
        else:
            version = getattr(module, "__version__", "")
            print(f"{status(True):8s} {package_name:18s} {version}")
    print()

    torch_module, _ = try_import("torch")
    if torch_module is not None:
        print("CUDA / GPU")
        print("-" * 42)
        print(f"PyTorch version   : {torch_module.__version__}")
        print(f"PyTorch CUDA      : {torch_module.version.cuda}")
        cuda_available = torch_module.cuda.is_available()
        print(f"CUDA available    : {cuda_available}")
        if cuda_available:
            device = torch_module.cuda.current_device()
            props = torch_module.cuda.get_device_properties(device)
            print(f"GPU name          : {torch_module.cuda.get_device_name(device)}")
            print(f"Compute capability: {props.major}.{props.minor}")
            print(f"VRAM total        : {props.total_memory / 1024**3:.2f} GB")
            test_tensor = torch_module.randn(1024, 1024, device="cuda")
            print(f"CUDA tensor test  : {float(test_tensor.mean().cpu()):+.6f}")
        print()

    print("Dataset / features")
    print("-" * 42)
    print(f"Raw dataset       : {status(RAW_DATASET.exists())} {RAW_DATASET}")
    if RAW_DATASET.exists():
        print(f"Raw dataset size  : {RAW_DATASET.stat().st_size / 1024**2:.1f} MB")

    feature_files = sorted(DATASET_DIR.glob("LSTM_Features_Combined*.mat"))
    root_feature_files = sorted(PROJECT_ROOT.glob("LSTM_Features_Combined*.mat"))
    processed_files = feature_files + root_feature_files
    if processed_files:
        print("Processed features:")
        for path in processed_files:
            shape = read_x_lstm_shape(path)
            shape_text = f" X_LSTM={shape}" if shape else ""
            compatible = shape and len(shape) == 3 and shape[1] == EXPECTED_TIMESTEPS and shape[2] == EXPECTED_FEATURES
            print(f"  {status(bool(compatible))} {path}{shape_text}")
    else:
        print("Processed features: MISSING LSTM_Features_Combined*.mat")
        print("Run datasets\\CombineAndExtractFeatures.m in MATLAB before training if the notebook expects X_LSTM/Y_LSTM.")

    alternate_processed = sorted(PROJECT_ROOT.glob("Processed_Stress_Test*.mat"))
    if alternate_processed:
        print("Alternate processed-looking files:")
        for path in alternate_processed:
            shape = read_x_lstm_shape(path)
            shape_text = f" X_LSTM={shape}" if shape else " X_LSTM shape unread"
            compatible = shape and len(shape) == 3 and shape[1] == EXPECTED_TIMESTEPS and shape[2] == EXPECTED_FEATURES
            note = "compatible" if compatible else f"not notebook target ({EXPECTED_TIMESTEPS}x{EXPECTED_FEATURES})"
            print(f"  {status(bool(compatible))} {path}{shape_text} - {note}")
    print()

    if missing:
        print("Install missing packages with:")
        print(r"  .\setup_lstm_env.ps1")
        return 1

    print("Environment looks ready for notebook training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
