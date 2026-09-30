# PUF_INTERFACE_SPEC.md
## PUF Randomness Interface Specification for ML-DSA-65 Integration

> 文件用途：定義 **PUF 系統** 與 **PQC / ML-DSA-65 系統** 之間的正式介面。  
> 適用對象：負責 PUF、FPGA、MCU、嵌入式系統、亂數處理與 API 開發的人員。  
> 目標：PUF 團隊只需實作固定的 Randomness API，即可接入既有 ML-DSA 系統，不需要修改 Django、liboqs 或 ML-DSA 原始碼。

---

# 1. 介面目標

PQC 系統只要求 PUF 端提供一個功能：

```text
給定 length = N
回傳 exactly N bytes 的 PUF-derived random data
```

介面形式：

```text
POST /api/random/
```

整體架構：

```text
PQC / Django
    |
    v
MLDSAService
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
    | HTTP REST API
    v
PUF Random Server
    |
    v
PUF Hardware / PUF Software
```

PUF 團隊不需要處理：

```text
ML-DSA KeyGen
ML-DSA Sign
ML-DSA Verify
Public Key
Secret Key
Signature
Django
liboqs
```

---

# 2. Required Endpoint

PUF 系統必須提供：

```text
POST /api/random/
```

Content-Type：

```text
application/json
```

---

# 3. Request Format

Request Body：

```json
{
  "length": 32
}
```

## `length`

型態：

```text
integer
```

意義：

```text
要求 PUF Server 回傳多少 bytes 的 random data
```

範例：

```json
{
  "length": 32
}
```

代表：

```text
回傳 exactly 32 bytes
```

不是：

```text
32 characters
```

不是：

```text
32 bits
```

而是：

```text
32 bytes = 256 bits
```

---

# 4. Successful Response

成功時：

```text
HTTP 200 OK
```

Response：

```json
{
  "random": "<Base64 encoded random bytes>",
  "length": 32
}
```

---

# 5. `random` 欄位規格

`random` 必須是：

```text
Standard Base64
```

流程：

```text
PUF-derived random bytes
        |
        v
      N bytes
        |
        v
  Base64 Encode
        |
        v
 JSON string
```

Python 範例：

```python
import base64

raw_bytes = get_puf_random_bytes(32)

encoded = base64.b64encode(
    raw_bytes
).decode("utf-8")
```

Response：

```json
{
  "random": "Base64DataHere...",
  "length": 32
}
```

---

# 6. `length` 必須與實際 bytes 一致

如果 Request：

```json
{
  "length": 32
}
```

則必須滿足：

```text
response["length"] == 32
```

並且：

```text
len(Base64Decode(response["random"])) == 32
```

PQC 端會同時檢查：

```text
1. Response 裡的 length
2. Base64 Decode 後的真正 byte length
```

以下情況會被拒絕：

```json
{
  "random": "<Base64 of only 31 bytes>",
  "length": 32
}
```

---

# 7. Invalid Request Handling

以下輸入必須拒絕。

## Case 1：length = 0

Request：

```json
{
  "length": 0
}
```

Expected：

```text
HTTP 400 Bad Request
```

---

## Case 2：Negative length

```json
{
  "length": -1
}
```

Expected：

```text
HTTP 400 Bad Request
```

---

## Case 3：Non-integer

```json
{
  "length": "32"
}
```

Expected：

```text
HTTP 400 Bad Request
```

注意：

```json
32
```

與：

```json
"32"
```

不同。

前者：

```text
integer
```

後者：

```text
string
```

---

# 8. 建議錯誤格式

建議：

```json
{
  "error": "length must be greater than 0"
}
```

或：

```json
{
  "error": "length must be an integer"
}
```

HTTP Status：

```text
400 Bad Request
```

---

# 9. 不可將 32 bytes 寫死

目前 ML-DSA-65 實驗中已觀察：

```text
KeyGen -> 32-byte random request
Sign   -> 32-byte random request
```

但是 API 不可以寫成：

```python
def get_random():
    return fixed_32_bytes
```

正確應為：

```python
def get_random_bytes(
    length: int
) -> bytes:
    ...
```

原因：

```text
不同演算法可能需要不同長度
不同 liboqs 版本可能有不同需求
測試會要求 16 / 32 / 64 bytes
未來其他 PQC 演算法可能要求不同長度
```

所以必須支援：

```text
N bytes
```

---

# 10. PUF 端建議函式介面

建議在 PUF 專案內部統一成：

```python
def get_puf_random_bytes(
    length: int
) -> bytes:
    """
    Return exactly `length` bytes of
    PUF-derived random data.
    """
```

基本要求：

```python
data = get_puf_random_bytes(32)

assert isinstance(
    data,
    bytes
)

assert len(data) == 32
```

---

# 11. PUF 內部實作由 PUF 團隊負責

PQC 系統不限制：

```text
FPGA
MCU
Raspberry Pi
Linux
Windows
Python
C
C++
Rust
Go
Embedded System
```

只要求最終輸出符合：

```text
POST /api/random/
```

PUF 內部可以是：

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

---

# 12. Raw PUF Response 不應直接被視為安全亂數

PUF Raw Response 可能存在：

```text
Noise
Bias
Environmental variation
Reliability issue
Non-uniform distribution
Bit instability
```

因此不要直接假設：

```text
Raw PUF Response
=
Cryptographically Secure Random Bytes
```

是否需要：

```text
Error Correction
Fuzzy Extractor
Entropy Extraction
Hash
KDF
DRBG
```

由 PUF 團隊依研究設計決定。

PQC 端只接受：

```text
最終產生的 N bytes
```

---

# 13. PUF Server 參考實作

以下 FastAPI 範例只示範介面，不代表真正 PUF 實作。

```python
import base64

from fastapi import (
    FastAPI,
    HTTPException
)

from pydantic import BaseModel


app = FastAPI()


class RandomRequest(BaseModel):
    length: int


def get_puf_random_bytes(
    length: int
) -> bytes:

    # TODO:
    # 在這裡接真正的 PUF。
    raise NotImplementedError


@app.post("/api/random/")
def random_bytes(
    request: RandomRequest
):

    length = request.length

    if length <= 0:

        raise HTTPException(
            status_code=400,
            detail=
            "length must be greater than 0"
        )

    random_data = (
        get_puf_random_bytes(
            length
        )
    )

    if not isinstance(
        random_data,
        bytes
    ):

        raise HTTPException(
            status_code=500,
            detail=
            "PUF output must be bytes"
        )

    if len(random_data) != length:

        raise HTTPException(
            status_code=500,
            detail=
            "Incorrect PUF output length"
        )

    encoded = base64.b64encode(
        random_data
    ).decode("utf-8")

    return {
        "random": encoded,
        "length": len(random_data)
    }
```

---

# 14. 不要回傳 Hex String

錯誤：

```json
{
  "random": "9f86d081884c7d659a2feaa0c55ad015...",
  "length": 32
}
```

如果這只是 Hex 表示法，PQC Client 不會把它當作 32 raw bytes。

請使用：

```text
Base64
```

---

# 15. 不要回傳 Python bytes literal

錯誤：

```json
{
  "random": "b'\\x12\\x34\\x56...'",
  "length": 32
}
```

正確：

```json
{
  "random": "EjRW...",
  "length": 32
}
```

---

# 16. PUF Server 不需要知道 ML-DSA 內容

PUF API 不會收到：

```text
message
public_key
secret_key
signature
```

只會收到：

```json
{
  "length": N
}
```

然後回：

```json
{
  "random": "...",
  "length": N
}
```

---

# 17. PUF API 驗收測試

PQC 專案提供：

```text
test_puf_interface.py
```

PUF Server 完成後，設定 Endpoint：

```python
PUF_ENDPOINT = (
    "http://PUF_SERVER_IP:PORT/api/random/"
)
```

例如：

```python
PUF_ENDPOINT = (
    "http://192.168.1.100:9000/api/random/"
)
```

執行：

```bash
python test_puf_interface.py
```

---

# 18. 預期 PASS

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

# 19. PASS 的意義

代表：

```text
HTTP 正常
JSON 正常
Base64 正常
Byte Length 正常
Error Handling 正常
Interface 相容
```

不代表：

```text
Entropy 已驗證
PUF uniqueness 已驗證
PUF reliability 已驗證
PUF unpredictability 已驗證
PUF security 已驗證
```

也就是：

```text
Interface PASS
!=
Cryptographic Security PASS
```

---

# 20. PUF Server Failure Handling

以下情況 PQC 端會視為失敗：

```text
Server unreachable
Connection refused
Timeout
HTTP Status != 200
Invalid JSON
Missing random
Missing length
Invalid Base64
Wrong decoded byte length
```

PUF Mode 下：

```text
PUF Failure
   |
   v
Crypto Operation Failure
```

不應自動 fallback：

```text
PUF Failure
   |
   v
System RNG
```

因為這會造成實驗結果失真。

---

# 21. Timeout

PQC 預設：

```env
PUF_TIMEOUT=5
```

代表：

```text
最多等待 5 秒
```

如果硬體 PUF 較慢，可調整：

```env
PUF_TIMEOUT=10
```

---

# 22. Concurrency

未來可能同時有：

```text
KeyGen
Sign
```

若 PUF Hardware 只能一次處理一筆，可由 PUF Server 內部實作：

```text
HTTP Request
   |
   v
Queue
   |
   v
Lock / Mutex
   |
   v
PUF Hardware
```

PQC 端不需要理解硬體資源鎖定。

---

# 23. 建議 Server Log

建議至少：

```text
[PUF REQUEST] Client requested 32 bytes
```

可以額外記錄：

```text
timestamp
request id
latency
success
failure
```

不建議把：

```text
Raw PUF secret material
```

直接寫入 log。

---

# 24. PQC 端設定方式

資工系完成 PUF Server 後，PQC `.env`：

```env
PQC_RANDOM_MODE=puf

PUF_ENDPOINT=http://192.168.1.100:9000/api/random/

PUF_TIMEOUT=5
```

不需要修改：

```text
mldsa_service.py
views.py
urls.py
liboqs
```

---

# 25. 已驗證的 ML-DSA 整合行為

目前 PoC 已驗證：

```text
ML-DSA-65 KeyGen
   |
   v
liboqs Custom RNG
   |
   v
PUF API
   |
   v
32-byte request
```

以及：

```text
ML-DSA-65 Sign
   |
   v
liboqs Custom RNG
   |
   v
PUF API
   |
   v
32-byte request
```

Verify：

```text
不需要新的 random input
```

---

# 26. 真正聯調流程

## Step 1

資工系啟動 PUF Server。

例如：

```bash
python puf_server.py
```

---

## Step 2

PQC 端執行：

```bash
python test_puf_interface.py
```

全部 PASS。

---

## Step 3

設定：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://PUF_SERVER_IP:PORT/api/random/
PUF_TIMEOUT=5
```

---

## Step 4

執行：

```bash
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

## Step 5

PUF Server Log 應看到：

```text
[PUF REQUEST] Client requested 32 bytes
[PUF REQUEST] Client requested 32 bytes
```

目前分別對應：

```text
KeyGen
Sign
```

---

# 27. 最終驗收條件

```text
[PASS] PUF Server 可啟動
[PASS] POST /api/random/ 正常
[PASS] 16-byte request 正常
[PASS] 32-byte request 正常
[PASS] 64-byte request 正常
[PASS] Invalid length -> HTTP 400
[PASS] Standard Base64
[PASS] Decoded byte length 正確

[PASS] PQC_RANDOM_MODE=puf
[PASS] ML-DSA-65 KeyGen 成功
[PASS] ML-DSA-65 Sign 成功
[PASS] ML-DSA-65 Verify = True
[PASS] PUF Server 實際收到 ML-DSA Random Request
```

---

# 28. PUF 團隊最小交付內容

PUF 團隊需提供：

```text
1. PUF Random Server
2. IP
3. Port
4. API Path
5. 啟動方式
6. test_puf_interface.py PASS 結果
7. PUF Randomness Processing 說明
```

例如：

```text
IP:
192.168.1.100

Port:
9000

Endpoint:
/api/random/

Full URL:
http://192.168.1.100:9000/api/random/
```

---

# 29. PUF Randomness Processing 說明至少要包含

```text
Raw PUF Response 如何取得
是否有 Error Correction
是否有 Fuzzy Extractor
是否有 Entropy Extraction
是否經過 Hash / KDF
是否使用 DRBG
如何產生 N bytes
```

---

# 30. 雙方責任邊界

## PUF Team

負責：

```text
PUF Hardware
PUF Driver
Challenge / Response
Reliability
Error Correction
Entropy Processing
Random Byte Generation
REST API
```

## PQC Team

負責：

```text
Django
ML-DSA-65
liboqs
Custom RNG Adapter
PUF HTTP Client
KeyGen
Sign
Verify
```

---

# 31. 最終一句話

資工系 PUF 團隊只需要做到：

```text
給我 N
   |
   v
產生 N bytes 的 PUF-derived random data
   |
   v
Base64
   |
   v
POST /api/random/ Response
```

PQC 系統會負責：

```text
PUF-derived bytes
        |
        v
Custom RNG Adapter
        |
        v
liboqs
        |
        v
ML-DSA-65
```

---

# 32. 最終預期成果

真正完成後：

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
ML-DSA-65 KeyGen / Sign
   |
   v
Verify = True
```

而 PQC 端只需設定：

```env
PQC_RANDOM_MODE=puf
```

即可將：

```text
System RNG
```

切換成：

```text
PUF RNG
```

不需要修改 ML-DSA 核心程式碼。
