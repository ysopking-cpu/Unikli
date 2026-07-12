# ==============================================================================
# MMSI v3.5 // SHARED FALLBACK LOADER
# Auto-Detect: Nutzt lokale .fif-Dateien, wenn PhysioNet offline ist.
# ==============================================================================

import os
import glob
import mne


def load_eeg_subject(subject, data_dir="/workspaces/Unikli/data/physionet", runs=(1, 2, 3, 4)):
    """
    Lädt EEG-Daten für einen Probanden.
    1. Zuerst lokale .fif-Fallback-Dateien suchen (offline/offline-fallback).
    2. Falls nicht vorhanden, Online-Download via MNE PhysioNet versuchen.
    """
    subject_str = f"S{subject:03d}"
    fif_paths = []
    for run in runs:
        matches = glob.glob(os.path.join(data_dir, f"{subject_str}R{run:02d}_*.fif"))
        if not matches:
            matches = glob.glob(os.path.join(data_dir, f"{subject_str}R{run:02d}*.fif"))
        fif_paths.extend(matches)

    if fif_paths:
        print(f"[LOADER] Lade lokale .fif-Daten ({len(fif_paths)} Dateien)...")
        return mne.concatenate_raws([
            mne.io.read_raw_fif(p, preload=True, verbose=False) for p in fif_paths
        ])

    from mne.datasets import eegbci
    print("[LOADER] Lokale Daten nicht gefunden. Starte PhysioNet Online-Download...")
    files = eegbci.load_data(subjects=[subject], runs=list(runs), path=data_dir)
    return mne.concatenate_raws([
        mne.io.read_raw_edf(f, preload=True, verbose=False) for f in files
    ])
