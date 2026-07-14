# ==============================================================================
# MMSI v3.5 // CRYPTOGRAPHIC LICENSE GENERATOR
# RSA-2048 Signierung von Hardware-gebundenen Lizenzschlüsseln.
# Pfad: /workspaces/Unikli/02_lsl_realtime/mmsi_license_gen.py
# ==============================================================================
import os
import sys
import json
import base64
import hashlib
import uuid
import platform
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("[LICENSE] 'cryptography' nicht gefunden. Installiere mit: pip install cryptography")
    sys.exit(1)


BASE_DIR = Path(__file__).resolve().parent
KEY_DIR = BASE_DIR / ".mmsi_keys"

def get_hw_id():
    """Generiert einen Hardware-Fingerprint (HWID)."""
    try:
        mac = uuid.getnode()
        cpu = platform.processor() or platform.machine()
        host = platform.node()
        raw = f"{mac}|{cpu}|{host}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:32].upper()
    except Exception:
        return "UNKNOWN-HWID"

def generate_rsa_keys(key_size=2048):
    """Generiert RSA-Schlüsselpaar und speichert es im versteckten .mmsi_keys Verzeichnis."""
    KEY_DIR.mkdir(exist_ok=True)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    priv_path = KEY_DIR / "mmsi_private.pem"
    pub_path = KEY_DIR / "mmsi_public.pem"
    
    with open(priv_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    print(f"[LICENSE] RSA-{key_size} Schlüsselpaar generiert:")
    print(f"  Privat: {priv_path}")
    print(f"  Öffentlich: {pub_path}")
    return private_key, public_key

def sign_license(hw_id, expiry_days=30, license_type="ACADEMIC"):
    """Signiert einen Lizenzschlüssel für eine gegebene HWID."""
    priv_path = KEY_DIR / "mmsi_private.pem"
    if not priv_path.exists():
        private_key, _ = generate_rsa_keys()
    else:
        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
    
    expiry = (datetime.utcnow() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
    payload = {
        "hwid": hw_id,
        "exp": expiry,
        "type": license_type,
        "ver": "3.5",
        "iss": "UNIKLI-CORE"
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    license_obj = {
        "p": base64.b64encode(payload_bytes).decode("utf-8"),
        "s": base64.b64encode(signature).decode("utf-8")
    }
    license_key = base64.b64encode(json.dumps(license_obj).encode("utf-8")).decode("utf-8")
    return license_key

def verify_license(license_key, public_key=None):
    """Verifiziert einen Lizenzschlüssel gegen den öffentlichen Schlüssel."""
    if public_key is None:
        pub_path = KEY_DIR / "mmsi_public.pem"
        if not pub_path.exists():
            return False, "Kein öffentlicher Schlüssel gefunden."
        with open(pub_path, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
    
    try:
        decoded = base64.b64decode(license_key.encode("utf-8"))
        license_obj = json.loads(decoded)
        payload_bytes = base64.b64decode(license_obj["p"])
        signature = base64.b64decode(license_obj["s"])
        
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        payload = json.loads(payload_bytes)
        expiry = datetime.strptime(payload["exp"], "%Y-%m-%d")
        if datetime.utcnow() > expiry:
            return False, f"Lizenz abgelaufen am {payload['exp']}"
        
        return True, f"Gültige Lizenz ({payload['type']}) für HWID: {payload['hwid']}"
    except Exception as e:
        return False, f"Verifikation fehlgeschlagen: {e}"

def main():
    parser = argparse.ArgumentParser(description="MMSI v3.5 License Generator")
    parser.add_argument("command", choices=["generate-keys", "sign", "verify"], help="Operation")
    parser.add_argument("--type", default="ACADEMIC", help="License type (ACADEMIC|COMMERCIAL)")
    parser.add_argument("--out", help="Output file path for license key")
    parser.add_argument("--days", type=int, default=30, help="Validity days for sign")
    args = parser.parse_args()

    print("=" * 60)
    print("MMSI v3.5 // LICENSE GENERATOR")
    print("=" * 60)
    
    hw_id = get_hw_id()
    print(f"[LICENSE] HWID: {hw_id}")
    
    if args.command == "generate-keys":
        generate_rsa_keys()
    elif args.command == "sign":
        key = sign_license(hw_id, expiry_days=args.days, license_type=args.type)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                f.write(key)
            print(f"[LICENSE] Schlüssel gespeichert: {out_path}")
        else:
            print(f"[LICENSE] Schlüssel: {key}")
    elif args.command == "verify":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        valid, msg = verify_license(key)
        print(f"[LICENSE] {'GÜLTIG' if valid else 'UNGÜLTIG'}: {msg}")

if __name__ == "__main__":
    main()
