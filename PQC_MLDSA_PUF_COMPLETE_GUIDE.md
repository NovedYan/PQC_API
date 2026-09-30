# PQC / ML-DSA-65 / PUF 完整建置、測試與交接指南

> 專案目標：以 **Python + Django REST Framework** 建立 ML-DSA-65 RESTful API，先使用系統亂數完成 KeyGen / Sign / Verify，再將 liboqs 的亂數來源抽象化，最後透過 HTTP REST API 接入由資工系提供的 **PUF-derived randomness**。  
> 本文件從「建立 Python 虛擬環境」開始，一路寫到「如何把 PUF 介面交給資工系、如何聯調、如何驗收」。  
> 目前定位：**Research / PoC**，不是正式上線版。

---

# 0. 最終要完成什麼

最後整個系統要長成：

```text
Client
  |
  v
Django REST Framework
  |
  v
MLDSAService
  |
  v
liboqs-python
  |
  v
liboqs
  |
  +-------------------------------+
  |                               |
  v                               v
System RNG                  Custom RNG Adapter
                                  |
                                  v
                           PUFRandomProvider
                                  |
                                  | HTTP REST API
                                  v
                           PUF Random Server
                                  |
                                  v
                       PUF-derived random bytes
```

PQC API：

```text
GET  /api/pqc/status/
POST /api/pqc/keygen/
POST /api/pqc/sign/
POST /api/pqc/verify/
```

PUF API：

```text
POST /api/random/
```

最終必須能做到：

```text
ML-DSA-65 KeyGen -> PUF RNG
ML-DSA-65 Sign   -> PUF RNG
ML-DSA-65 Verify -> True / False
```

並且在 PUF Server log 中可以直接看到 ML-DSA 需要亂數時確實有打到：

```text
[PUF REQUEST] Client requested 32 bytes
```

目前實驗已經觀察到：

```text
ML-DSA-65 KeyGen -> 32-byte random request
ML-DSA-65 Sign   -> 32-byte random request
```

注意：

> 不要把 PUF API 寫死成只能回 32 bytes。  
> 介面必須支援 `N bytes`，由 Request 的 `length` 決定。

---

# 1. 技術棧

目前使用：

```text
Python
Django
Django REST Framework
liboqs-python
liboqs
requests
python-dotenv
SQLite
```

PQC：

```text
ML-DSA-65
```

用途：

```text
Key Generation
Digital Signature
Signature Verification
```

亂數來源：

```text
System RNG
PUF RNG
```

---

# 2. 目前開發環境

本次 Windows PoC 使用：

```text
Windows
Python 3.10.x
Django 5.2.17
Django REST Framework 3.18.1
liboqs-python 0.16.0.1
liboqs 0.16.0
Git 2.55.0.windows.5
CMake 4.3.1-msvc1
MSVC 19.51.36260 x64
```

虛擬環境：

```text
.venv
```

專案路徑範例：

```text
C:\Users\onlyc\Projects\PQC_API
```

---

# 3. 完整專案結構

建議最後整理成：

```text
PQC_API/
│
├── .venv/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── PUF_INTERFACE_SPEC.md
├── PQC_MLDSA_PUF_COMPLETE_GUIDE.md
│
├── manage.py
├── db.sqlite3
│
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── pqc/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── mldsa_service.py
│       │
│       └── random/
│           ├── __init__.py
│           ├── base.py
│           ├── system_provider.py
│           ├── mock_puf_provider.py
│           ├── puf_provider.py
│           ├── oqs_adapter.py
│           └── manager.py
│
├── mock_puf_server.py
├── test_mldsa.py
├── test_random_provider.py
├── test_puf_provider.py
├── test_puf_interface.py
├── test_oqs_puf_rng.py
└── test_mldsa_puf_keygen.py
```

---

# 4. Windows：從零開始安裝

## 4.1 建立專案資料夾

```cmd
mkdir C:\Users\onlyc\Projects\PQC_API
cd /d C:\Users\onlyc\Projects\PQC_API
```

---

## 4.2 建立 Python 虛擬環境

```cmd
python -m venv .venv
```

如果使用的是 **Windows CMD**：

```cmd
.venv\Scripts\activate
```

成功後會看到：

```text
(.venv) C:\Users\onlyc\Projects\PQC_API>
```

注意：

PowerShell 才使用：

```powershell
.venv\Scripts\Activate.ps1
```

CMD 不要使用 `.ps1`。

---

## 4.3 確認虛擬環境

```cmd
where python
```

第一個路徑應該是：

```text
C:\Users\onlyc\Projects\PQC_API\.venv\Scripts\python.exe
```

再確認：

```cmd
python --version
python -m pip --version
```

---

# 5. 安裝 Django 與 Django REST Framework

```cmd
python -m pip install --upgrade pip
python -m pip install django
python -m pip install djangorestframework
```

確認：

```cmd
python -m django --version
python -m pip show djangorestframework
```

---

# 6. 建立 Django 專案

在：

```text
C:\Users\onlyc\Projects\PQC_API
```

執行：

```cmd
django-admin startproject config .
```

注意最後的：

```text
.
```

代表直接在目前資料夾建立專案。

---

## 6.1 啟動 Django 測試

```cmd
python manage.py runserver
```

開：

```text
http://127.0.0.1:8000/
```

看到 Django 安裝成功頁面即正常。

停止：

```text
Ctrl + C
```

---

# 7. 初始化資料庫

```cmd
python manage.py migrate
```

會建立：

```text
db.sqlite3
```

研究 PoC 階段使用 SQLite 足夠。

---

# 8. 建立 PQC App

```cmd
python manage.py startapp pqc
```

---

# 9. 註冊 Django REST Framework 與 PQC App

打開：

```text
config/settings.py
```

找到：

```python
INSTALLED_APPS = [
    ...
]
```

加入：

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',

    # Local
    'pqc',
]
```

檢查：

```cmd
python manage.py check
```

預期：

```text
System check identified no issues (0 silenced).
```

---

# 10. 建立第一個 Status API

`pqc/views.py`：

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def status(request):
    return Response({
        "status": "ok",
        "service": "PQC API",
        "algorithm": "ML-DSA-65"
    })
```

建立：

```text
pqc/urls.py
```

內容：

```python
from django.urls import path
from .views import status


urlpatterns = [
    path("status/", status, name="pqc-status"),
]
```

修改：

```text
config/urls.py
```

```python
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/pqc/", include("pqc.urls")),
]
```

測試：

```cmd
python manage.py runserver
```

開：

```text
http://127.0.0.1:8000/api/pqc/status/
```

預期：

```json
{
    "status": "ok",
    "service": "PQC API",
    "algorithm": "ML-DSA-65"
}
```

---

# 11. Windows：安裝 liboqs-python 前置工具

`liboqs-python` 是 Python wrapper，底層仍需要 native `liboqs`。

Windows 建議準備：

```text
Git
CMake
MSVC
Windows SDK
```

---

# 12. 安裝 Visual Studio Build Tools

下載：

```text
Visual Studio Build Tools
```

工作負載勾選：

```text
Desktop development with C++
```

至少確認：

```text
MSVC
Windows SDK
CMake tools for Windows
```

本次安裝位置：

```text
C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools
```

---

## 12.1 載入 MSVC x64 環境

普通 CMD 中執行：

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

成功時會看到：

```text
Environment initialized for: 'x64'
```

確認：

```cmd
cl
cmake --version
```

---

# 13. 安裝 Git

可用：

```cmd
winget install --id Git.Git -e --source winget
```

重新開 CMD 後：

```cmd
git --version
```

---

# 14. 每次需要 native build 時的 CMD 啟動順序

新開 CMD 後：

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

cd /d C:\Users\onlyc\Projects\PQC_API

.venv\Scripts\activate
```

確認：

```cmd
git --version
cmake --version
cl
```

---

# 15. 安裝 liboqs-python

```cmd
python -m pip install liboqs-python==0.16.0.1
```

確認：

```cmd
python -m pip show liboqs-python
```

第一次：

```cmd
python -c "import oqs; print('liboqs-python:', oqs.oqs_python_version()); print('liboqs:', oqs.oqs_version())"
```

可能會觸發：

```text
下載 liboqs
CMake
編譯
安裝 native library
```

本次環境最後看到：

```text
liboqs-python: 0.16.0.1
liboqs: 0.16.0
```

以及 native library：

```text
C:\Users\onlyc\_oqs\bin\oqs.dll
```

---

# 16. `liboqs-python faulthandler is disabled`

執行程式時可能看到：

```text
liboqs-python faulthandler is disabled
```

這不是 ML-DSA 失敗。

它只是 native crash debug 相關提示。

只要後續：

```text
KeyGen
Sign
Verify
```

正常即可。

---

# 17. 確認 ML-DSA-65

```cmd
python -c "import oqs; print('ML-DSA-65' in oqs.get_enabled_sig_mechanisms())"
```

預期：

```text
True
```

---

# 18. 第一支 ML-DSA 測試

建立：

```text
test_mldsa.py
```

最初可用：

```python
import oqs


ALGORITHM = "ML-DSA-65"
message = b"Hello ML-DSA-65"


with oqs.Signature(ALGORITHM) as signer:

    public_key = signer.generate_keypair()

    signature = signer.sign(message)

    print("Public key length:", len(public_key))
    print("Signature length:", len(signature))


with oqs.Signature(ALGORITHM) as verifier:

    is_valid = verifier.verify(
        message,
        signature,
        public_key
    )

    print("Signature valid:", is_valid)
```

預期：

```text
Public key length: 1952 bytes
Signature length: 3309 bytes
Signature valid: True
```

---

# 19. 把 ML-DSA 封裝成 Service

建立：

```text
pqc/services/mldsa_service.py
```

最終版本：

```python
import oqs

from .random.manager import RandomManager
from .random.oqs_adapter import OQSRandomAdapter


class MLDSAService:
    """
    ML-DSA-65 密碼服務。
    """

    ALGORITHM = "ML-DSA-65"


    @classmethod
    def _prepare_rng(cls):

        RandomManager.configure()

        OQSRandomAdapter.clear_error()


    @classmethod
    def _check_rng(cls):

        OQSRandomAdapter.raise_if_error()


    @classmethod
    def generate_keypair(cls):

        cls._prepare_rng()

        with oqs.Signature(
            cls.ALGORITHM
        ) as signer:

            public_key = signer.generate_keypair()

            secret_key = signer.export_secret_key()

        cls._check_rng()

        return public_key, secret_key


    @classmethod
    def sign(
        cls,
        message: bytes,
        secret_key: bytes
    ):

        cls._prepare_rng()

        with oqs.Signature(
            cls.ALGORITHM,
            secret_key=secret_key
        ) as signer:

            signature = signer.sign(
                message
            )

        cls._check_rng()

        return signature


    @classmethod
    def verify(
        cls,
        message: bytes,
        signature: bytes,
        public_key: bytes
    ):

        with oqs.Signature(
            cls.ALGORITHM
        ) as verifier:

            is_valid = verifier.verify(
                message,
                signature,
                public_key
            )

        return is_valid
```

---

# 20. MLDSAService 測試

`test_mldsa.py`：

```python
from pqc.services.mldsa_service import MLDSAService


message = b"Hello ML-DSA Service"


public_key, secret_key = MLDSAService.generate_keypair()

print("--- Key Generation ---")
print("Public key length:", len(public_key), "bytes")
print("Secret key length:", len(secret_key), "bytes")


signature = MLDSAService.sign(
    message,
    secret_key
)

print("\n--- Signing ---")
print("Signature length:", len(signature), "bytes")


is_valid = MLDSAService.verify(
    message,
    signature,
    public_key
)

print("\n--- Verification ---")
print("Signature valid:", is_valid)
```

預期：

```text
Public key length: 1952 bytes
Secret key length: 4032 bytes

Signature length: 3309 bytes

Signature valid: True
```

---

# 21. Django KeyGen / Sign / Verify API

`pqc/views.py` 可使用：

```python
import base64

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.mldsa_service import MLDSAService


@api_view(["GET"])
def status(request):

    return Response({
        "status": "ok",
        "service": "PQC API",
        "algorithm": "ML-DSA-65"
    })


@api_view(["POST"])
def keygen(request):

    public_key, secret_key = (
        MLDSAService.generate_keypair()
    )

    public_key_b64 = base64.b64encode(
        public_key
    ).decode("utf-8")

    secret_key_b64 = base64.b64encode(
        secret_key
    ).decode("utf-8")

    return Response({
        "algorithm": MLDSAService.ALGORITHM,
        "public_key": public_key_b64,
        "secret_key": secret_key_b64,
        "public_key_length": len(public_key),
        "secret_key_length": len(secret_key)
    })


@api_view(["POST"])
def sign(request):

    message = request.data.get("message")
    secret_key_b64 = request.data.get("secret_key")

    if message is None:
        return Response(
            {"error": "message is required"},
            status=400
        )

    if secret_key_b64 is None:
        return Response(
            {"error": "secret_key is required"},
            status=400
        )

    try:

        message_bytes = message.encode("utf-8")

    except Exception:

        return Response(
            {"error": "message must be a string"},
            status=400
        )

    try:

        secret_key = base64.b64decode(
            secret_key_b64,
            validate=True
        )

    except Exception:

        return Response(
            {"error": "secret_key is not valid Base64"},
            status=400
        )

    try:

        signature = MLDSAService.sign(
            message_bytes,
            secret_key
        )

    except Exception as error:

        return Response(
            {
                "error": "ML-DSA signing failed",
                "detail": str(error)
            },
            status=400
        )

    signature_b64 = base64.b64encode(
        signature
    ).decode("utf-8")

    return Response({
        "algorithm": MLDSAService.ALGORITHM,
        "message": message,
        "signature": signature_b64,
        "signature_length": len(signature)
    })


@api_view(["POST"])
def verify(request):

    message = request.data.get("message")
    signature_b64 = request.data.get("signature")
    public_key_b64 = request.data.get("public_key")

    if message is None:
        return Response(
            {"error": "message is required"},
            status=400
        )

    if signature_b64 is None:
        return Response(
            {"error": "signature is required"},
            status=400
        )

    if public_key_b64 is None:
        return Response(
            {"error": "public_key is required"},
            status=400
        )

    try:

        message_bytes = message.encode("utf-8")

    except Exception:

        return Response(
            {"error": "message must be a string"},
            status=400
        )

    try:

        signature = base64.b64decode(
            signature_b64,
            validate=True
        )

    except Exception:

        return Response(
            {"error": "signature is not valid Base64"},
            status=400
        )

    try:

        public_key = base64.b64decode(
            public_key_b64,
            validate=True
        )

    except Exception:

        return Response(
            {"error": "public_key is not valid Base64"},
            status=400
        )

    try:

        is_valid = MLDSAService.verify(
            message_bytes,
            signature,
            public_key
        )

    except Exception as error:

        return Response(
            {
                "error": "ML-DSA verification failed",
                "detail": str(error)
            },
            status=400
        )

    return Response({
        "algorithm": MLDSAService.ALGORITHM,
        "message": message,
        "valid": is_valid
    })
```

---

# 22. PQC URLs

`pqc/urls.py`：

```python
from django.urls import path

from .views import (
    status,
    keygen,
    sign,
    verify
)


urlpatterns = [

    path(
        "status/",
        status,
        name="pqc-status"
    ),

    path(
        "keygen/",
        keygen,
        name="pqc-keygen"
    ),

    path(
        "sign/",
        sign,
        name="pqc-sign"
    ),

    path(
        "verify/",
        verify,
        name="pqc-verify"
    ),

]
```

---

# 23. 測試 Django API

啟動：

```cmd
python manage.py runserver
```

---

## 23.1 Status

```text
GET http://127.0.0.1:8000/api/pqc/status/
```

---

## 23.2 KeyGen

```text
POST http://127.0.0.1:8000/api/pqc/keygen/
```

Body：

```json
{}
```

預期：

```json
{
    "algorithm": "ML-DSA-65",
    "public_key": "...",
    "secret_key": "...",
    "public_key_length": 1952,
    "secret_key_length": 4032
}
```

---

## 23.3 Sign

```text
POST http://127.0.0.1:8000/api/pqc/sign/
```

Body：

```json
{
    "message": "Hello PQC",
    "secret_key": "<KeyGen 回傳的 Base64 Secret Key>"
}
```

預期：

```json
{
    "algorithm": "ML-DSA-65",
    "message": "Hello PQC",
    "signature": "...",
    "signature_length": 3309
}
```

---

## 23.4 Verify

```text
POST http://127.0.0.1:8000/api/pqc/verify/
```

Body：

```json
{
    "message": "Hello PQC",
    "signature": "<Sign 回傳的 Base64 Signature>",
    "public_key": "<KeyGen 回傳的 Base64 Public Key>"
}
```

預期：

```json
{
    "algorithm": "ML-DSA-65",
    "message": "Hello PQC",
    "valid": true
}
```

---

# 24. Negative Verification Test

把：

```json
"message": "Hello PQC"
```

改成：

```json
"message": "Hello PQC!"
```

Signature / Public Key 不變。

預期：

```json
{
    "valid": false
}
```

這可以避免誤以為 API 只是固定回 `true`。

---

# 25. 為什麼需要 Base64

ML-DSA 的：

```text
Public Key
Secret Key
Signature
```

都是 binary bytes。

JSON 不適合直接存 raw bytes。

因此：

```text
bytes
  |
  v
Base64
  |
  v
JSON string
```

接收端：

```text
JSON string
  |
  v
Base64 Decode
  |
  v
bytes
```

不要用：

```python
str(binary_data)
```

取代 Base64。

---

# 26. 建立 Random Provider 抽象層

建立：

```text
pqc/services/random/
```

目的：

```text
ML-DSA 不直接依賴 PUF
PUF 不直接依賴 ML-DSA
```

---

# 27. `base.py`

```python
from abc import ABC, abstractmethod


class RandomProvider(ABC):

    @abstractmethod
    def get_random_bytes(
        self,
        length: int
    ) -> bytes:

        pass
```

統一介面：

```python
get_random_bytes(length: int) -> bytes
```

---

# 28. `system_provider.py`

```python
import os

from .base import RandomProvider


class SystemRandomProvider(RandomProvider):

    def get_random_bytes(
        self,
        length: int
    ) -> bytes:

        if length <= 0:
            raise ValueError(
                "length must be greater than 0"
            )

        return os.urandom(length)
```

---

# 29. `mock_puf_provider.py`

```python
import os

from .base import RandomProvider


class MockPUFRandomProvider(RandomProvider):
    """
    注意：
    這不是真正的 PUF。
    只是用 os.urandom 模擬 PUF interface。
    """

    def get_random_bytes(
        self,
        length: int
    ) -> bytes:

        if length <= 0:
            raise ValueError(
                "length must be greater than 0"
            )

        return os.urandom(length)
```

---

# 30. 測試 Provider

`test_random_provider.py`：

```python
from pqc.services.random.system_provider import (
    SystemRandomProvider
)

from pqc.services.random.mock_puf_provider import (
    MockPUFRandomProvider
)


system_rng = SystemRandomProvider()

system_random = (
    system_rng.get_random_bytes(32)
)


mock_puf_rng = MockPUFRandomProvider()

mock_puf_random = (
    mock_puf_rng.get_random_bytes(32)
)


print(
    "System RNG length correct:",
    len(system_random) == 32
)

print(
    "Mock PUF RNG length correct:",
    len(mock_puf_random) == 32
)

print(
    "Two outputs are different:",
    system_random != mock_puf_random
)
```

預期：

```text
System RNG length correct: True
Mock PUF RNG length correct: True
Two outputs are different: True
```

注意：

> `Two outputs are different` 只是 basic sanity check。  
> 它不能證明 entropy quality。

---

# 31. 安裝 HTTP Client

```cmd
python -m pip install requests
```

---

# 32. `puf_provider.py`

```python
import base64

import requests

from .base import RandomProvider


class PUFRandomProvider(RandomProvider):

    def __init__(
        self,
        endpoint: str,
        timeout: int = 5
    ):

        self.endpoint = endpoint
        self.timeout = timeout


    def get_random_bytes(
        self,
        length: int
    ) -> bytes:

        if length <= 0:
            raise ValueError(
                "length must be greater than 0"
            )

        payload = {
            "length": length
        }

        try:

            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout
            )

        except requests.RequestException as error:

            raise RuntimeError(
                f"Unable to connect to PUF service: {error}"
            )

        if response.status_code != 200:

            raise RuntimeError(
                "PUF service returned "
                f"HTTP {response.status_code}"
            )

        try:

            data = response.json()

        except ValueError:

            raise RuntimeError(
                "PUF service did not return valid JSON"
            )

        if "random" not in data:

            raise RuntimeError(
                "PUF response missing 'random'"
            )

        if "length" not in data:

            raise RuntimeError(
                "PUF response missing 'length'"
            )

        if data["length"] != length:

            raise RuntimeError(
                "PUF returned incorrect length value"
            )

        try:

            random_bytes = base64.b64decode(
                data["random"],
                validate=True
            )

        except Exception:

            raise RuntimeError(
                "PUF random data is not valid Base64"
            )

        if len(random_bytes) != length:

            raise RuntimeError(
                "PUF returned incorrect number of bytes"
            )

        return random_bytes
```

---

# 33. PUF HTTP API Contract

資工系最後要提供：

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

必要條件：

```text
Base64Decode(random) 的長度 == length
```

---

# 34. Mock PUF Server

建立：

```text
mock_puf_server.py
```

```python
from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer
)

import json
import base64
import os


class MockPUFHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        if self.path != "/api/random/":

            self.send_error(
                404,
                "API endpoint not found"
            )

            return

        content_length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        request_body = self.rfile.read(
            content_length
        )

        try:

            request_data = json.loads(
                request_body.decode("utf-8")
            )

        except Exception:

            self.send_json(
                {"error": "Invalid JSON"},
                status=400
            )

            return

        length = request_data.get(
            "length"
        )

        if not isinstance(length, int):

            self.send_json(
                {
                    "error":
                    "length must be an integer"
                },
                status=400
            )

            return

        if length <= 0:

            self.send_json(
                {
                    "error":
                    "length must be greater than 0"
                },
                status=400
            )

            return

        print(
            f"[PUF REQUEST] "
            f"Client requested {length} bytes"
        )

        # Mock only
        random_bytes = os.urandom(
            length
        )

        random_b64 = base64.b64encode(
            random_bytes
        ).decode("utf-8")

        self.send_json(
            {
                "random": random_b64,
                "length": len(random_bytes)
            },
            status=200
        )


    def send_json(
        self,
        data,
        status=200
    ):

        response_body = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response_body))
        )

        self.end_headers()

        self.wfile.write(
            response_body
        )


if __name__ == "__main__":

    HOST = "127.0.0.1"
    PORT = 9000

    server = HTTPServer(
        (HOST, PORT),
        MockPUFHandler
    )

    print("============================")
    print("Mock PUF Server")
    print("============================")

    print(
        f"Running at: "
        f"http://{HOST}:{PORT}/api/random/"
    )

    print("Press Ctrl+C to stop.")

    server.serve_forever()
```

---

# 35. 啟動 Mock PUF Server

新開 CMD：

```cmd
cd /d C:\Users\onlyc\Projects\PQC_API
.venv\Scripts\activate
python mock_puf_server.py
```

保持視窗不要關。

---

# 36. 測試 PUF Provider

`test_puf_provider.py`：

```python
from pqc.services.random.puf_provider import (
    PUFRandomProvider
)


provider = PUFRandomProvider(
    endpoint=
    "http://127.0.0.1:9000/api/random/"
)


random_32 = (
    provider.get_random_bytes(32)
)

print(
    "Received:",
    len(random_32),
    "bytes"
)


random_64 = (
    provider.get_random_bytes(64)
)

print(
    "Received:",
    len(random_64),
    "bytes"
)


print(
    "32-byte request correct:",
    len(random_32) == 32
)

print(
    "64-byte request correct:",
    len(random_64) == 64
)
```

---

# 37. 建立 PUF Interface Compliance Test

這是之後直接交給資工系的驗收工具。

`test_puf_interface.py` 的目的：

```text
測試 Server Reachability
測試 JSON
測試 Base64
測試 byte length
測試錯誤處理
測試 16 / 32 / 64 bytes
```

驗收預期：

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

注意：

```text
Interface PASS
```

不代表：

```text
PUF entropy / security PASS
```

---

# 38. liboqs Custom RNG Adapter

真正將 PUF 導入 ML-DSA 的核心是：

```text
OQS_randombytes_custom_algorithm()
```

建立：

```text
pqc/services/random/oqs_adapter.py
```

```python
import ctypes as ct
import threading
import oqs

from .base import RandomProvider


OQS_RANDOM_CALLBACK = ct.CFUNCTYPE(
    None,
    ct.POINTER(ct.c_uint8),
    ct.c_size_t
)


class OQSRandomAdapter:

    _callback = None
    _provider = None
    _thread_state = threading.local()


    @classmethod
    def install(
        cls,
        provider: RandomProvider
    ):

        cls._provider = provider

        cls.clear_error()


        @OQS_RANDOM_CALLBACK
        def random_callback(
            output_buffer,
            bytes_to_read
        ):

            try:

                length = int(
                    bytes_to_read
                )

                random_data = (
                    cls._provider
                    .get_random_bytes(
                        length
                    )
                )

                if len(random_data) != length:

                    raise RuntimeError(
                        "Random provider returned "
                        "incorrect number of bytes"
                    )

                ct.memmove(
                    output_buffer,
                    random_data,
                    length
                )

            except Exception as error:

                cls._thread_state.error = (
                    error
                )

                ct.memset(
                    output_buffer,
                    0,
                    int(bytes_to_read)
                )


        cls._callback = (
            random_callback
        )

        native = oqs.native()

        native.OQS_randombytes_custom_algorithm.argtypes = [
            OQS_RANDOM_CALLBACK
        ]

        native.OQS_randombytes_custom_algorithm.restype = (
            None
        )

        native.OQS_randombytes_custom_algorithm(
            cls._callback
        )


    @classmethod
    def clear_error(cls):

        cls._thread_state.error = (
            None
        )


    @classmethod
    def raise_if_error(cls):

        error = getattr(
            cls._thread_state,
            "error",
            None
        )

        if error is not None:

            cls._thread_state.error = (
                None
            )

            raise RuntimeError(
                f"Custom RNG failed: {error}"
            )
```

---

# 39. 為什麼 PUF 失敗不能偷偷 fallback

如果設定：

```text
PQC_RANDOM_MODE=puf
```

但 PUF Server 掛掉：

```text
PUF timeout
PUF connection refused
Invalid Base64
Wrong byte length
```

不能：

```text
自動改用 System RNG
```

否則會出現：

```text
實驗名義：PUF + ML-DSA
實際執行：System RNG + ML-DSA
```

導致研究結果失真。

正確：

```text
PUF Failure
  |
  v
Crypto Operation Failure
```

---

# 40. 測試 liboqs 是否真的走 PUF

建立：

```text
test_oqs_puf_rng.py
```

核心流程：

```text
liboqs randombytes()
   |
   v
Custom callback
   |
   v
PUFRandomProvider
   |
   v
Mock PUF Server
```

測試成功時：

```text
Length correct: True
Outputs different: True
```

---

# 41. 測試 ML-DSA KeyGen 是否真的走 PUF

建立：

```text
test_mldsa_puf_keygen.py
```

流程：

```text
ML-DSA-65 KeyGen
     |
     v
liboqs
     |
     v
Custom RNG
     |
     v
PUF HTTP API
```

成功時：

```text
Public key length: 1952 bytes
Secret key length: 4032 bytes
```

同時 Mock PUF Server 應看到：

```text
[PUF REQUEST] Client requested 32 bytes
```

---

# 42. 建立 RandomManager

建立：

```text
pqc/services/random/manager.py
```

```python
import os

from dotenv import load_dotenv

from oqs.rand import (
    randombytes_switch_algorithm
)

from .puf_provider import (
    PUFRandomProvider
)

from .oqs_adapter import (
    OQSRandomAdapter
)


load_dotenv()


class RandomManager:

    _configured = False
    _mode = None


    @classmethod
    def configure(cls):

        if cls._configured:
            return

        mode = os.getenv(
            "PQC_RANDOM_MODE",
            "system"
        ).lower()


        if mode == "system":

            randombytes_switch_algorithm(
                "system"
            )

            cls._mode = "system"


        elif mode == "puf":

            endpoint = os.getenv(
                "PUF_ENDPOINT",
                "http://127.0.0.1:9000/api/random/"
            )

            timeout = int(
                os.getenv(
                    "PUF_TIMEOUT",
                    "5"
                )
            )

            provider = (
                PUFRandomProvider(
                    endpoint=endpoint,
                    timeout=timeout
                )
            )

            OQSRandomAdapter.install(
                provider
            )

            cls._mode = "puf"


        else:

            raise ValueError(
                "Invalid PQC_RANDOM_MODE. "
                "Allowed values are "
                "'system' or 'puf'."
            )

        cls._configured = True


    @classmethod
    def get_mode(cls):

        return cls._mode
```

---

# 43. 安裝 python-dotenv

```cmd
python -m pip install python-dotenv
```

---

# 44. `.env`

建立：

```text
.env
```

測試 PUF 模式：

```env
PQC_RANDOM_MODE=puf

PUF_ENDPOINT=http://127.0.0.1:9000/api/random/

PUF_TIMEOUT=5
```

System 模式：

```env
PQC_RANDOM_MODE=system
```

---

# 45. `.env.example`

提交給別人的是：

```text
.env.example
```

內容：

```env
# system / puf
PQC_RANDOM_MODE=system

# Only used in puf mode
PUF_ENDPOINT=http://127.0.0.1:9000/api/random/

# seconds
PUF_TIMEOUT=5
```

對方：

```text
複製 .env.example
變成 .env
```

再改 IP。

---

# 46. `.gitignore`

建議：

```gitignore
# Python
__pycache__/
*.pyc

# Virtual environment
.venv/

# Local environment config
.env

# Django local database
db.sqlite3

# OS / IDE
.DS_Store
Thumbs.db
.vscode/
```

要保留：

```text
.env.example
requirements.txt
PUF_INTERFACE_SPEC.md
PQC_MLDSA_PUF_COMPLETE_GUIDE.md
```

---

# 47. requirements.txt

建立：

```cmd
python -m pip freeze > requirements.txt
```

目前實際內容：

```text
asgiref==3.12.1
certifi==2026.7.22
charset-normalizer==3.5.1
Django==5.2.17
djangorestframework==3.18.1
idna==3.20
liboqs-python==0.16.0.1
python-dotenv==1.2.3
requests==2.34.2
sqlparse==0.6.0
tomli==2.4.1
typing_extensions==4.16.0
tzdata==2026.4
urllib3==2.8.0
```

---

# 48. 完整 System RNG 測試

`.env`：

```env
PQC_RANDOM_MODE=system
```

執行：

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

# 49. 完整 PUF RNG 測試

第一個 CMD：

```cmd
cd /d C:\Users\onlyc\Projects\PQC_API
.venv\Scripts\activate
python mock_puf_server.py
```

`.env`：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://127.0.0.1:9000/api/random/
PUF_TIMEOUT=5
```

第二個 CMD：

```cmd
cd /d C:\Users\onlyc\Projects\PQC_API
.venv\Scripts\activate
python test_mldsa.py
```

預期 ML-DSA：

```text
Public key length: 1952 bytes
Secret key length: 4032 bytes

Signature length: 3309 bytes

Signature valid: True
```

預期 PUF Server：

```text
[PUF REQUEST] Client requested 32 bytes
[PUF REQUEST] Client requested 32 bytes
```

目前兩筆分別可對應：

```text
KeyGen
Sign
```

---

# 50. Django + PUF 模式

先啟動 PUF Server：

```cmd
python mock_puf_server.py
```

另一個 CMD：

```cmd
python manage.py runserver
```

然後照順序：

```text
POST /api/pqc/keygen/
POST /api/pqc/sign/
POST /api/pqc/verify/
```

Verify 應回：

```json
{
    "valid": true
}
```

PUF Server 應收到 Random Request。

---

# 51. 換成真正資工系 PUF 時，PQC 端要改什麼

理想答案：

```text
幾乎不用改程式。
```

只改：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://資工系IP:PORT/api/random/
PUF_TIMEOUT=5
```

例如：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://192.168.1.100:9000/api/random/
PUF_TIMEOUT=5
```

---

# 52. 資工系到底需要做什麼

資工系不要碰：

```text
Django
ML-DSA
liboqs
mldsa_service.py
views.py
urls.py
Secret Key
Signature
```

只做：

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

---

# 53. 資工系 PUF 端建議抽象

建議他們自己也定義：

```python
def get_puf_random_bytes(
    length: int
) -> bytes:
    ...
```

要求：

```python
data = get_puf_random_bytes(32)

assert isinstance(
    data,
    bytes
)

assert len(data) == 32
```

---

# 54. PUF Raw Response 不等於 CSPRNG

這是最重要的研究邊界之一。

不要直接假設：

```text
PUF Raw Response
=
Cryptographically Secure Random Bytes
```

PUF 原始輸出可能存在：

```text
Noise
Bias
Environmental variation
Reliability issue
Non-uniform distribution
```

因此 PUF 團隊應自行決定是否加入：

```text
Error Correction
Fuzzy Extractor
Entropy Extraction
Hash
KDF
DRBG
```

可能架構：

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
DRBG
   |
   v
N bytes
```

PQC 端只接受最後：

```text
N bytes
```

---

# 55. PUF API 不可寫死 32 bytes

雖然目前 ML-DSA-65 實驗觀察到：

```text
KeyGen -> 32 bytes
Sign   -> 32 bytes
```

但 API 應支援：

```text
16 bytes
32 bytes
64 bytes
N bytes
```

所以：

```json
{
    "length": 64
}
```

必須回：

```text
exactly 64 bytes
```

---

# 56. PUF Interface 驗收規格

至少測：

```text
16-byte request
32-byte request
64-byte request
```

以及：

```text
length = 0
length = -1
length = "32"
```

不合法輸入：

```text
HTTP 400
```

---

# 57. PUF API 錯誤情況

以下都應視為失敗：

```text
Server unreachable
Connection refused
Timeout
HTTP != 200
Invalid JSON
Missing random
Missing length
Invalid Base64
Wrong byte length
```

---

# 58. PUF Server Concurrency

Django 未來可能同時有：

```text
KeyGen
Sign
```

如果 PUF 硬體不能平行處理：

PUF 端可自行：

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

這個硬體排程不應丟給 PQC 端處理。

---

# 59. PUF Server 建議輸出 Log

建議至少：

```text
[PUF REQUEST] Client requested 32 bytes
```

可再加：

```text
timestamp
latency
request id
success / failure
```

但不要把 raw PUF secret material 寫入 log。

---

# 60. 資工系可以用什麼技術做 Server

不限。

例如：

```text
FastAPI
Flask
Django
C/C++
Rust
Go
Node.js
Embedded HTTP server
```

只要符合：

```text
POST /api/random/
```

即可。

---

# 61. FastAPI 參考 Server

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
    # 資工系在這裡接真正的 PUF。
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

# 62. 聯調前雙方先確認

```text
PUF Server IP:
PUF Server Port:
API Path:
HTTP / HTTPS:
Timeout:
Authentication:
Firewall:
Network segment:
Concurrent request support:
Maximum random bytes:
Average latency:
PUF failure behavior:
```

---

# 63. 交給資工系的最小檔案集合

至少給：

```text
PQC_MLDSA_PUF_COMPLETE_GUIDE.md
PUF_INTERFACE_SPEC.md
test_puf_interface.py
.env.example
```

建議再給：

```text
requirements.txt
test_mldsa.py
```

如果需要直接聯調完整 PQC：

```text
pqc/
config/
manage.py
```

---

# 64. 資工系收到後的執行順序

## Step 1

看：

```text
PUF_INTERFACE_SPEC.md
```

## Step 2

實作：

```text
POST /api/random/
```

## Step 3

讓：

```text
test_puf_interface.py
```

全部 PASS。

## Step 4

提供：

```text
IP
Port
Endpoint
啟動方式
```

## Step 5

PQC 端設定：

```env
PQC_RANDOM_MODE=puf
PUF_ENDPOINT=http://PUF_SERVER_IP:PORT/api/random/
PUF_TIMEOUT=5
```

## Step 6

PQC 端：

```cmd
python test_mldsa.py
```

## Step 7

確認：

```text
KeyGen successful
Sign successful
Verify = True
```

## Step 8

確認 PUF Server log：

```text
[PUF REQUEST] Client requested ...
```

---

# 65. 最終驗收條件

以下全部成立：

```text
[PASS] PUF Server 可啟動
[PASS] POST /api/random/ 正常
[PASS] 16-byte request
[PASS] 32-byte request
[PASS] 64-byte request
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

# 66. 最終預期成果

最終 demo 可以呈現：

```text
1. 使用 System RNG
2. 完成 ML-DSA-65 KeyGen / Sign / Verify

3. 切換 .env：
   PQC_RANDOM_MODE=puf

4. 不修改 ML-DSA 原始碼

5. 再執行 ML-DSA-65 KeyGen / Sign / Verify

6. PUF Server log 同時顯示：
   ML-DSA 正在要求 random bytes

7. Verify = True
```

最終展示架構：

```text
                  Django REST API
                         |
                         v
                    ML-DSA-65
                         |
                         v
                      liboqs
                         |
                +--------+--------+
                |                 |
                v                 v
           System RNG      PUF Random API
                                  |
                                  v
                                 PUF
```

切換方式：

```env
PQC_RANDOM_MODE=system
```

或：

```env
PQC_RANDOM_MODE=puf
```

不需要修改：

```text
MLDSAService
Django views
API endpoints
KeyGen logic
Sign logic
Verify logic
```

---

# 67. 研究結果應清楚區分兩件事

## 介面整合成功

代表：

```text
PUF API
-> PQC
-> liboqs
-> ML-DSA
```

可以正常運作。

## PUF 密碼學品質

需要另外驗證：

```text
Entropy
Bias
Reliability
Uniqueness
Stability
Unpredictability
Environmental robustness
```

這兩件事情不要混為一談。

---

# 68. 正式部署前還缺什麼

目前是：

```text
Research / PoC
```

正式部署至少還要做：

```text
HTTPS / TLS
PUF Server Authentication
API Authentication
Authorization
Rate Limiting
Secret Key Secure Storage
Key ID
Key Rotation
Audit Logging
Error Sanitization
Replay Protection
Network Security
Production WSGI / ASGI
```

目前 `/keygen/` 直接回 Secret Key：

```json
{
    "secret_key": "..."
}
```

只適合 PoC。

正式版本應：

```text
Private Key 留在 Server / Secure Storage
```

API 只回：

```text
key_id
public_key
```

---

# 69. macOS 搬移方式

不要把 Windows 的：

```text
.venv
```

複製到 Mac。

正確：

```bash
cd PQC_API

python3 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

Native build 準備：

```bash
xcode-select --install
```

確認：

```bash
clang --version
git --version
cmake --version
```

再：

```bash
python -c "import oqs; print(oqs.oqs_version())"
```

---

# 70. 新 Windows 電腦快速建立

```cmd
cd /d C:\path\to\PQC_API

python -m venv .venv

.venv\Scripts\activate

python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

安裝：

```text
Git
Visual Studio Build Tools
Desktop development with C++
```

Native build CMD：

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

然後：

```cmd
python manage.py migrate
python manage.py check
```

---

# 71. 常見錯誤

## `.venv\Scripts\Activate.ps1` 在 CMD 沒反應

CMD 請用：

```cmd
.venv\Scripts\activate
```

---

## `cl` 找不到

執行：

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

---

## `cmake` 找不到

同上，先載入 Build Tools 環境。

---

## `git` 找不到

確認 Git for Windows 已安裝並重新開 CMD。

---

## `include is not defined`

`config/urls.py`：

```python
from django.urls import (
    include,
    path
)
```

---

## `HTTP 405 Method Not Allowed`

例如：

```text
GET /api/pqc/keygen/
```

但 API 只接受：

```text
POST
```

這是正常的。

---

## `IndentationError`

Python 縮排錯誤。

建議：

```cmd
python -m py_compile path\to\file.py
```

先做語法檢查。

---

## `MLDSAService has no attribute sign`

通常代表：

```text
sign()
```

因縮排錯誤掉到 class 外面，或被刪掉。

可檢查：

```cmd
python -c "from pqc.services.mldsa_service import MLDSAService; print(hasattr(MLDSAService, 'sign'))"
```

應為：

```text
True
```

---

# 72. 建議的正式驗收順序

```text
[1] Python / venv
[2] pip install -r requirements.txt
[3] Git / CMake / Compiler
[4] import oqs
[5] ML-DSA-65 enabled
[6] python manage.py check
[7] System RNG test_mldsa.py
[8] Mock PUF Server
[9] test_puf_interface.py
[10] test_puf_provider.py
[11] test_oqs_puf_rng.py
[12] test_mldsa_puf_keygen.py
[13] .env -> puf
[14] test_mldsa.py
[15] Django keygen
[16] Django sign
[17] Django verify
[18] Replace Mock PUF with real PUF
[19] Re-run interface test
[20] Re-run ML-DSA integration test
```

---

# 73. 最後交接一句話

給資工系的任務可以濃縮成：

```text
你們只需要實作：

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

並且讓 test_puf_interface.py 全部 PASS。
```

PQC 端會負責：

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

# 74. 最終目標

真正的完成狀態不是：

```text
PUF 可以產生 bytes
```

而是：

```text
Real PUF
   |
   v
PUF Random Server
   |
   v
HTTP REST API
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

並且可透過：

```env
PQC_RANDOM_MODE=system
```

與：

```env
PQC_RANDOM_MODE=puf
```

在**不修改 ML-DSA 核心程式碼**的情況下切換亂數來源。

這就是本專案的最終整合成果。
