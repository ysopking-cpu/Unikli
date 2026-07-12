# ==============================================================================
# MMSI v3.5 // AUTONOMOUS PHYSIONET EEG DOWNLOADER & INGESTION ENGINE
# Pfad: /workspaces/Unikli/01_physionet_ingestion/mmsi_auto_downloader.py
# ==============================================================================

import os
import numpy as np
import mne
from mne.datasets import eegbci
import matplotlib.pyplot as plt


def download_and_process_eeg(subject=1, runs=[1, 2, 3, 4], target_dir="/workspaces/Unikli/data/physionet"):
    os.makedirs(target_dir, exist_ok=True)
    print(f"[DOWNLOADER] Starte automatischen PhysioNet-Download für Subjekt {subject:03d}, Runs {runs}...")

    local_files = eegbci.load_data(subjects=[subject], runs=runs, path=target_dir)
    print(f"[DOWNLOADER] {len(local_files)} EDF-Dateien erfolgreich auf Datenträger verankert:")
    for f in local_files:
        print(f"  -> {f}")

    print("[PROCESSING] Lade EDF-Signale in den Arbeitsspeicher...")
    raw_list = [mne.io.read_raw_edf(f, preload=True, verbose=False) for f in local_files]
    raw = mne.concatenate_raws(raw_list)

    sfreq = raw.info['sfreq']
    n_channels = len(raw.ch_names)

    print("[FILTER] Appliziere FIR-Bandpassfilter (8.0 - 12.0 Hz)...")
    raw_filtered = raw.copy().filter(l_freq=8.0, h_freq=12.0, fir_design='firwin', verbose=False)

    data, times = raw_filtered.get_data(), raw_filtered.times

    window_size = int(0.5 * sfreq)
    step_size = int(0.1 * sfreq)

    d_alpha_trajectory = []
    w_load_trajectory = []
    time_axis = []

    d_baseline = 3.18
    d_target = 1.12
    trigger_threshold = 1.32

    print("[MATHEMATICS] Berechne effektive Raumdimension d_alpha(t) & Systemische Last W(t)...")
    for start in range(0, data.shape[1] - window_size, step_size):
        end = start + window_size
        window_data = data[:, start:end]

        cov_matrix = np.cov(window_data)
        eigenvals = np.maximum(np.linalg.eigvalsh(cov_matrix), 0)

        sum_l = np.sum(eigenvals)
        sum_l_sq = np.sum(eigenvals ** 2)

        d_alpha = (sum_l ** 2) / sum_l_sq if sum_l_sq > 0 else 0.0

        if d_alpha <= trigger_threshold:
            w_load = 0.0
        else:
            w_load = np.clip((d_alpha - d_target) / (d_baseline - d_target), 0.0, 1.0)

        d_alpha_trajectory.append(d_alpha)
        w_load_trajectory.append(w_load)
        time_axis.append(times[start + window_size // 2])

    d_arr = np.array(d_alpha_trajectory)
    w_arr = np.array(w_load_trajectory)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, facecolor='#ffffff')

    ax1.plot(time_axis, d_arr, color='#1e3a8a', linewidth=1.2, label=r'Empirische Trajektorie $d_{\alpha}(t)$')
    ax1.axhline(y=trigger_threshold, color='#10b981', linestyle='--', label=r'$P_S$-Trigger Schwelle ($1.32$)')
    ax1.set_title(f'PhysioNet eegmmidb (S{subject:03d}) // Autonom heruntergeladene EEG-Realdaten', fontsize=12, fontweight='bold')
    ax1.set_ylabel(r'Raumdimension $d_{\alpha}$')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right')

    ax2.plot(time_axis, w_arr, color='#dc2626', linewidth=1.2, label=r'Systemische Reibung / Last $W(t)$')
    ax2.set_xlabel('Zeit (Sekunden)')
    ax2.set_ylabel(r'Systemische Last $W(t)$')
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right')

    output_png = "/workspaces/Unikli/01_physionet_ingestion/physionet_auto_download_result.png"
    plt.savefig(output_png, dpi=150, bbox_inches='tight')
    plt.close(fig)

    print(f"[OUTPUT] Download & Ingestion abgeschlossen. Grafik gespeichert: {output_png}")


if __name__ == "__main__":
    download_and_process_eeg(subject=1, runs=[1, 2, 3, 4])
