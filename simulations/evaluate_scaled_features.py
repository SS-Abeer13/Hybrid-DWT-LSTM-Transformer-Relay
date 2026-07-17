import os
import torch
import torch.nn as nn
import numpy as np
import scipy.io

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
    sim_file = r"f:\Downloads\Transformer Thesis\simulations\scaled_features_test.mat"
    model_path = r"f:\Downloads\Transformer Thesis\runs\20260601_lstm_training\transformer_protection_lstm_best.pth"
    
    data = scipy.io.loadmat(sim_file)
    features = data['feat_data'] # shape: (1569, 9, 1601)
    
    # Transpose to (1601, 1569, 9)
    features_t = np.transpose(features, (2, 0, 1))
    
    ckpt = torch.load(model_path, map_location="cpu")
    cfg = ckpt["model_config"]
    
    model = TransformerProtectionLSTM(
        input_size=cfg.get("input_size", 9),
        hidden_size=cfg.get("hidden_size", 128),
        num_layers=cfg.get("num_layers", 2),
        dropout=cfg.get("dropout", 0.3),
        bidirectional=cfg.get("bidirectional", True)
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    with torch.no_grad():
        x_tensor = torch.from_numpy(features_t).float()
        logits = model(x_tensor)
        probs = torch.sigmoid(logits).numpy()
        
    print("Features stats in memory:")
    print(f"  Shape: {features_t.shape}")
    print(f"  Min  : {np.min(features_t):.6f}")
    print(f"  Max  : {np.max(features_t):.6f}")
    print(f"  Mean : {np.mean(features_t):.6f}")
    
    print("\nLSTM Prediction results:")
    print(f"  Max Probability overall: {np.max(probs):.6f}")
    print(f"  Min Probability overall: {np.min(probs):.6f}")
    print(f"  Mean Probability overall: {np.mean(probs):.6f}")
    
    # Print the probability values for the last few steps (when buffer contains the fault)
    print("\nLast 10 steps probabilities:")
    for idx in range(1591, 1601):
        print(f"  Step {idx}: prob={probs[idx]:.6f}")

if __name__ == "__main__":
    main()
