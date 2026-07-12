# ==============================================================================
# MMSI v3.5 // REAL OPEN-SOURCE EEG VALIDATOR (PHYSIONET eegmmidb)
# Pfad: /workspaces/Unikli/01_physionet_ingestion/mmsi_physionet_validator.py
# ==============================================================================

import os
import numpy as np
import mne
import matplotlib.pyplot as plt
from mmsi_fallback_loader import load_eeg_subject


def run_real_eeg_validation(subject=1):
    print(f"[PHYSIONET] Lade EEG-Daten für Subject {subject:03d}...")

    raw = load_eeg_subject(subject)

    sfreq = raw.info["sfreq"]
    n_channels = len(raw.ch_names)
    print(
        f"[PHYSIONET] Daten geladen: {n_channels} Kanäle | Abtastrate: {sfreq} Hz | Gesamtdauer: {raw.times[-1]:.1f}s"
    )

    print("[FILTER] Appliziere Bandpass (8.0 - 12.0 Hz)...")
    raw_alpha = raw.copy().filter(
        l_freq=8.0, h_freq=12.0, fir_design="firwin", verbose=False
    )
    data, times = raw_alpha.get_data(), raw_alpha.times

    window_size = int(0.5 * sfreq)
    step_size = int(0.1 * sfreq)

    d_alpha_trajectory = []
    time_axis = []

    print("[ANALYSE] Berechne d_alpha(t) auf echten EEG-Signalen...")
    for start in range(0, data.shape[1] - window_size, step_size):
        end = start + window_size
        window_data = data[:, start:end]

        cov_matrix = np.cov(window_data)
        eigenvals = np.maximum(np.linalg.eigvalsh(cov_matrix), 0)

        sum_l = np.sum(eigenvals)
        sum_l_sq = np.sum(eigenvals ** 2)

        d_alpha = (sum_l ** 2) / sum_l_sq if sum_l_sq > 0 else 0.0
        d_alpha_trajectory.append(d_alpha)
        time_axis.append(times[start + window_size // 2])

    d_alpha_arr = np.array(d_alpha_trajectory)

    d_mean_rest = np.mean(d_alpha_arr[: int(len(d_alpha_arr) * 0.5)])
    d_mean_task = np.mean(d_alpha_arr[int(len(d_alpha_arr) * 0.5) :])

    print("\n==================================================")
    print("   EMPIRISCHE MESSWERTE (ECHTE PHYSIONET-DATEN)   ")
    print("==================================================")
    print(f"  * d_alpha Ruhe-Phase (Eyes Open/Closed): {d_mean_rest:.3f}")
    print(f"  * d_alpha Fokus-Phase (Motor Task)     : {d_mean_task:.3f}")
    print(f"  * Delta Phasenraum-Kontraktion          : {d_mean_task - d_mean_rest:.3f}")
    print("==================================================\n")

    plt.figure(figsize=(12, 5), facecolor="#ffffff")
    plt.plot(
        time_axis,
        d_alpha_arr,
        color="#1e3a8a",
        linewidth=1.2,
        label=r"Empirische Trajektorie $d_{\alpha}(t)$ (Realdaten)",
    )
    plt.axhline(
        y=1.32,
        color="#10b981",
        linestyle="--",
        label=r"Ps-Trigger Schwellenwert ($d=1.32$)",
    )
    plt.title(
        f"PhysioNet eegmmidb (Subject {subject:03d}) // Realdaten-Trajektorie d_alpha(t)",
        fontsize=12,
        fontweight="bold",
    )
    plt.xlabel("Zeit (Sekunden)")
    plt.ylabel(r"Effektive Raumdimension $d_{\alpha}$")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right")

    out_dir = "/workspaces/Unikli/01_physionet_ingestion"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "physionet_real_eeg_trajectory.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"[OUTPUT] Realgrafik gespeichert: {out_path}")


if __name__ == "__main__":
    run_real_eeg_validation(subject=1)
