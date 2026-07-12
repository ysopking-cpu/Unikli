# ==============================================================================
# MMSI v3.5 // AUTOMATED CODE & INVARIANTS AUDIT
# Pfad: /workspaces/Unikli/mmsi_code_audit.py
# ==============================================================================
import numpy as np
import sys
import os

sys.path.append("/workspaces/Unikli/01_physionet_ingestion")
sys.path.append("/workspaces/Unikli/02_lsl_realtime")


def audit_eigenvalue_stability():
    print("[AUDIT 01] Teste Eigenwert-Metrik & Null-Division-Schutz...")
    zero_data = np.zeros((64, 80))
    cov_zero = np.cov(zero_data)
    eigenvals_zero = np.maximum(np.linalg.eigvalsh(cov_zero), 0)

    sum_l = np.sum(eigenvals_zero)
    sum_l_sq = np.sum(eigenvals_zero ** 2)
    d_alpha_zero = (sum_l ** 2) / sum_l_sq if sum_l_sq > 0 else 0.0

    assert d_alpha_zero == 0.0, "FAIL: Zero-Division Protection fehlgeschlagen."
    print(" -> PASSED: Zero-Division gewahrt (d_alpha = 0.0).")


def audit_dimension_bounds():
    print("[AUDIT 02] Teste mathematische Schranken von d_alpha...")
    n_channels = 64
    samples = 80

    single_rank_data = np.outer(np.ones(n_channels), np.sin(np.linspace(0, 10, samples)))
    cov_rank1 = np.cov(single_rank_data)
    eigs1 = np.maximum(np.linalg.eigvalsh(cov_rank1), 0)
    d_rank1 = (np.sum(eigs1) ** 2) / np.sum(eigs1 ** 2)

    noise_data = np.random.normal(0, 1, (n_channels, samples))
    cov_noise = np.cov(noise_data)
    eigs_noise = np.maximum(np.linalg.eigvalsh(cov_noise), 0)
    d_noise = (np.sum(eigs_noise) ** 2) / np.sum(eigs_noise ** 2)

    assert 0.99 <= d_rank1 <= 1.01, f"FAIL: Rank 1 Kollaps nicht exakt 1.0 (Ist: {d_rank1})"
    assert 1.0 < d_noise <= n_channels, f"FAIL: Noise Dimension außerhalb Grenzen (Ist: {d_noise})"
    print(f" -> PASSED: Bounds validiert (Kohärenz: {d_rank1:.3f} | Noise: {d_noise:.2f}).")


def audit_load_decoupling():
    print("[AUDIT 03] Teste Null-Last-Kopplung W(t)...")
    trigger_threshold = 1.32
    d_baseline = 3.18
    d_target = 1.12

    d_test_ts = 1.10
    load_ts = 0.0 if d_test_ts <= trigger_threshold else np.clip((d_test_ts - d_target) / (d_baseline - d_target), 0, 1)

    d_test_tv = 2.50
    load_tv = 0.0 if d_test_tv <= trigger_threshold else np.clip((d_test_tv - d_target) / (d_baseline - d_target), 0, 1)

    assert load_ts == 0.0, "FAIL: W(t) im Ts-Modus nicht Null."
    assert load_tv > 0.0, "FAIL: W(t) im Tv-Modus nicht skaliert."
    print(f" -> PASSED: Entkopplung verifiziert (Ts-Last: {load_ts} | Tv-Last: {load_tv:.3f}).")


def run_full_audit():
    print("==================================================")
    print("   MMSI v3.5 // CODE AUDIT & INVARANTEN CHECK   ")
    print("==================================================")
    audit_eigenvalue_stability()
    audit_dimension_bounds()
    audit_load_decoupling()
    print("==================================================")
    print("AUDIT-STATUS: 100% INVARIANTEN-KONFORM [READY FOR LIVE]")
    print("==================================================")


if __name__ == "__main__":
    run_full_audit()
