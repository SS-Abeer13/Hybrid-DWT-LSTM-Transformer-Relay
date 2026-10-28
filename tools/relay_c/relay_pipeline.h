#ifndef RELAY_PIPELINE_H
#define RELAY_PIPELINE_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Computes 12 features from a 32-sample sliding window of 3-phase differential currents.
 * Input: win_3x32 [3][32] (phase A, B, C; 32 samples each)
 * Output: feat_out [12]
 */
void extract_features_12(const float win_3x32[3][32], float feat_out[12]);

/*
 * Evaluates the 2-layer LSTM + attention + classifier network on a sequence of 32 feature vectors.
 * Input: feat_seq [32][12]
 * Returns: scalar trip probability in [0, 1]
 */
float lstm_infer_probability(const float feat_seq[32][12]);

/*
 * Complete relay sample step:
 * Extracts 12 features from current window and evaluates the LSTM sequence.
 */
float relay_step(const float win_3x32[3][32], const float feat_seq[32][12]);

#ifdef __cplusplus
}
#endif

#endif /* RELAY_PIPELINE_H */
