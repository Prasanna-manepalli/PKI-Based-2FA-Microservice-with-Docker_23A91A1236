# Build Secure PKI-Based 2FA Microservice with Docker

This project implements a complete Public-Key-Infrastructure based Two-Factor Authentication (2FA) system required for **Global Placement Program – Week 2**.

It includes:

- RSA key generation  
- RSA/OAEP decryption of instructor-generated seed  
- RSA-PSS commit proof signing  
- TOTP generation and verification  
- Docker container with FastAPI + Cron + UTC timezone  
- Automated cron logging of OTP every minute  
- Fully reproducible deterministic seed flow  

---

## 1. Repository Information

### GitHub Repository
```
https://github.com/Prasanna-manepalli/PKI-Based-2FA-Microservice-with-Docker_23A91A1236
```
This URL was also used for instructor API seed generation and final submission.

---

## 2. System Overview
This project securely generates a TOTP-based 2FA code using:
- An encrypted seed from instructor API
- RSA-4096 private key for decryption
- Deterministic seed stored in `/data/seed.txt`
- Base32 conversion for TOTP
- FastAPI service for endpoints
- Cron job for periodic OTP logging

---

## 3. Directory Structure
```
.
├── app/
│   ├── server.py
│   ├── crypto_utils.py
│   ├── totp_utils.py
│   └── generate_proof.py
│
├── cron/
│   └── totp_cron
│
├── scripts/
│   └── cron_job.py
│
├── student_private.pem
├── student_public.pem
├── instructor_public.pem
├── encrypted_signature.b64
├── encrypted_seed.txt
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitattributes
├── .gitignore
└── README.md
```

---

## 4. Cryptography Details

### 4.1 Key Pair
- RSA 4096 bits
- Public exponent 65537
- Stored as PEM files

### 4.2 Seed Decryption (RSA-OAEP-SHA256)
- Padding: OAEP
- MGF: MGF1(SHA-256)
- Hash: SHA-256
- Label: None

### 4.3 Commit Proof Signing (RSA-PSS-SHA256)
- PSS padding
- MGF1(SHA-256)
- Salt length: MAX
- Signed message: ASCII commit hash

---

## 5. TOTP System
- Algorithm: TOTP (RFC 6238)
- Hash: SHA-1
- Period: 30 seconds
- Digits: 6
- Seed: hex -> bytes -> base32 -> TOTP
- Verification window: ±1

---

## 6. API Endpoints

### Base URL
```
http://localhost:8080
```

### 6.1 POST /decrypt-seed
Decrypts instructor encrypted seed.

Request:
```json
{
  "encrypted_seed": "BASE64_STRING"
}
```
Response:
```json
{"status": "ok"}
```

### 6.2 GET /generate-2fa
Returns current OTP.

Response:
```json
{
  "code": "123456",
  "valid_for": 20
}
```

### 6.3 POST /verify-2fa
Verifies OTP.
```json
{"code": "123456"}
```
Response:
```json
{"valid": true}
```

---

## 7. Cron System
- File: `cron/totp_cron`
- Must use LF line endings
- Runs every 1 minute
- Executes `scripts/cron_job.py`
- Logs to `/cron/last_code.txt`

Example line:
```
2025-12-02 12:52:01 - 2FA Code: 430030
```

---

## 8. Docker Setup

### 8.1 Dockerfile
- Multi-stage build
- UTC timezone
- Cron installed
- Volumes: `/data`, `/cron`

### 8.2 Docker Compose
- Named volumes: `seed-data`, `cron-output`
- Maps port 8080

---

## 9. How to Run Locally

### Build
```bash
docker compose build
```

### Start
```bash
docker compose up -d
```

### Test seed decryption
```bash
curl -X POST http://localhost:8080/decrypt-seed \
  -H "Content-Type: application/json" \
  -d "{\"encrypted_seed\": \"$(cat encrypted_seed.txt)\"}"
```

### Generate OTP
```bash
curl http://localhost:8080/generate-2fa
```

### Verify OTP
```bash
CODE=$(curl -s http://localhost:8080/generate-2fa | jq -r '.code')
curl -X POST http://localhost:8080/verify-2fa \
  -H "Content-Type: application/json" \
  -d "{\"code\": \"$CODE\"}"
```

### Check cron output
```bash
docker compose exec app cat /cron/last_code.txt
```

---

## 10. Submission Information
- GitHub Repo URL
- Commit Hash
- Encrypted Seed
- Student Public Key
- Encrypted Signature (from encrypted_signature.b64)
- (Optional) Docker image link

---

## 11. Common Pitfalls
- Wrong padding (must use OAEP & PSS)
- Cron file using CRLF instead of LF
- Seed stored inside container instead of /data
- Seed not base32-encoded before TOTP
- Not using UTC
- Not allowing ±1 window
- Commit hash signed as binary instead of ASCII
- Encrypted signature copied with line breaks

---

## 12. Final Notes
This implementation fully satisfies the requirements for Week-2:
- PKI
- RSA Decryption
- RSA Signature & Proof
- TOTP Generation & Verification
- Docker Runtime
- Cron Automation