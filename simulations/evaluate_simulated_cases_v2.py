"""
evaluate_simulated_cases_v2.py
Training-consistent offline evaluation of the WT-LSTM relay.

Why v2 exists
-------------
Training (FeatureExtractor.m -> X_LSTM) uses ONE full [1569 x 9] sequence per
scenario and assigns ONE label. The original evaluate_simulated_cases.py instead
ran the model on all 1601 rolling buffer states and took the MAX probability,
which includes partial / zero-padded early windows and over-triggers.

v2 evaluates the SAME representation the model was trained on: the completed
final window  features[:, :, -1]  -> a single [1569 x 9] sequence -> one forward
pass -> one probability. It also prints the old max-rolling number for contrast,
and prints provenance so train/test calibration mismatch is visible.
"""
import os, datetime
import torch, torch.nn as nn, numpy as np, scipy.io as sio
from pathlib import Path

# Project root resolved from this script's location (simulations/ -> root)
BASE       = str(Path(__file__).resolve().parent.parent)
SIM_FILE   = os.path.join(BASE, r"simulations\simulated_test_features.mat")
MODEL_PATH = os.path.join(BASE, r"runs\20260601_lstm_training\transformer_protection_lstm_best.pth")
# Training feature set (for provenance / distribution-shift awareness)
TRAIN_FEATURES = os.path.join(BASE, r"datasets\LSTM_Features_Combined_20260601_024803.mat")

class TransformerProtectionLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout=0.3, bidirectional=True):
        super().__init__(); D = 2 if bidirectional else 1
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0, bidirectional=bidirectional)
        self.layer_norm = nn.LayerNorm(hidden_size * D)
        self.attention  = nn.Linear(hidden_size * D, 1)
        self.classifier = nn.Sequential(nn.Linear(hidden_size * D, 64), nn.ReLU(),
                                         nn.Dropout(dropout), nn.Linear(64, 1))
    def forward(self, x):
        out, _ = self.lstm(x); out = self.layer_norm(out)
        w = torch.softmax(self.attention(out), dim=1)
        ctx = (w * out).sum(dim=1)
        return self.classifier(ctx).squeeze(-1)

def mtime(p):
    return datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d") if os.path.exists(p) else "MISSING"

def main():
    print("=== PROVENANCE ===")
    print(f"  training features : {os.path.basename(TRAIN_FEATURES)}  (built {mtime(TRAIN_FEATURES)})")
    print(f"  test features     : {os.path.basename(SIM_FILE)}  (built {mtime(SIM_FILE)})")
    print(f"  model checkpoint  : {os.path.basename(MODEL_PATH)}  (trained {mtime(MODEL_PATH)})")
    print("  NOTE: for a valid comparison, training features and test features")
    print("        must come from the SAME calibration/pipeline.\n")

    ck  = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    cfg = ck["model_config"]; thr = float(ck.get("best_threshold", 0.5617))
    model = TransformerProtectionLSTM(cfg.get("input_size", 9), cfg.get("hidden_size", 64),
                                      cfg.get("num_layers", 2), cfg.get("dropout", 0.3),
                                      cfg.get("bidirectional", False))
    model.load_state_dict(ck["model_state_dict"]); model.eval()
    print(f"threshold = {thr:.4f}   config = hidden{cfg.get('hidden_size')} "
          f"layers{cfg.get('num_layers')} bidir{cfg.get('bidirectional')}\n")

    data = sio.loadmat(SIM_FILE)
    exp = {'Normal_Operation':0, 'Magnetizing_Inrush':0, 'Internal_A_G_Fault':1, 'External_3_Fault':0}
    order = ['Normal_Operation', 'Magnetizing_Inrush', 'Internal_A_G_Fault', 'External_3_Fault']

    print(f"{'Case':22s} {'Exp':4s} | {'p(final-seq)':12s} {'decision':8s} {'status':6s} | {'p(max-roll)':11s}")
    print("-"*78)
    for c in order:
        feats = data[c]['features'][0,0]          # (1569, 9, 1601)
        # Training-consistent: the completed final window is the full-run sequence
        full = feats[:, :, -1].astype(np.float32)  # (1569, 9)
        with torch.no_grad():
            p_full = float(torch.sigmoid(model(torch.from_numpy(full)[None])).item())
        # Old rule (max over all rolling buffers) for contrast, chunked
        X = np.transpose(feats, (2,0,1)).astype(np.float32)   # (1601,1569,9)
        pr = np.empty(X.shape[0], np.float32)
        with torch.no_grad():
            for i in range(0, X.shape[0], 128):
                pr[i:i+128] = torch.sigmoid(model(torch.from_numpy(X[i:i+128]))).numpy()
        p_roll = float(pr.max())
        dec = "TRIP" if p_full > thr else "BLOCK"
        st  = "PASS" if (dec=="TRIP")==bool(exp[c]) else "FAIL"
        print(f"{c:22s} {('TRIP' if exp[c] else 'BLOCK'):4s} | {p_full:<12.4f} {dec:8s} {st:6s} | {p_roll:<11.4f}")

if __name__ == "__main__":
    main()
