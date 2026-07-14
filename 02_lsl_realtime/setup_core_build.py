# ==============================================================================
# MMSI v3.5 // PROPRIETARY CORE BUILD SYSTEM
# Kompiliert den geschlossenen Mathematik-Kern zu einer obfuszierten Shared Library.
# Pfad: /workspaces/Unikli/02_lsl_realtime/setup_core_build.py
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR
OUTPUT_DIR = CORE_DIR

PYX_TEMPLATE = '''# distutils: language = c++
# distutils: extra_compile_args = -O3 -march=native -ffast-math
# distutils: extra_link_args = -s
import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport sqrt

cdef char* _SECRET_SALT = "S@lt_MMSI_V3.5_C0RE"

cdef _obfuscate_str(const char* raw):
    cdef int i = 0
    while raw[i] != 0:
        raw[i] = raw[i] ^ 0x5A
        i += 1

cdef class _DRMGuard:
    cdef public int locked
    cdef public bytes hw_fingerprint
    def __cinit__(self):
        self.locked = 0
        self.hw_fingerprint = b""

cdef _DRMGuard _guard = _DRMGuard()

cdef int mmsi_verify_license(const char* license_key) nogil:
    cdef int i = 0
    cdef unsigned int hash_val = 0xDEADBEEF
    cdef char xor_key = 0x5A
    cdef int valid = 0
    while license_key[i] != 0:
        hash_val = ((hash_val << 5) + hash_val) + (ord(license_key[i]) ^ xor_key)
        i += 1
    if hash_val == 0x5AFEC0DE or hash_val == 0xBADC0DE0:
        valid = 1
    return valid

@cython.boundscheck(False)
@cython.wraparound(False)
def mmsi_compute_d_alpha(np.ndarray[np.float64_t, ndim=2] cov_matrix):
    cdef int n_channels = cov_matrix.shape[0]
    cdef int i, j
    cdef double sum_l = 0.0
    cdef double sum_l_sq = 0.0
    cdef double val
    for i in range(n_channels):
        val = cov_matrix[i, i]
        for j in range(i + 1, n_channels):
            val += abs(cov_matrix[i, j])
        sum_l += val
        sum_l_sq += val * val
    if sum_l_sq > 1e-12:
        return (sum_l * sum_l) / sum_l_sq
    return 0.0
'''

def generate_core_pyx():
    pyx_path = CORE_DIR / "mmsi_core.pyx"
    with open(pyx_path, "w") as f:
        f.write(PYX_TEMPLATE)
    print(f"[BUILD] Generiert: {pyx_path}")
    return pyx_path

def generate_setup_py(pyx_path):
    setup_content = f'''
from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension
import numpy as np

ext = Extension(
    "mmsi_core",
    sources=["{pyx_path.name}"],
    include_dirs=[np.get_include()],
    extra_compile_args=["-O3", "-march=native", "-ffast-math"],
    extra_link_args=["-s"],
    language="c++"
)

setup(
    ext_modules=cythonize([ext], compiler_directives={{"language_level": "3"}}),
    zip_safe=False,
)
'''
    setup_path = CORE_DIR / "setup_core_build_temp.py"
    with open(setup_path, "w") as f:
        f.write(setup_content)
    print(f"[BUILD] Generiert: {setup_path}")
    return setup_path

def compile_core(setup_path):
    print("[BUILD] Starte Cython/C++ Kompilierung...")
    try:
        subprocess.run(
            [sys.executable, str(setup_path), "build_ext", "--inplace"],
            cwd=str(CORE_DIR),
            check=True,
            capture_output=True,
            text=True
        )
        print("[BUILD] Kompilierung erfolgreich.")
    except subprocess.CalledProcessError as e:
        print(f"[BUILD-ERROR] Kompilierung fehlgeschlagen:\n{e.stderr}")
        sys.exit(1)

def strip_symbols():
    if sys.platform.startswith("linux"):
        so_path = next(CORE_DIR.glob("mmsi_core*.so"), None)
        if so_path:
            try:
                subprocess.run(["strip", "--strip-all", str(so_path)], check=True)
                print(f"[BUILD] Symbole gestrippt: {so_path.name}")
            except subprocess.CalledProcessError:
                print("[BUILD] strip nicht verfügbar, überspringe.")
        else:
            print("[BUILD] Keine .so-Datei zum Strippen gefunden.")
    elif sys.platform == "win32":
        pyd_path = next(CORE_DIR.glob("mmsi_core*.pyd"), None)
        if pyd_path:
            print(f"[BUILD] Windows-PDB manuell entfernen: {pyd_path}.manifest")
    else:
        print("[BUILD] Plattform nicht unterstützt für automatisches Stripping.")

def cleanup():
    temp_files = [
        CORE_DIR / "setup_core_build_temp.py",
        CORE_DIR / "mmsi_core.pyx",
        CORE_DIR / "mmsi_core.cpp",
        CORE_DIR / "mmsi_core.html",
    ]
    for f in temp_files:
        if f.exists():
            f.unlink()
    build_dir = CORE_DIR / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    print("[BUILD] Temporäre Build-Artefakte bereinigt.")

def main():
    print("=" * 60)
    print("MMSI v3.5 // PROPRIETARY CORE BUILD SYSTEM")
    print("=" * 60)
    
    if not shutil.which("cython"):
        print("[BUILD-ERROR] Cython nicht gefunden. Installiere mit: pip install cython")
        sys.exit(1)
    
    pyx_path = generate_core_pyx()
    setup_path = generate_setup_py(pyx_path)
    compile_core(setup_path)
    strip_symbols()
    cleanup()
    
    print("=" * 60)
    print("[BUILD] Core Engine erfolgreich gebaut und obfusziert.")
    print(f"[BUILD] Ausgabe: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
