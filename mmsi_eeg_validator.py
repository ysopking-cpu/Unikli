# ==============================================================================
# MMSI SYSTEM-OPERATOR // VALIDATION PIPELINE v3.5 (Standalone-Core)
# File: mmsi_eeg_validator.py
# Target IDE: VS Code // Language: Python 3
# ==============================================================================

import numpy as np
import mne
import matplotlib.pyplot as plt
from scipy.signal import hilbert

def generate_mmsi_synthetic_eeg(sfreq=250, duration=20, n_channels=32):
    """
    Generiert einen synthetischen EEG-Datenstrom zur Emulation der Phasenübergänge.
    Zeitintervall 0-10s: Verarbeitungsmodus T_V (hohe dimensionale Komplexität, d=3)
    Zeitintervall 10-20s: Seinsmodus T_S (Kollaps auf Kohärenz-Singularität, d=1)
    """
    n_samples = int(sfreq * duration)
    time = np.linspace(0, duration, n_samples)
    data = np.zeros((n_channels, n_samples))
    
    # Segment 1: T_V (0 bis 50% der Zeit) - Fragmentierte, unkorrelierte Oszillationen
    half_samples = n_samples // 2
    for i in range(n_channels):
        # Zufällige Frequenzen im Alpha/Beta-Band simulieren unkoordiniertes Phasenrauschen
        freq = np.random.uniform(8, 25)
        data[i, :half_samples] = np.sin(2 * np.pi * freq * time[:half_samples]) + np.random.normal(0, 0.5, half_samples)
        
    # Segment 2: T_S (50% bis 100% der Zeit) - Synchronisierter Alpha-Kollaps (Konnektivität)
    # Ein dominanter globaler Oszillator (10 Hz) übernimmt das System
    global_alpha = np.sin(2 * np.pi * 10 * time[half_samples:])
    for i in range(n_channels):
        # Kanäle koppeln sich phasenstarr an den globalen T_S-Vektor (+ Rauschen)
        phase_shift = np.random.uniform(-0.1, 0.1)
        data[i, half_samples:] = np.sin(2 * np.pi * 10 * time[half_samples:] + phase_shift) + np.random.normal(0, 0.2, n_samples - half_samples)
        
    # In MNE RawArray überführen
    ch_names = [f'EEG_{i:02d}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)
    return raw

def calculate_effective_dimension(window_data):
    """
    Berechnet die effektive Dimension d_alpha über das Eigenwertspektrum
    der räumlichen Kovarianzmatrix (MMSI v3.5 Axiom II).
    """
    # Räumliche Kovarianzmatrix berechnen
    cov_matrix = np.cov(window_data)
    
    # Eigenwerte extrahieren
    eigenvals = np.linalg.eigvalsh(cov_matrix)
    eigenvals = np.maximum(eigenvals, 0) # Numerische Negativwerte eliminieren
    
    if np.sum(eigenvals) == 0:
        return 0
        
    # MMSI v3.5 Formel: (Summe(lambda))^2 / Summe(lambda^2)
    sum_lambda = np.sum(eigenvals)
    sum_lambda_sq = np.sum(eigenvals**2)
    
    d_alpha = (sum_lambda**2) / sum_lambda_sq
    return d_alpha

def main():
    print("[SYSTEM] Initialisiere MMSI-EEG-Pipeline...")
    
    # 1. Datenbeschaffung / Generierung
    raw = generate_mmsi_synthetic_eeg(sfreq=250, duration=20, n_channels=32)
    
    # 2. Filterung (Alpha-Band-Isolierung zur Fokus-Analyse)
    print("[SYSTEM] Applikziere Bandpass-Filter (8 - 12 Hz)...")
    raw_filtered = raw.copy().filter(l_freq=8.0, h_freq=12.0, fir_design='firwin', verbose=False)
    
    # Daten-Arrays extrahieren
    data, times = raw_filtered.get_data(), raw_filtered.times
    sfreq = raw_filtered.info['sfreq']
    
    # 3. Gleitende Fensteranalyse (Sliding Window Trajectory)
    window_size = int(0.5 * sfreq) # 500ms Fenster
    step_size = int(0.1 * sfreq)   # 100ms Schrittweite
    
    d_alpha_trajectory = []
    time_axis = []
    
    print("[SYSTEM] Berechne kognitive Zustandsraum-Trajektorie...")
    for start in range(0, data.shape[1] - window_size, step_size):
        end = start + window_size
        window_data = data[:, start:end]
        
        # Effektive Dimension berechnen
        d_alpha = calculate_effective_dimension(window_data)
        d_alpha_trajectory.append(d_alpha)
        
        # Zentralen Zeitpunkt des Fensters speichern
        time_axis.append(times[start + window_size // 2])
        
    # 4. Visualisierung der Invarianten-Flugbahn
    print("[SYSTEM] Generiere Phasenraum-Plot...")
    plt.figure(figsize=(12, 6), facecolor='#f5f5f5')
    plt.plot(time_axis, d_alpha_trajectory, color='#1e3d59', linewidth=2.5, label=r'$d_{\alpha}(t)$ Trajektorie')
    
    # Modus-Grenzflächen einzeichnen
    plt.axhline(y=3.0, color='#ff6e40', linestyle='--', alpha=0.7, label='TV-Limit (Maximum Fragmentierung)')
    plt.axhline(y=1.0, color='#17b978', linestyle='--', alpha=0.7, label='TS-Limit (Singularität / Null-Last)')
    
    # Phasen-Zonen markieren
    plt.axvspan(0, 10, color='#ff6e40', alpha=0.1, label='Modus Tv (Verarbeitung)')
    plt.axvspan(10, 20, color='#17b978', alpha=0.1, label='Modus Ts (Sein / Kollaps)')
    
    plt.title('MMSI v3.5 // Geometrischer Dimensionskollaps $d_{\alpha}(t)$', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Physikalische Zeit (s)', fontsize=12)
    plt.ylabel('Effektive Dimension $d_{\alpha}$', fontsize=12)
    plt.ylim(0, 5)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='none')
    
    print("[SYSTEM] Pipeline-Lauf abgeschlossen. Zeige Graph.")
    plt.show()

if __name__ == "__main__":
    main()
