#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <windows.h>
#include "relay_pipeline.h"

int compare_double(const void *a, const void *b) {
    double da = *(const double *)a;
    double db = *(const double *)b;
    return (da > db) - (da < db);
}

int main(int argc, char **argv) {
    LARGE_INTEGER freq, t0, t1;
    QueryPerformanceFrequency(&freq);
    double freq_d = (double)freq.QuadPart;

    int n_warmup = 100;
    int n_calls = 10000;

    float win[3][32];
    float feat_seq[32][12];

    /* Initialise deterministic synthetic input signals */
    for (int p = 0; p < 3; p++) {
        for (int i = 0; i < 32; i++) {
            win[p][i] = (float)sin(2.0 * 3.1415926535 * (double)i / 32.0 + (double)p * 2.094);
        }
    }
    for (int t = 0; t < 32; t++) {
        for (int f = 0; f < 12; f++) {
            feat_seq[t][f] = (float)(0.1 * (t + 1) + 0.05 * (f + 1));
        }
    }

    /* --- Warm-up --- */
    float prob = 0.0f;
    float f12[12];
    for (int i = 0; i < n_warmup; i++) {
        extract_features_12(win, f12);
        prob = lstm_infer_probability(feat_seq);
        prob = relay_step(win, feat_seq);
    }

    /* --- 1. Benchmark Feature Extraction alone --- */
    double *times_dwt = (double *)malloc(n_calls * sizeof(double));
    double sum_dwt = 0.0;
    for (int i = 0; i < n_calls; i++) {
        QueryPerformanceCounter(&t0);
        extract_features_12(win, f12);
        QueryPerformanceCounter(&t1);
        double us = ((double)(t1.QuadPart - t0.QuadPart) * 1e6) / freq_d;
        times_dwt[i] = us;
        sum_dwt += us;
    }

    /* --- 2. Benchmark LSTM Inference alone --- */
    double *times_lstm = (double *)malloc(n_calls * sizeof(double));
    double sum_lstm = 0.0;
    for (int i = 0; i < n_calls; i++) {
        QueryPerformanceCounter(&t0);
        prob = lstm_infer_probability(feat_seq);
        QueryPerformanceCounter(&t1);
        double us = ((double)(t1.QuadPart - t0.QuadPart) * 1e6) / freq_d;
        times_lstm[i] = us;
        sum_lstm += us;
    }

    /* --- 3. Benchmark End-to-End Relay Step --- */
    double *times_relay = (double *)malloc(n_calls * sizeof(double));
    double sum_relay = 0.0;
    for (int i = 0; i < n_calls; i++) {
        QueryPerformanceCounter(&t0);
        prob = relay_step(win, feat_seq);
        QueryPerformanceCounter(&t1);
        double us = ((double)(t1.QuadPart - t0.QuadPart) * 1e6) / freq_d;
        times_relay[i] = us;
        sum_relay += us;
    }

    qsort(times_dwt, n_calls, sizeof(double), compare_double);
    qsort(times_lstm, n_calls, sizeof(double), compare_double);
    qsort(times_relay, n_calls, sizeof(double), compare_double);

    printf("RESULT_START\n");
    printf("dwt_mean=%.2f;dwt_median=%.2f;dwt_p90=%.2f;dwt_p95=%.2f;dwt_p99=%.2f;dwt_max=%.2f;dwt_min=%.2f\n",
           sum_dwt / n_calls, times_dwt[n_calls / 2], times_dwt[(int)(n_calls * 0.90)],
           times_dwt[(int)(n_calls * 0.95)], times_dwt[(int)(n_calls * 0.99)], times_dwt[n_calls - 1], times_dwt[0]);
    printf("lstm_mean=%.2f;lstm_median=%.2f;lstm_p90=%.2f;lstm_p95=%.2f;lstm_p99=%.2f;lstm_max=%.2f;lstm_min=%.2f\n",
           sum_lstm / n_calls, times_lstm[n_calls / 2], times_lstm[(int)(n_calls * 0.90)],
           times_lstm[(int)(n_calls * 0.95)], times_lstm[(int)(n_calls * 0.99)], times_lstm[n_calls - 1], times_lstm[0]);
    printf("relay_mean=%.2f;relay_median=%.2f;relay_p90=%.2f;relay_p95=%.2f;relay_p99=%.2f;relay_max=%.2f;relay_min=%.2f\n",
           sum_relay / n_calls, times_relay[n_calls / 2], times_relay[(int)(n_calls * 0.90)],
           times_relay[(int)(n_calls * 0.95)], times_relay[(int)(n_calls * 0.99)], times_relay[n_calls - 1], times_relay[0]);
    printf("prob=%.6f\n", prob);
    printf("RESULT_END\n");

    free(times_dwt);
    free(times_lstm);
    free(times_relay);
    return 0;
}
