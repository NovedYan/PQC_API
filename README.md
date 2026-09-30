# PQC_API

ML-DSA-65 REST API with pluggable System RNG / PUF-derived randomness integration.

本專案使用 **Python、Django REST Framework 與 liboqs** 建立 ML-DSA-65 後量子數位簽章 API，並設計可切換的 Random Provider，使 ML-DSA 可以使用作業系統亂數，或由外部 PUF（Physical Unclonable Function）系統提供亂數來源。

---

# Project Architecture

```text
Client
  |
  v
Django REST API
  |
  v
MLDSAService
  |
  v
liboqs
  |
  +------------------------+
  |                        |
  v                        v
System RNG          Custom RNG Adapter
                           |
                           v
                    PUFRandomProvider
                           |
                           | HTTP REST API
                           v
                    PUF Random Server
                           |
                           v
                          PUF
```

---

# Current Status

目前已完成：

```text
[OK] Django REST API

[OK] ML-DSA-65 Key Generation
[OK] ML-DSA-65 Signing
[OK] ML-DSA-65 Verification

[OK] System RNG

[OK] Random Provider abstraction
[OK] HTTP PUF Random Provider
[OK] Mock PUF Server

[OK] liboqs Custom RNG Adapter

[OK] ML-DSA-65 KeyGen -> PUF RNG
[OK] ML-DSA-65 Sign -> PUF RNG

[OK] .env System / PUF switching
```

目前測試結果：

```text
Public key length: 1952 bytes
Secret key length: 4032 bytes
Signature length: 3309 bytes
Signature valid: True
```

---

# Quick Start

## 1. Create virtual environment

Windows：

```cmd
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

## 3. Create `.env`

複製：

```text
.env.example
```

成：

```text
.env
```

Example：

```env
DJANGO_SECRET_KEY=your-own-django-secret-key

PQC_RANDOM_MODE=system

PUF_ENDPOINT=http://127.0.0.1:9000/api/random/

PUF_TIMEOUT=5
```

Generate a Django secret key：

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

請不要把 `.env` commit 到 Git。

---

## 4. Django initialization

```bash
python manage.py migrate
python manage.py check
```

啟動：

```bash
python manage.py runserver
```

預設：

```text
http://127.0.0.1:8000/
```

---

# PQC REST API

## Status

```text
GET /api/pqc/status/
```

---

## ML-DSA-65 Key Generation

```text
POST /api/pqc/keygen/
```

Request：

```json
{}
```

Example response：

```json
{
  "algorithm": "ML-DSA-65",
  "public_key": "<Base64>",
  "secret_key": "<Base64>",
  "public_key_length": 1952,
  "secret_key_length": 4032
}
```

> 注意：目前 PoC 版本會直接回傳 Secret Key。正式部署應改為 Server-side secure storage，API 僅回傳 `key_id` 與 `public_key`。

---

## ML-DSA-65 Sign

```text
POST /api/pqc/sign/
```

Request：

```json
{
  "message": "Hello PQC",
  "secret_key": "<Base64 Secret Key>"
}
```

Example response：

```json
{
  "algorithm": "ML-DSA-65",
  "message": "Hello PQC",
  "signature": "<Base64 Signature>",
  "signature_length": 3309
}
```

---

## ML-DSA-65 Verify

```text
POST /api/pqc/verify/
```

Request：

```json
{
  "message": "Hello PQC",
  "signature": "<Base64 Signature>",
  "public_key": "<Base64 Public Key>"
}
```

Successful verification：

```json
{
  "algorithm": "ML-DSA-65",
  "message": "Hello PQC",
  "valid": true
}
```

若修改 message 而保持 Signature / Public Key 不變，預期：

```json
{
  "valid": false
}
```

---

# Randomness Mode

Random source 由 `.env` 控制。

## System RNG

```env
PQC_RANDOM_MODE=system
```

Architecture：

```text
ML-DSA-65
   |
   v
liboqs
   |
   v
System RNG
```

---

## PUF RNG

```env
PQC_RANDOM_MODE=puf

PUF_ENDPOINT=http://127.0.0.1:9000/api/random/

PUF_TIMEOUT=5
```

Architecture：

```text
ML-DSA-65
   |
   v
liboqs
   |
   v
Custom RNG Adapter
   |
   v
PUFRandomProvider
   |
   v
PUF REST API
```

---

# Mock PUF Server

開發與整合測試可使用：

```bash
python mock_puf_server.py
```

Default endpoint：

```text
http://127.0.0.1:9000/api/random/
```

目前 Mock PUF Server 使用：

```python
os.urandom()
```

它只用來模擬 PUF API 介面。

它**不是真正的 PUF 實作**，也不能代表 PUF entropy 或 cryptographic security 已被驗證。

---

# PUF Interface

外部 PUF 系統只需要實作：

```text
POST /api/random/
```

Request：

```json
{
  "length": 32
}
```

Response：

```json
{
  "random": "<Base64 encoded random bytes>",
  "length": 32
}
```

解碼後必須符合：

```text
len(Base64Decode(random)) == length
```

PUF Server 必須依 Request 的 `length` 回傳指定長度，不能把 32 bytes 寫死。

---

# PUF Interface Test

執行：

```bash
python test_puf_interface.py
```

Interface test 會檢查：

```text
16-byte request
32-byte request
64-byte request

HTTP status
JSON
Base64
Decoded byte length
Invalid input handling
```

Invalid examples：

```json
{
  "length": 0
}
```

```json
{
  "length": -1
}
```

```json
{
  "length": "32"
}
```

以上應回：

```text
HTTP 400
```

---

# ML-DSA + PUF Test

設定：

```env
PQC_RANDOM_MODE=puf
```

先啟動 PUF Server：

```bash
python mock_puf_server.py
```

再執行：

```bash
python test_mldsa.py
```

Expected：

```text
--- Key Generation ---
Public key length: 1952 bytes
Secret key length: 4032 bytes

--- Signing ---
Signature length: 3309 bytes

--- Verification ---
Signature valid: True
```

PUF Server 應顯示類似：

```text
[PUF REQUEST] Client requested 32 bytes
[PUF REQUEST] Client requested 32 bytes
```

目前實驗中，這兩筆分別對應 ML-DSA-65 的：

```text
KeyGen
Sign
```

---

# Integrating a Real PUF

PUF 團隊只需要提供：

```text
POST /api/random/
```

Request：

```json
{
  "length": N
}
```

Response：

```json
{
  "random": "<Base64 encoded N bytes>",
  "length": N
}
```

完成後，PQC 端只需修改 `.env`：

```env
PQC_RANDOM_MODE=puf

PUF_ENDPOINT=http://PUF_SERVER_IP:PORT/api/random/

PUF_TIMEOUT=5
```

不需要修改：

```text
MLDSAService
Django views
Django URLs
ML-DSA KeyGen
ML-DSA Sign
ML-DSA Verify
```

---

# Recommended PUF Internal Design

PUF 內部實作由 PUF 團隊決定，可能包含：

```text
Challenge
   |
   v
PUF
   |
   v
Raw Response
   |
   v
Error Correction
   |
   v
Fuzzy Extractor
   |
   v
Entropy Extraction
   |
   v
Seed
   |
   v
DRBG / Random Generation
   |
   v
N bytes
```

不應直接假設：

```text
Raw PUF Response
=
Cryptographically Secure Random Bytes
```

是否需要 Error Correction、Extractor、Hash、KDF 或 DRBG，應依實驗設計與安全需求決定。

---

# Important Research Boundary

通過：

```text
test_puf_interface.py
```

只代表：

```text
Interface Compatibility PASS
```

包括：

```text
HTTP
JSON
Base64
Byte Length
Error Handling
```

它不代表以下項目已驗證：

```text
Entropy
PUF uniqueness
PUF reliability
PUF unpredictability
Environmental robustness
Cryptographic security
```

---

# Failure Policy

當：

```env
PQC_RANDOM_MODE=puf
```

時，如果 PUF 發生：

```text
Connection refused
Timeout
Invalid JSON
Missing random
Missing length
Invalid Base64
Wrong byte length
```

PQC 端應讓 cryptographic operation 失敗。

不應自動：

```text
PUF Failure
   |
   v
System RNG
```

因為這會造成實驗結果與實際亂數來源不一致。

---

# Documentation

完整建置、安裝、測試與除錯指南：

```text
PQC_MLDSA_PUF_COMPLETE_GUIDE.md
```

PUF 專用介面規格：

```text
PUF_INTERFACE_SPEC.md
```

---

# Handoff to PUF Team

交接給 PUF 團隊時，至少提供：

```text
README.md
PUF_INTERFACE_SPEC.md
test_puf_interface.py
.env.example
```

建議一併提供：

```text
requirements.txt
test_mldsa.py
```

如果要直接聯調整套 PQC：

```text
config/
pqc/
manage.py
```

PUF Team 最小任務：

```text
1. 實作 POST /api/random/
2. 支援 length = N
3. 回傳 Base64 encoded N bytes
4. Invalid input 回 HTTP 400
5. 通過 test_puf_interface.py
6. 提供 IP / Port / Endpoint / 啟動方式
```

---

# Expected Final Result

最終成果：

```text
Real PUF
   |
   v
PUF Random Server
   |
   v
POST /api/random/
   |
   v
PUFRandomProvider
   |
   v
OQSRandomAdapter
   |
   v
liboqs
   |
   v
ML-DSA-65
   |
   +---- KeyGen
   |
   +---- Sign
   |
   +---- Verify
```

最終應可透過：

```env
PQC_RANDOM_MODE=system
```

與：

```env
PQC_RANDOM_MODE=puf
```

在**不修改 ML-DSA 核心程式碼**的情況下切換亂數來源。

---

# Final Validation Checklist

```text
[PASS] Django REST API 可啟動

[PASS] ML-DSA-65 KeyGen
[PASS] ML-DSA-65 Sign
[PASS] ML-DSA-65 Verify = True

[PASS] System RNG mode

[PASS] PUF Interface Test
[PASS] 16-byte request
[PASS] 32-byte request
[PASS] 64-byte request
[PASS] Invalid request -> HTTP 400

[PASS] PUF mode

[PASS] ML-DSA-65 KeyGen -> PUF
[PASS] ML-DSA-65 Sign -> PUF

[PASS] PUF Server 確實收到 ML-DSA random request
```

---

# Project Status

目前：

```text
Research / PoC
```

正式部署前仍應補強：

```text
HTTPS / TLS
Authentication
Authorization
Rate Limiting
Secure Private Key Storage
Key Lifecycle
Audit Logging
Error Sanitization
Replay Protection
Production WSGI / ASGI Deployment
PUF Server Authentication
```
