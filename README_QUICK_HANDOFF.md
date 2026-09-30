# PQC / ML-DSA-65 + PUF 快速交接 README

> 用途：讓接手的人在最短時間內知道「這個專案是什麼、怎麼跑、怎麼測、資工系 PUF 要怎麼接進來」。

---

# 1. 專案目標

本專案使用：

```text
Python
Django
Django REST Framework
liboqs-python
ML-DSA-65
```

建立 RESTful API，並支援兩種亂數來源：

```text
System RNG
PUF RNG
```

最終架構：

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
  +--------------------+
  |                    |
  v                    v
System RNG        PUF Random API
                       |
                       v
                      PUF
```

---

# 2. 已完成

目前 PoC 已完成：

```text
[OK] Django REST API
[OK] ML-DSA-65 KeyGen
[OK] ML-DSA-65 Sign
[OK] ML-DSA-65 Verify

[OK] System RNG
[OK] Random Provider abstraction
[OK] PUF HTTP Provider
[OK] Mock PUF Server
[OK] liboqs Custom RNG Adapter
[OK] ML-DSA-65 KeyGen -> PUF RNG
[OK] ML-DSA-65 Sign -> PUF RNG
[OK] .env system / puf 切換
```

目前實測：

```text
Public key length: 1952 bytes
Secret key length: 4032 bytes
Signature length: 3309 bytes
Signature valid: True
```

---

# 3. 專案主要檔案

```text
PQC_API/
│
├── manage.py
├── requirements.txt
├── .env
├── .env.example
│
├── config/
│
├── pqc/
│   ├── views.py
│   ├── urls.py
│   │
│   └── services/
│       ├── mldsa_service.py
│       │
│       └── random/
│           ├── base.py
│           ├── system_provider.py
│           ├── mock_puf_provider.py
│           ├── puf_provider.py
│           ├── oqs_adapter.py
│           └── manager.py
│
├── mock_puf_server.py
├── test_mldsa.py
├── test_puf_provider.py
├── test_puf_interface.py
├── test_oqs_puf_rng.py
└── test_mldsa_puf_keygen.py
```

---

# 4. Windows 快速啟動

## 4.1 建立虛擬環境

```cmd
cd /d C:\Users\onlyc\Projects\PQC_API

python -m venv .venv

.venv\Scripts\activate
```

---

## 4.2 安裝套件

```cmd
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

---

## 4.3 Windows native build 環境

需要：

```text
Git
CMake
Visual Studio Build Tools
Desktop development with C++
```

如果 CMD 找不到：

```text
cl
cmake
```

先執行：

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

再確認：

```cmd
git --version
cmake --version
cl
```

---

# 5. 確認 liboqs

```cmd
python -c "import oqs; print(oqs.oqs_python_version()); print(oqs.oqs_version())"
```

確認 ML-DSA-65：

```cmd
python -c "import oqs; print('ML-DSA-65' in oqs.get_enabled_sig_mechanisms())"
```

預期：

```text
True
```

---

# 6. Django 初始化

第一次：

```cmd
python manage.py migrate
```

檢查：

```cmd
python manage.py check
```

啟動：

```cmd
python manage.py runserver
```

預設：

```text
http://127.0.0.1:8000/
```

---

# 7. API

## Status

```text
GET /api/pqc/status/
```

---

## KeyGen

```text
POST /api/pqc/keygen/
```

Request：

```json
{}
```

Response 會包含：

```text
public_key
secret_key
```

Base64 格式。

---

## Sign

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

---

## Verify

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

成功：

```json
{
  "valid": true
}
```

---

# 8. 快速測 ML-DSA

```cmd
python test_mldsa.py
```

預期：

```text
--- Key Generation ---
Public key length: 1952 bytes
Secret key length: 4032 bytes

--- Signing ---
Signature length: 3309 bytes

--- Verification ---
Signature valid: True
```

---

# 9. System RNG / PUF RNG 切換

使用：

```text
.env
```

---

## System RNG

```env
PQC_RANDOM_MODE=system
```

---

## PUF RNG

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://127.0.0.1:9000/api/random/
PUF_TIMEOUT=5
```

未來真正資工系 PUF：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://資工系IP:PORT/api/random/
PUF_TIMEOUT=5
```

---

# 10. Mock PUF 測試

第一個 CMD：

```cmd
python mock_puf_server.py
```

預設：

```text
http://127.0.0.1:9000/api/random/
```

第二個 CMD：

```cmd
python test_mldsa.py
```

PUF Server 應看到：

```text
[PUF REQUEST] Client requested 32 bytes
[PUF REQUEST] Client requested 32 bytes
```

目前對應：

```text
KeyGen
Sign
```

---

# 11. 資工系要做什麼

資工系不需要修改：

```text
Django
ML-DSA
liboqs
views.py
mldsa_service.py
```

他們只要提供：

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
  "random": "<Base64 encoded bytes>",
  "length": 32
}
```

---

# 12. PUF API 必要規格

Request：

```json
{
  "length": N
}
```

必須回：

```text
exactly N bytes
```

再 Base64。

也就是：

```text
len(Base64Decode(random)) == N
```

---

# 13. 不合法輸入

以下都應：

```text
HTTP 400
```

例如：

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

---

# 14. 不要把 32 bytes 寫死

目前 ML-DSA-65 實測：

```text
KeyGen -> 32 bytes
Sign   -> 32 bytes
```

但 PUF API 必須支援：

```text
N bytes
```

例如：

```text
16
32
64
其他長度
```

---

# 15. PUF Interface 驗收

執行：

```cmd
python test_puf_interface.py
```

預期：

```text
[PASS] 16-byte request
[PASS] 32-byte request
[PASS] 32-byte request
[PASS] 64-byte request
[PASS] Repeated requests produce different output

[PASS] Reject invalid length: 0
[PASS] Reject invalid length: -1
[PASS] Reject invalid length: 32
```

---

# 16. 注意：PASS 不代表 PUF 已安全

上述測試只驗證：

```text
HTTP
JSON
Base64
Byte Length
Error Handling
```

不代表：

```text
Entropy
Uniqueness
Reliability
Unpredictability
PUF Security
```

都已通過。

---

# 17. PUF 端建議介面

資工系最好自己實作：

```python
def get_puf_random_bytes(
    length: int
) -> bytes:
    ...
```

要求：

```python
data = get_puf_random_bytes(32)

assert isinstance(data, bytes)

assert len(data) == 32
```

---

# 18. PUF Raw Response 不要直接當亂數

建議概念：

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
Entropy Extraction
   |
   v
Seed / DRBG
   |
   v
N bytes
```

是否需要：

```text
Fuzzy Extractor
Hash
KDF
DRBG
```

由 PUF 團隊自行決定。

---

# 19. 真正接資工系 PUF 的流程

## Step 1

資工系完成：

```text
POST /api/random/
```

---

## Step 2

跑：

```cmd
python test_puf_interface.py
```

全部 PASS。

---

## Step 3

資工系提供：

```text
IP
Port
Endpoint
啟動方式
```

例如：

```text
http://192.168.1.100:9000/api/random/
```

---

## Step 4

PQC `.env`：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://192.168.1.100:9000/api/random/
PUF_TIMEOUT=5
```

---

## Step 5

跑：

```cmd
python test_mldsa.py
```

---

## Step 6

確認：

```text
KeyGen success
Sign success
Verify = True
```

---

## Step 7

確認 PUF Server log：

```text
[PUF REQUEST] Client requested ...
```

---

# 20. 最終驗收

以下全部成功：

```text
[PASS] PUF Server 啟動
[PASS] POST /api/random/
[PASS] 16-byte request
[PASS] 32-byte request
[PASS] 64-byte request
[PASS] Invalid input -> HTTP 400
[PASS] Base64 正確
[PASS] Byte length 正確

[PASS] PQC_RANDOM_MODE=puf
[PASS] ML-DSA-65 KeyGen
[PASS] ML-DSA-65 Sign
[PASS] ML-DSA-65 Verify = True

[PASS] PUF Server 確實收到 ML-DSA random request
```

---

# 21. 最終預期成果

最後 demo：

```text
System RNG
   |
   v
ML-DSA-65
KeyGen / Sign / Verify
```

然後只改：

```env
PQC_RANDOM_MODE=puf
```

變成：

```text
Real PUF
   |
   v
PUF Random Server
   |
   v
HTTP API
   |
   v
liboqs Custom RNG
   |
   v
ML-DSA-65
   |
   v
KeyGen / Sign / Verify
```

而且：

```text
Signature valid: True
```

同時 PUF Server log 顯示：

```text
[PUF REQUEST] Client requested 32 bytes
```

---

# 22. 交接給資工系時最少給這些

```text
README_QUICK_HANDOFF.md
PUF_INTERFACE_SPEC.md
test_puf_interface.py
.env.example
```

如果要讓他們直接測完整整合，再給：

```text
requirements.txt
test_mldsa.py
pqc/
config/
manage.py
```

---

# 23. 一句話交接版

資工系只需要記住：

```text
你們提供：

POST /api/random/

輸入：
{
  "length": N
}

輸出：
{
  "random": "<Base64 encoded N bytes>",
  "length": N
}
```

讓：

```text
test_puf_interface.py
```

全部 PASS。

PQC 端會負責：

```text
PUF bytes
   |
   v
liboqs
   |
   v
ML-DSA-65
```

---

# 24. 更完整文件

如果需要完整安裝、設計、測試與除錯紀錄，請看：

```text
PQC_MLDSA_PUF_COMPLETE_GUIDE.md
```

如果只要看 PUF 介面：

```text
PUF_INTERFACE_SPEC.md
```
