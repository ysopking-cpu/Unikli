#!/bin/bash
# ==============================================================================
# MMSI v3.5 // UNIFIED DEPLOYMENT & VERIFICATION BOOTSTRAPPER (PRE-COMPILED)
# Pfad: /workspaces/Unikli/build_and_verify.sh
# ==============================================================================
set -e

WORKSPACE_DIR="/workspaces/Unikli"
REALTIME_DIR="$WORKSPACE_DIR/02_lsl_realtime"

echo "[DRM-BUILD] Installiere Environment-Abhängigkeiten..."
pip install --upgrade pip -q
pip install cryptography numpy scipy mne matplotlib pylsl -q

echo "[DRM-BUILD] Verifiziere Integrität des vorkompilierten Binärkerns..."
if [ ! -f "$REALTIME_DIR/libmmsi_core.so" ] && [ ! -f "$REALTIME_DIR/mmsi_core.pyd" ]; then
    echo "[DRM-ERROR] Kein vorkompilierter Binärkern (libmmsi_core.so/mmsi_core.pyd) vorhanden."
    exit 1
fi

echo "[DRM-BUILD] Generiere kryptographischen RSA-2048 Lizenzschlüssel..."
python3 "$REALTIME_DIR/mmsi_license_gen.py" --type COMMERCIAL --out "$REALTIME_DIR/prod_license.key"

echo "[DRM-BUILD] Starte Offline-Verifikation via Headless CLI-Streamer..."
export MMSI_LICENSE_PATH="$REALTIME_DIR/prod_license.key"
python3 "$REALTIME_DIR/mmsi_lsl_cli.py"

echo "================================================================================"
echo " MMSI v3.5 INTEGRATIONSTEST: ERFOLGREICH (Vorkompiliert & DRM-geschützt)"
echo "================================================================================"
