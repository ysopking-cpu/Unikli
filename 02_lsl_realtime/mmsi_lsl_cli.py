# ==============================================================================
# MMSI v3.5 // HEADLESS LSL CLI STREAMER & TRIGGER LOGGER
# Pfad: /workspaces/Unikli/02_lsl_realtime/mmsi_lsl_cli.py
# ==============================================================================

import time
import numpy as np
from collections import deque
import mne


def run_headless_lsl_stream(duration_sec=10):
    print("[HEADLESS LSL] Initialisiere Offline-Replay-Streamer...")

    fif_path = "/workspaces/Unikli/data/physionet/S001R01_rest.fif"
    raw = mne.io.read_raw_fif(fif_path, preload=True, verbose=False)
    data = raw.get_data()
    sfreq = raw.info["sfreq"]

    buffer_size = int(sfreq * 0.5)
    buffer = deque(maxlen=buffer_size)

    d_baseline = 3.18
    d_target = 1.12
    trigger_threshold = 1.32

    print(f"[HEADLESS LSL] Starte Live-Simulation ({duration_sec}s Stream)...")
    print("-" * 65)

    start_time = time.time()
    total_samples = int(duration_sec * sfreq)
    for idx in range(total_samples):
        sample = data[:, idx % data.shape[1]]
        buffer.append(sample)

        if len(buffer) == buffer_size and idx % int(sfreq * 0.25) == 0:
            window_data = np.array(buffer).T
            cov = np.cov(window_data)
            eigs = np.maximum(np.linalg.eigvalsh(cov), 0)

            sum_l = np.sum(eigs)
            sum_l_sq = np.sum(eigs ** 2)
            d_alpha = (sum_l ** 2) / sum_l_sq if sum_l_sq > 0 else 0.0

            if d_alpha <= trigger_threshold:
                status = "TS_SINGULARITY (TRIGGER ACTIVE)"
                load_w = 0.0
            else:
                status = "TV_PROCESSING_LOAD"
                load_w = np.clip((d_alpha - d_target) / (d_baseline - d_target), 0.0, 1.0)

            t_rel = idx / sfreq
            print(f"t={t_rel:5.2f}s | d_alpha = {d_alpha:.3f} | W(t) = {load_w:.2f} | Status: {status}")

    print("-" * 65)
    print("[HEADLESS LSL] Simulation erfolgreich abgeschlossen.")


if __name__ == "__main__":
    run_headless_lsl_stream(duration_sec=5)
