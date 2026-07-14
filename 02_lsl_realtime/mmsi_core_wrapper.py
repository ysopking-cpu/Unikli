# ==============================================================================
# MMSI v3.5 // PROPRIETARY CORE WRAPPER & DRM INTERFACE
# Pfad: /workspaces/Unikli/02_lsl_realtime/mmsi_core_wrapper.py
# ==============================================================================
import os
import sys
import ctypes
import numpy as np


class MMSICoreEngineWrapper:
    """Proprietäre Schnittstelle zur kompilierten Shared Library (Closed Source)."""
    def __init__(self, license_key: str):
        self._license_key = license_key
        self._lib_path = self._get_binary_path()
        self._engine = None
        self._verify_and_load()

    def _get_binary_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if sys.platform.startswith("linux"):
            return os.path.join(base_dir, "libmmsi_core.so")
        elif sys.platform == "win32":
            return os.path.join(base_dir, "mmsi_core.dll")
        else:
            raise OSError("Nicht unterstützte Ziel-Plattform.")

    def _verify_and_load(self):
        if not os.path.exists(self._lib_path):
            raise FileNotFoundError(
                f"[DRM-ERROR] Proprietäre Core-Engine '{self._lib_path}' nicht gefunden. "
                "Bitte kompilierte Binärdatei einfügen."
            )
        
        # Lade kompilierten C/C++-Binärkern
        self._engine = ctypes.CDLL(self._lib_path)
        
        # Cryptographic Handshake via C-Schnittstelle
        verify_func = self._engine.mmsi_verify_license
        verify_func.argtypes = [ctypes.c_char_p]
        verify_func.restype = ctypes.c_int
        
        status = verify_func(self._license_key.encode('utf-8'))
        if status != 1:
            raise PermissionError("[DRM-ERROR] Ungültiger oder abgelaufener Lizenzschlüssel.")

    def compute_d_alpha(self, cov_matrix: np.ndarray) -> float:
        """Aufruf der kompilierten C++ Eigenwert-Kontraktion."""
        cov_flat = cov_matrix.astype(np.float64).flatten()
        n_channels = cov_matrix.shape[0]
        
        calc_func = self._engine.mmsi_compute_d_alpha
        calc_func.argtypes = [
            ctypes.POINTER(ctypes.c_double), 
            ctypes.c_int
        ]
        calc_func.restype = ctypes.c_double
        
        c_arr = cov_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        return calc_func(c_arr, n_channels)
