#include "relay_pipeline.h"
#include "relay_weights.h"
#include <math.h>
#include <string.h>
#include <immintrin.h>

static inline float sigmoid(float x) {
    return 1.0f / (1.0f + expf(-x));
}

static inline float tanhf_fast(float x) {
    return tanhf(x);
}

/* AVX2 + FMA 64-element dot product: 8 vector multiply-adds */
static inline float dot_64_avx2(const float *a, const float *b) {
    __m256 acc0 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 0),  _mm256_loadu_ps(b + 0),  _mm256_setzero_ps());
    __m256 acc1 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 8),  _mm256_loadu_ps(b + 8),  _mm256_setzero_ps());
    __m256 acc2 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 16), _mm256_loadu_ps(b + 16), _mm256_setzero_ps());
    __m256 acc3 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 24), _mm256_loadu_ps(b + 24), _mm256_setzero_ps());
    __m256 acc4 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 32), _mm256_loadu_ps(b + 32), _mm256_setzero_ps());
    __m256 acc5 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 40), _mm256_loadu_ps(b + 40), _mm256_setzero_ps());
    __m256 acc6 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 48), _mm256_loadu_ps(b + 48), _mm256_setzero_ps());
    __m256 acc7 = _mm256_fmadd_ps(_mm256_loadu_ps(a + 56), _mm256_loadu_ps(b + 56), _mm256_setzero_ps());

    __m256 sum01 = _mm256_add_ps(_mm256_add_ps(acc0, acc1), _mm256_add_ps(acc2, acc3));
    __m256 sum23 = _mm256_add_ps(_mm256_add_ps(acc4, acc5), _mm256_add_ps(acc6, acc7));
    __m256 sum = _mm256_add_ps(sum01, sum23);

    __m128 lo = _mm256_castps256_ps128(sum);
    __m128 hi = _mm256_extractf128_ps(sum, 1);
    __m128 sum128 = _mm_add_ps(lo, hi);
    sum128 = _mm_hadd_ps(sum128, sum128);
    sum128 = _mm_hadd_ps(sum128, sum128);
    return _mm_cvtss_f32(sum128);
}

void extract_features_12(const float win_3x32[3][32], float feat_out[12]) {
    float a1[19], d1[19], a2[13], d2[13];

    for (int p = 0; p < 3; p++) {
        const float *x = win_3x32[p];

        /* Level 1 DWT */
        float sum_sq_d1 = 0.0f;
        for (int i = 0; i < 19; i++) {
            float sa = 0.0f, sd = 0.0f;
            for (int j = 0; j < 32; j++) {
                sa += CONST_M_a1[i * 32 + j] * x[j];
                sd += CONST_M_d1[i * 32 + j] * x[j];
            }
            a1[i] = sa;
            d1[i] = sd;
            sum_sq_d1 += sd * sd;
        }

        /* Level 2 DWT */
        float sum_sq_d2 = 0.0f, sum_sq_a2 = 0.0f;
        for (int i = 0; i < 13; i++) {
            float sa = 0.0f, sd = 0.0f;
            for (int j = 0; j < 19; j++) {
                sa += CONST_M_a2[i * 19 + j] * a1[j];
                sd += CONST_M_d2[i * 19 + j] * a1[j];
            }
            a2[i] = sa;
            d2[i] = sd;
            sum_sq_d2 += sd * sd;
            sum_sq_a2 += sa * sa;
        }

        feat_out[p * 3 + 0] = log1pf(sum_sq_d1);
        feat_out[p * 3 + 1] = log1pf(sum_sq_d2);
        feat_out[p * 3 + 2] = log1pf(sum_sq_a2);

        /* 32-point FFT fundamental and 2nd harmonic */
        float r1 = 0.0f, i1 = 0.0f, r2 = 0.0f, i2 = 0.0f;
        for (int j = 0; j < 32; j++) {
            float val = x[j];
            r1 += val * CONST_fft_cos1[j];
            i1 -= val * CONST_fft_sin1[j];
            r2 += val * CONST_fft_cos2[j];
            i2 -= val * CONST_fft_sin2[j];
        }
        float mag1 = sqrtf(r1 * r1 + i1 * i1);
        float mag2 = sqrtf(r2 * r2 + i2 * i2);
        float ratio = mag2 / (mag1 + 1e-4f);
        feat_out[9 + p] = ratio > 2.0f ? 2.0f : ratio;
    }
}

float lstm_infer_probability(const float feat_seq[32][12]) {
    float h0[64] = {0.0f}, c0[64] = {0.0f};
    float h1[64] = {0.0f}, c1[64] = {0.0f};
    float seq_out[32][64];

    /* Process 32 time steps through 2-layer LSTM */
    for (int t = 0; t < 32; t++) {
        const float *xt = feat_seq[t];

        /* --- Layer 0 (input: 12, hidden: 64); new hidden state goes to h0n so that all 64 units use the PREVIOUS h0 --- */
        float h0n[64];
        for (int i = 0; i < 64; i++) {
            /* Input gate */
            float gi = B_L0[i] + dot_64_avx2(&W_HH_L0[i * 64], h0);
            for (int j = 0; j < 12; j++) gi += W_IH_L0[i * 12 + j] * xt[j];

            /* Forget gate */
            int ifg = 64 + i;
            float gf = B_L0[ifg] + dot_64_avx2(&W_HH_L0[ifg * 64], h0);
            for (int j = 0; j < 12; j++) gf += W_IH_L0[ifg * 12 + j] * xt[j];

            /* Cell gate */
            int igg = 128 + i;
            float gg = B_L0[igg] + dot_64_avx2(&W_HH_L0[igg * 64], h0);
            for (int j = 0; j < 12; j++) gg += W_IH_L0[igg * 12 + j] * xt[j];

            /* Output gate */
            int iog = 192 + i;
            float go = B_L0[iog] + dot_64_avx2(&W_HH_L0[iog * 64], h0);
            for (int j = 0; j < 12; j++) go += W_IH_L0[iog * 12 + j] * xt[j];

            float ig = sigmoid(gi);
            float fg = sigmoid(gf);
            float c_cand = tanhf_fast(gg);
            float og = sigmoid(go);

            c0[i] = fg * c0[i] + ig * c_cand;
            h0n[i] = og * tanhf_fast(c0[i]);
        }
        for (int i = 0; i < 64; i++) h0[i] = h0n[i];

        /* --- Layer 1 (input: 64, hidden: 64); same two-step update of h1 --- */
        float h1n[64];
        for (int i = 0; i < 64; i++) {
            float gi = B_L1[i] + dot_64_avx2(&W_IH_L1[i * 64], h0) + dot_64_avx2(&W_HH_L1[i * 64], h1);
            int ifg = 64 + i;
            float gf = B_L1[ifg] + dot_64_avx2(&W_IH_L1[ifg * 64], h0) + dot_64_avx2(&W_HH_L1[ifg * 64], h1);
            int igg = 128 + i;
            float gg = B_L1[igg] + dot_64_avx2(&W_IH_L1[igg * 64], h0) + dot_64_avx2(&W_HH_L1[igg * 64], h1);
            int iog = 192 + i;
            float go = B_L1[iog] + dot_64_avx2(&W_IH_L1[iog * 64], h0) + dot_64_avx2(&W_HH_L1[iog * 64], h1);

            float ig = sigmoid(gi);
            float fg = sigmoid(gf);
            float c_cand = tanhf_fast(gg);
            float og = sigmoid(go);

            c1[i] = fg * c1[i] + ig * c_cand;
            h1n[i] = og * tanhf_fast(c1[i]);
            seq_out[t][i] = h1n[i];
        }
        for (int i = 0; i < 64; i++) h1[i] = h1n[i];
    }

    /* --- LayerNorm over hidden dimension (64) for each time step --- */
    float norm_seq[32][64];
    for (int t = 0; t < 32; t++) {
        float mean = 0.0f;
        for (int j = 0; j < 64; j++) mean += seq_out[t][j];
        mean /= 64.0f;

        float var = 0.0f;
        for (int j = 0; j < 64; j++) {
            float diff = seq_out[t][j] - mean;
            var += diff * diff;
        }
        var /= 64.0f;
        float inv_std = 1.0f / sqrtf(var + 1e-5f);

        for (int j = 0; j < 64; j++) {
            norm_seq[t][j] = ((seq_out[t][j] - mean) * inv_std) * LN_WEIGHT[j] + LN_BIAS[j];
        }
    }

    /* --- Attention mechanism --- */
    float att_logits[32];
    float max_att = -1e30f;
    for (int t = 0; t < 32; t++) {
        float val = ATT_BIAS[0] + dot_64_avx2(ATT_WEIGHT, norm_seq[t]);
        att_logits[t] = val;
        if (val > max_att) max_att = val;
    }

    float sum_exp = 0.0f;
    float att_weights[32];
    for (int t = 0; t < 32; t++) {
        float e = expf(att_logits[t] - max_att);
        att_weights[t] = e;
        sum_exp += e;
    }
    float inv_sum = 1.0f / sum_exp;
    for (int t = 0; t < 32; t++) att_weights[t] *= inv_sum;

    /* Context vector */
    float context[64] = {0.0f};
    for (int t = 0; t < 32; t++) {
        float w = att_weights[t];
        for (int j = 0; j < 64; j++) {
            context[j] += w * norm_seq[t][j];
        }
    }

    /* --- Classifier: Dense(64,64) -> ReLU -> Dense(64,1) -> Sigmoid --- */
    float h_cls[64];
    for (int i = 0; i < 64; i++) {
        float val = FC0_BIAS[i] + dot_64_avx2(&FC0_WEIGHT[i * 64], context);
        h_cls[i] = val > 0.0f ? val : 0.0f; /* ReLU */
    }

    float logit = FC1_BIAS[0] + dot_64_avx2(FC1_WEIGHT, h_cls);
    return sigmoid(logit);
}

float relay_step(const float win_3x32[3][32], const float feat_seq[32][12]) {
    float f12[12];
    extract_features_12(win_3x32, f12);

    /* Build sequence with latest feature vector at the end */
    float seq_copy[32][12];
    for (int t = 0; t < 31; t++) {
        memcpy(seq_copy[t], feat_seq[t + 1], 12 * sizeof(float));
    }
    memcpy(seq_copy[31], f12, 12 * sizeof(float));

    return lstm_infer_probability(seq_copy);
}
