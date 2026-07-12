# ==============================================================================
# MMSI v3.5 // PROTOKOLL 02: REAL-TIME LSL PIPELINE (KALIBRIERT VIA VEKTOR 01)
# Pfad: /workspaces/Unikli/02_lsl_realtime/mmsi_lsl_realtime.py
# ==============================================================================
import time
import numpy as np
from collections import deque


class MMSIRealTimeBuffer:
    """
    Simuliert einen hochfrequenten LSL-Stream-Inlet mit Ringpuffer
    zur Echtzeit-Berechnung von d_alpha(t) für rt-fMRT / BCI Closed-Loop.
    Kalibriert via PhysioNet eegmmidb (Subject 01, Runs 01/02/03/04).
    """
    def __init__(self, n_channels=64, sfreq=160, window_duration=0.5):
        self.n_channels = n_channels
        self.sfreq = sfreq
        self.buffer_size = int(sfreq * window_duration)
        self.buffer = deque(maxlen=self.buffer_size)

        # Empirisch injizierte Parameter aus Vektor 01 (PhysioNet eegmmidb)
        self.d_baseline = 3.18
        self.d_target = 1.12
        self.trigger_threshold = 1.32
        self.noise_variance = 0.014

    def push_sample(self, sample):
        self.buffer.append(sample)

    def is_ready(self):
        return len(self.buffer) == self.buffer_size

    def compute_current_d_alpha(self):
        if not self.is_ready():
            return None
        data = np.array(self.buffer).T
        cov_matrix = np.cov(data)
        eigenvals = np.maximum(np.linalg.eigvalsh(cov_matrix), 0)
        sum_l = np.sum(eigenvals)
        sum_l_sq = np.sum(eigenvals ** 2)
        if sum_l_sq == 0:
            return 0.0
        return (sum_l ** 2) / sum_l_sq

    def evaluate_state(self, d_alpha):
        """
        Klassifiziert den kognitiven Zustand auf Basis der empirischen Baselines
        und berechnet die systemische Last W(t) inklusive stochastischem Rauschen.
        """
        noise = np.random.normal(0, np.sqrt(self.noise_variance))
        d_alpha_noisy = d_alpha + noise

        if d_alpha_noisy <= self.trigger_threshold:
            return "TS_SINGULARITY_ACTIVE", 0.0
        else:
            load = (d_alpha_noisy - self.d_target) / (self.d_baseline - self.d_target)
            return "TV_PROCESSING_LOAD", float(np.clip(load, 0.0, 1.0))


def simulate_realtime_stream():
    n_channels = 64
    sfreq = 160
    rt_buffer = MMSIRealTimeBuffer(n_channels=n_channels, sfreq=sfreq, window_duration=0.5)

    print("[STREAM] Starte LSL-Real-Time Simulation (kalibriert)...")
    print(f"[STREAM] Trigger-Schwelle: d_alpha <= {rt_buffer.trigger_threshold}")

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > 10.0:
            break

        if elapsed < 5.0:
            sample = np.random.normal(0, 1.0, n_channels)
        else:
            base_signal = np.sin(2 * np.pi * 10 * elapsed)
            sample = base_signal + np.random.normal(0, 0.1, n_channels)

        rt_buffer.push_sample(sample)

        if rt_buffer.is_ready() and int(elapsed * 100) % 25 == 0:
            d_alpha = rt_buffer.compute_current_d_alpha()
            state, load_w = rt_buffer.evaluate_state(d_alpha)
            print(f"t={elapsed:.2f}s | d={d_alpha:.3f} | state={state} | W(t)={load_w:.3f}")

        time.sleep(1 / sfreq)


if __name__ == '__main__':
    simulate_realtime_stream()
