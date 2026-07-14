# ==============================================================================
# MMSI v3.5 // REAL-TIME CLOSED-LOOP GUI (REAL EEG REPLAY STREAM)
# Pfad: /workspaces/Unikli/02_lsl_realtime/mmsi_lsl_gui.py
# ==============================================================================

import sys
import time
import numpy as np
from collections import deque
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import mne

try:
    from mmsi_core_wrapper import MMSICoreEngineWrapper
    HAS_CORE = True
except ImportError:
    HAS_CORE = False

try:
    from pylsl import StreamOutlet, StreamInfo
    HAS_LSL = True
except ImportError:
    HAS_LSL = False

try:
    from mmsi_fallback_loader import load_eeg_subject
    HAS_FALLBACK = True
except ImportError:
    HAS_FALLBACK = False


class MMSIRealEEGStreamer:
    """Streamt echte Open-Source PhysioNet-Daten oder lokale .fif-Fallback-Dateien."""
    def __init__(self, subject=1, runs=(1, 3)):
        if HAS_FALLBACK:
            raw = load_eeg_subject(subject, runs=runs)
        else:
            from mne.datasets import eegbci
            files = eegbci.load_data(subjects=[subject], runs=list(runs))
            raw = mne.io.read_raw_edf(files[0], preload=True, verbose=False)
        self.data = raw.get_data()
        self.sfreq = raw.info["sfreq"]
        self.n_channels = self.data.shape[0]
        self.current_idx = 0

    def get_next_sample(self):
        sample = self.data[:, self.current_idx]
        self.current_idx = (self.current_idx + 1) % self.data.shape[1]
        return sample


class MMSIRealTimeEngine:
    def __init__(self, n_channels=64, sfreq=160, window_duration=0.5):
        self.n_channels = n_channels
        self.sfreq = sfreq
        self.buffer_size = int(sfreq * window_duration)
        self.buffer = deque(maxlen=self.buffer_size)
        self.trigger_threshold = 1.32
        self.d_baseline = 3.18
        self.d_target = 1.12

        self.core_engine = None
        if HAS_CORE:
            try:
                self.core_engine = MMSICoreEngineWrapper(license_key="ACADEMIC-TEST-KEY")
            except Exception:
                self.core_engine = None

    def _compute_d_alpha_fallback(self, cov_matrix):
        eigenvals = np.maximum(np.linalg.eigvalsh(cov_matrix), 0)
        sum_l = np.sum(eigenvals)
        sum_l_sq = np.sum(eigenvals ** 2)
        return (sum_l ** 2) / sum_l_sq if sum_l_sq > 0 else 0.0

    def push_sample(self, sample):
        self.buffer.append(sample)

    def is_ready(self):
        return len(self.buffer) == self.buffer_size

    def compute_metrics(self):
        if not self.is_ready():
            return None, None, False

        data = np.array(self.buffer).T
        cov_matrix = np.cov(data)

        if self.core_engine is not None:
            d_alpha = self.core_engine.compute_d_alpha(cov_matrix)
        else:
            d_alpha = self._compute_d_alpha_fallback(cov_matrix)

        is_triggered = d_alpha <= self.trigger_threshold

        if is_triggered:
            load_w = 0.0
        else:
            load_w = np.clip((d_alpha - self.d_target) / (self.d_baseline - self.d_target), 0.0, 1.0)

        return d_alpha, load_w, is_triggered


class MMSIRealDashboard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MMSI v3.5 // Closed-Loop Real-EEG Streamer (PhysioNet)")
        self.resize(1050, 650)

        self.streamer = MMSIRealEEGStreamer()
        self.engine = MMSIRealTimeEngine(n_channels=self.streamer.n_channels, sfreq=self.streamer.sfreq)

        self.history_len = 250
        self.time_history = deque(maxlen=self.history_len)
        self.d_alpha_history = deque(maxlen=self.history_len)
        self.load_w_history = deque(maxlen=self.history_len)

        self.start_time = time.time()
        self.init_ui()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(int(1000 / self.streamer.sfreq))

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        pg.setConfigOption("background", "#0f172a")
        pg.setConfigOption("foreground", "#f8fafc")

        self.status_label = QtWidgets.QLabel("SYSTEM-STATUS: INITIALISIERE ECHTES PHYSIONET-STREAMING...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #38bdf8; padding: 4px;")
        layout.addWidget(self.status_label)

        self.plot_d = pg.PlotWidget(title="Effektive Raumdimension d_alpha(t) [PhysioNet Realdaten-Stream]")
        self.plot_d.showGrid(x=True, y=True, alpha=0.3)
        self.plot_d.setYRange(0.5, 5.0)
        self.curve_d = self.plot_d.plot(pen=pg.mkPen("#38bdf8", width=2))
        self.plot_d.addLine(y=1.32, pen=pg.mkPen("#4ade80", style=QtCore.Qt.DashLine, width=1.5), label="Ps-Trigger (1.32)")
        layout.addWidget(self.plot_d)

        self.plot_w = pg.PlotWidget(title="Systemische Last W(t) [Realdaten-Entkopplung]")
        self.plot_w.showGrid(x=True, y=True, alpha=0.3)
        self.plot_w.setYRange(-0.05, 1.1)
        self.curve_w = self.plot_w.plot(pen=pg.mkPen("#f43f5e", width=2))
        layout.addWidget(self.plot_w)

    def update_loop(self):
        sample = self.streamer.get_next_sample()
        self.engine.push_sample(sample)

        t_now = time.time() - self.start_time
        d_alpha, load_w, is_triggered = self.engine.compute_metrics()

        if d_alpha is not None:
            self.time_history.append(t_now)
            self.d_alpha_history.append(d_alpha)
            self.load_w_history.append(load_w)

            self.curve_d.setData(list(self.time_history), list(self.d_alpha_history))
            self.curve_w.setData(list(self.time_history), list(self.load_w_history))

            if is_triggered:
                self.status_label.setText(f"REAL-EEG STATUS: TS_SINGULARITY_ACTIVE (d_alpha = {d_alpha:.2f} | W = 0.00)")
                self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4ade80; padding: 4px;")
            else:
                self.status_label.setText(f"REAL-EEG STATUS: TV_PROCESSING_LOAD (d_alpha = {d_alpha:.2f} | W = {load_w:.2f})")
                self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f43f5e; padding: 4px;")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MMSIRealDashboard()
    window.show()
    sys.exit(app.exec_())
