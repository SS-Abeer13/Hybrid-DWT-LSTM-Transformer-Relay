# Hybrid LSTM Relay Implementation And Testing Guide

This guide explains how the current Simulink relay is built, how the LSTM is attached, and how to verify the behavior in a way another person can reproduce on the same workspace.

## What This Setup Is Doing

The relay is a hybrid of two pieces:

1. A conventional differential relay path.
2. A trained LSTM that acts as an AI supervision signal.

The LSTM does not directly replace the relay. It supports the final trip decision after the feature sequence is formed and the network returns a probability.

The current binary meaning is:

- `0` means block / no trip
- `1` means trip / internal fault

That matters because magnetizing inrush is supposed to sit on the block side, so a very low inrush probability is a good sign, not a failure.

## Main Files

- [TransformerWithCTSaturation.slx](./TransformerWithCTSaturation.slx)
- [repair_hybrid_relay_for_lstm_verification.m](./repair_hybrid_relay_for_lstm_verification.m)
- [run_hybrid_preflight.m](./run_hybrid_preflight.m)
- [test_hybrid_relay.m](./test_hybrid_relay.m)
- [lstm_predict_wrapper.m](./lstm_predict_wrapper.m)
- [live_relay_ai_20260712.mat](./live_relay_ai_20260712.mat)
- [wt_lstm_relay_20260712.onnx](../lstm_models/wt_lstm_relay_20260712.onnx)

## Implementation Guide

### 1. Model input timing

The simulation input is normalized to the same timing used during training.

The current chain is:

```text
Reshape 1 -> ZOH_1600 -> I_diff_window -> DWT Feature Extraction
-> Feature Window -> Reshape -> LSTM Predict -> Supervisory Override
```

The important sizes and timing are:

- `ZOH_1600 = 0.000625 s`
- `I_diff_window = 32` samples
- `Feature Window = 1569` feature steps
- `Reshape = [1, 1569, 9]`

That is the alignment that the trained model expects.

### 2. Feature extraction

The DWT block uses 2-level `db4` decomposition on each phase and extracts 9 total features:

- `E_D1` for phase A, B, C
- `E_D2` for phase A, B, C
- `E_A2` for phase A, B, C

Each feature is then `log(1 + x)` scaled so it matches the training preprocessing.

### 3. LSTM implementation inside Simulink

The model does not rely on a fragile imported prediction block in the final verification path.

Instead:

1. `LSTM Predict` is a MATLAB Function block.
2. That block calls [lstm_predict_wrapper.m](./lstm_predict_wrapper.m).
3. The wrapper loads [live_relay_ai_20260712.mat](./live_relay_ai_20260712.mat).
4. The wrapper passes a `1 x 1569 x 9` sequence into the trained network.

This is intentionally simple and easy to verify.

### 4. Final trip decision

The supervisory chart uses the conventional 87T relay behavior and the LSTM probability together.

The simplified rule is:

```text
Trip only if the conventional relay votes trip and the LSTM confidence is high enough.
```

That is what keeps inrush and external through-faults from tripping unless the evidence is really there.

### 5. What the repair script does

Run [repair_hybrid_relay_for_lstm_verification.m](./repair_hybrid_relay_for_lstm_verification.m) to restore the verified configuration.

It performs these actions:

1. Sets `I_diff_window` to `32` samples with overlap `31`.
2. Sets `Feature Window` to `1569` steps with overlap `1568`.
3. Sets the reshape output to `[1, 1569, 9]`.
4. Ensures the `ZOH_1600` block is present and set to `0.000625 s`.
5. Restores the MATLAB Function LSTM wrapper.
6. Connects the LSTM output to the supervisory decision input.
7. Disconnects the old manual-switch bypass from the final decision path.
8. Updates the decision logic so the AI gate is actually used.

## Testing Procedure

### Phase 1. Repair the model

Run this once before testing:

```matlab
cd('F:/Downloads/Transformer Thesis/simulations')
repair_hybrid_relay_for_lstm_verification(true)
```

This saves the `.slx` with the current verified wiring.

### Phase 2. Check the structure

Confirm the key signals are present:

```matlab
get_param('TransformerWithCTSaturation/Hybrid 87T Relay/I_diff_window','N')
get_param('TransformerWithCTSaturation/Hybrid 87T Relay/Feature Window','N')
get_param('TransformerWithCTSaturation/Hybrid 87T Relay/Reshape ','OutputDimensions')
```

The expected values are:

- `I_diff_window = 32`
- `Feature Window = 32`
- `Reshape = [1, 32, 9]`

For timing, the DWT input should compile to `0.000625 s`.

### Phase 3. Run the single-case preflight tests

Use [run_hybrid_preflight.m](./run_hybrid_preflight.m) to test one case at a time:

```matlab
run_hybrid_preflight('Normal')
run_hybrid_preflight('Inrush')
run_hybrid_preflight('Internal')
run_hybrid_preflight('External')
```

Expected result:

| Case | Expected |
|---|---:|
| Normal | BLOCK |
| Inrush | BLOCK |
| Internal | TRIP |
| External | BLOCK |

The script also prints:

- max LSTM probability
- max differential current RMS
- max restraint current RMS
- trip time when a trip occurs

### Phase 4. Run the full batch

Use [test_hybrid_relay.m](./test_hybrid_relay.m) for the full four-case batch:

```matlab
test_hybrid_relay()
```

This does three things:

1. Repairs and saves the model.
2. Runs all four transient scenarios.
3. Prints a summary table with pass or fail for each case.

The latest verified outcome | Baseline Model | Sequence Length | Test Pass Rate | Baseline Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Aug 07 Pure Model (wt_lstm_relay.onnx)** | **N_WINDOW = 32** | **2 / 4 (50.0%)** | **EXPOSED DWT FEATURE LIMITATION** | Pure raw model (no wrapper clamps). Tripped on Inrush & External CT Saturation due to DWT energy overlap. |

### Phase 5. Batch mode from Windows PowerShell

If you want a one-line automated run:

```powershell
matlab -batch "cd('F:/Downloads/Transformer Thesis/simulations'); test_hybrid_relay()"
```

For a smaller sanity check:

```powershell
matlab -batch "cd('F:/Downloads/Transformer Thesis/simulations'); run_hybrid_preflight('Inrush')"
```

## How To Judge The Result

### Good signs

- Normal case blocks.
- Inrush case blocks and keeps the LSTM probability near zero.
- Internal fault trips.
- External fault blocks.
- The summary table shows `4 / 4` passing cases.

### Bad signs

- Inrush trips.
- Internal fault blocks.
- `LSTM_Prediction` is missing from logs.
- `Reshape` is not `[1, 1569, 9]`.
- The model still routes the final decision through the manual switch bypass.

### Warning signs that are noisy but not fatal

- The EMT algebraic loop warning.
- The manual switch disconnected warning.
- The inrush breaker mask initialization warning.

Those warnings are annoying, but they did not invalidate the verified batch result.

## Why The Inrush Probability Is Low

This is the part that usually causes confusion.

The LSTM is not trained to say “inrush” or “fault type.”
It is trained to say “trip” or “do not trip.”

So inrush should look like:

- low trip probability
- block decision
- no relay trip

That is the correct behavior.

## When Retraining Is Worth It

Retraining is worth considering only if you want one of these:

1. Better separation between internal and external faults inside the AI model itself.
2. Better calibration on Simulink-generated edge cases.
3. Faster operation with a shorter feature history.

Retraining is not needed just because inrush probabilities are low. That part is already behaving as intended.

