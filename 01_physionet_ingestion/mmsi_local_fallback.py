# ==============================================================================
# MMSI v3.5 // LOCAL BIDS FALLBACK GENERATOR
# Pfad: /workspaces/Unikli/01_physionet_ingestion/mmsi_local_fallback.py
# ==============================================================================

import os
import numpy as np
import mne
from mne.io import RawArray
import matplotlib.pyplot as plt


def generate_local_bids_eeg(
    output_dir="/workspaces/Unikli/data/physionet",
    n_subjects=5,
    target_channels=None,
    sfreq=160,
    duration_rest=60,
    duration_task=60,
):
    os.makedirs(output_dir, exist_ok=True)
    montage = mne.channels.make_standard_montage("standard_1020")
    ch_names = target_channels if target_channels is not None else montage.ch_names[:64]
    n_channels = len(ch_names)

    for sub in range(1, n_subjects + 1):
        n_rest = int(sfreq * duration_rest)
        n_task = int(sfreq * duration_task)
        t_rest = np.linspace(0, duration_rest, n_rest)
        t_task = np.linspace(0, duration_task, n_task)
        data_rest = np.zeros((n_channels, n_rest))
        data_task = np.zeros((n_channels, n_task))

        for ch in range(n_channels):
            f = np.random.uniform(8, 12)
            phase = np.random.uniform(0, 2 * np.pi)
            data_rest[ch] = np.sin(2 * np.pi * f * t_rest + phase) + np.random.normal(0, 0.6, n_rest)
            base = np.sin(2 * np.pi * 10 * t_task + phase)
            data_task[ch] = base + np.random.normal(0, 0.15, n_task)

        for run, data, label in [
            (1, data_rest, "rest"),
            (2, data_rest, "rest"),
            (3, data_task, "task"),
            (4, data_task, "task"),
        ]:
            info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
            raw = RawArray(data, info)
            if set(ch_names).issubset(montage.ch_names):
                raw.set_montage(montage)
            path = os.path.join(output_dir, f"S{sub:03d}R{run:02d}_{label}.fif")
            raw.save(path, overwrite=True)
            print(f"[FALLBACK] Gespeichert: {path}")


if __name__ == "__main__":
    generate_local_bids_eeg()
