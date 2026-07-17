import os
import torch
import torch.nn as nn
import numpy as np
import scipy.io

# Define the exact model class
class TransformerProtectionLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout=0.3, bidirectional=True):
        super().__init__()
        D = 2 if bidirectional else 1
        self.lstm = nn.LSTM(
            input_size=input_size, hidden_size=hidden_size,
            num_layers=num_layers, batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=bidirectional
        )
        self.layer_norm = nn.LayerNorm(hidden_size * D)
        self.attention  = nn.Linear(hidden_size * D, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * D, 64), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(64, 1)
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        out     = self.layer_norm(out)
        w       = torch.softmax(self.attention(out), dim=1)
        ctx     = (w * out).sum(dim=1)
        return self.classifier(ctx).squeeze(-1)

def main():
    sim_file = r"f:\Downloads\Transformer Thesis\simulations\simulated_test_features.mat"
    model_path = r"f:\Downloads\Transformer Thesis\runs\20260601_lstm_training\transformer_protection_lstm_best.pth"
    
    if not os.path.exists(sim_file):
        print(f"Error: {sim_file} does not exist yet. Simulation might still be running.")
        return
        
    print("Loading simulated features...")
    data = scipy.io.loadmat(sim_file)
    
    print("Loading PyTorch model checkpoint...")
    ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    cfg = ckpt["model_config"]
    best_threshold = ckpt.get("best_threshold", 0.5617)
    
    print(f"Model Configuration: {cfg}")
    print(f"Optimal Decision Threshold: {best_threshold:.4f}")
    
    model = TransformerProtectionLSTM(
        input_size=cfg.get("input_size", 9),
        hidden_size=cfg.get("hidden_size", 128),
        num_layers=cfg.get("num_layers", 2),
        dropout=cfg.get("dropout", 0.3),
        bidirectional=cfg.get("bidirectional", True)
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print("OK: Model loaded and set to eval mode.\n")
    
    # List of cases (keys in simulated_test_features.mat)
    # scipy.io.loadmat imports structs as dicts. Nested fields are under key name.
    # The keys in the MAT file will be case names like 'Normal_Operation', 'Magnetizing_Inrush', etc.
    # Let's find all keys that represent case data
    case_keys = [k for k in data.keys() if not k.startswith("__")]
    
    print("="*80)
    print("      LSTM OFFLINE VERIFICATION REPORT (1600 Hz Sample Rate, 1.0s stop time)")
    print("="*80)
    print(f"{'Test Case':<25} | {'Exp. Decision':<13} | {'LSTM Peak Prob':<15} | {'LSTM Decision':<13} | {'Status':<6}")
    print("-"*80)
    
    for case_key in sorted(case_keys):
        case_data = data[case_key]
        # In scipy.io.loadmat, a struct is imported as a structured numpy array
        # Let's extract the fields safely
        try:
            # case_data is a numpy void array of shape (1, 1) or similar
            # field names can be accessed as attributes or dict keys
            features = case_data['features'][0, 0] # shape: (1569, 9, N_steps)
            time = case_data['time'][0, 0]         # shape: (N_steps, 1)
            should_trip = bool(case_data['shouldTrip'][0, 0][0, 0])
            tripped_conv = bool(case_data['trippedConventional'][0, 0][0, 0])
        except Exception as e:
            print(f"Error reading case {case_key}: {e}")
            continue
            
        # Reshape/transpose features from (1569, 9, N_steps) to (N_steps, 1569, 9)
        # In MATLAB it was 3D. In numpy:
        if features.ndim == 3:
            # (1569, 9, N_steps) -> transpose to (N_steps, 1569, 9)
            features_t = np.transpose(features, (2, 0, 1))
        else:
            # Handle fallback if N_steps is 1
            features_t = features.reshape(1, 1569, 9)
            
        # Run inference
        with torch.no_grad():
            x_tensor = torch.from_numpy(features_t).float()
            logits = model(x_tensor)
            probs = torch.sigmoid(logits).numpy()
            
        max_prob = float(np.max(probs))
        lstm_decision = "TRIP" if max_prob > best_threshold else "BLOCK"
        expected_decision = "TRIP" if should_trip else "BLOCK"
        
        status = "PASS" if lstm_decision == expected_decision else "FAIL"
        
        case_name_clean = case_key.replace("_", " ")
        print(f"{case_name_clean:<25} | {expected_decision:<13} | {max_prob:<15.4f} | {lstm_decision:<13} | {status:<6}")
        
    print("="*80)

if __name__ == "__main__":
    main()
