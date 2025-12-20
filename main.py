from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import os
import time
import pyotp

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

app = FastAPI()

DATA_DIR = "/data"
SEED_FILE = "/data/seed.txt")
PRIVATE_KEY_FILE = "student_private.pem"


class DecryptRequest(BaseModel):
    encrypted_seed: str

class VerifyRequest(BaseModel):
    code: str


@app.post("/decrypt-seed")
def decrypt_seed(request: DecryptRequest):
    try:
        # 1. Load private key
        with open(PRIVATE_KEY_FILE, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )

        # 2. Base64 decode encrypted seed
        encrypted_bytes = base64.b64decode(request.encrypted_seed)

        # 3. RSA OAEP SHA-256 decrypt
        decrypted_bytes = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        decrypted_seed = decrypted_bytes.decode("utf-8")

        # 4. Validate seed
        if len(decrypted_seed) != 64 or not all(c in "0123456789abcdef" for c in decrypted_seed):
            raise ValueError("Invalid seed format")

        # 5. Save seed
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SEED_FILE, "w") as f:
            f.write(decrypted_seed)

        return {"status": "ok"}

    except Exception:
        raise HTTPException(status_code=500, detail="Decryption failed")


@app.get("/generate-2fa")
def generate_2fa():
    try:
        # 1. Check if seed exists
        if not os.path.exists(SEED_FILE):
            raise HTTPException(status_code=500, detail="Seed not decrypted yet")

        # 2. Read hex seed
        with open(SEED_FILE, "r") as f:
            hex_seed = f.read().strip()

        # 3. Convert HEX → BYTES
        seed_bytes = bytes.fromhex(hex_seed)

        # 4. Convert BYTES → BASE32
        seed_base32 = base64.b32encode(seed_bytes).decode()

        # 5. Generate TOTP
        totp = pyotp.TOTP(seed_base32)
        code = totp.now()

        # 6. Calculate remaining validity
        valid_for = 30 - (int(time.time()) % 30)

        return {
            "code": code,
            "valid_for": valid_for
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Seed not decrypted yet")

@app.post("/verify-2fa")
def verify_2fa(request: VerifyRequest):
    try:
        # 1. Validate code
        if not request.code:
            raise HTTPException(status_code=400, detail="Missing code")

        # 2. Check if seed exists
        if not os.path.exists(SEED_FILE):
            raise HTTPException(status_code=500, detail="Seed not decrypted yet")

        # 3. Read hex seed
        with open(SEED_FILE, "r") as f:
            hex_seed = f.read().strip()

        # 4. Convert HEX → BYTES
        seed_bytes = bytes.fromhex(hex_seed)

        # 5. Convert BYTES → BASE32
        seed_base32 = base64.b32encode(seed_bytes).decode()

        # 6. Create TOTP object
        totp = pyotp.TOTP(seed_base32)

        # 7. Verify with ±1 time window (±30s)
        is_valid = totp.verify(request.code, valid_window=1)

        return {"valid": is_valid}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Seed not decrypted yet")
