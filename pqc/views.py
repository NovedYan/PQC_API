from django.shortcuts import render

# Base64 編碼工具
# 用來把 binary bytes 轉成可以放進 JSON 的文字
import base64

from rest_framework.decorators import api_view
from rest_framework.response import Response

# 匯入我們自己建立的 ML-DSA Service
from .services.mldsa_service import MLDSAService


# ============================================================
# Status API
# ============================================================

@api_view(["GET"])
def status(request):
    """
    檢查 PQC API 是否正常運作。
    """

    return Response({
        "status": "ok",
        "service": "PQC API",
        "algorithm": "ML-DSA-65"
    })


# ============================================================
# ML-DSA Key Generation API
# ============================================================

@api_view(["POST"])
def keygen(request):
    """
    產生一組 ML-DSA-65 公私鑰。

    REST API 使用 JSON，
    但 ML-DSA 金鑰是 bytes（二進位資料）。

    因此流程為：

        ML-DSA bytes
            ↓
        Base64 Encode
            ↓
        UTF-8 String
            ↓
           JSON

    Returns:
        public_key:
            Base64 編碼後的公鑰。

        secret_key:
            Base64 編碼後的私鑰。
    """

    # 呼叫我們建立的 MLDSAService
    # 產生 ML-DSA-65 公私鑰
    public_key, secret_key = MLDSAService.generate_keypair()

    # 將 public key 從 bytes 轉成 Base64
    public_key_b64 = base64.b64encode(
        public_key
    ).decode("utf-8")

    # 將 secret key 從 bytes 轉成 Base64
    secret_key_b64 = base64.b64encode(
        secret_key
    ).decode("utf-8")

    # 回傳 JSON
    return Response({
        "algorithm": MLDSAService.ALGORITHM,

        "public_key": public_key_b64,

        "secret_key": secret_key_b64,

        # 額外回傳原始 bytes 長度
        # 方便研究與測試時確認資料是否正確
        "public_key_length": len(public_key),

        "secret_key_length": len(secret_key)
    })
    
    # ============================================================
# ML-DSA Signing API
# ============================================================

@api_view(["POST"])
def sign(request):
    """
    使用 ML-DSA-65 私鑰對訊息進行數位簽章。

    Request JSON:

    {
        "message": "Hello PQC",
        "secret_key": "Base64 encoded secret key"
    }

    流程：

        JSON
          ↓
        message (string)
          ↓
        UTF-8 Encode
          ↓
        message bytes

        secret_key (Base64 string)
          ↓
        Base64 Decode
          ↓
        secret_key bytes

          ↓

        ML-DSA-65 Sign

          ↓

        signature bytes
          ↓
        Base64 Encode
          ↓
        JSON
    """

    # --------------------------------------------------------
    # 1. 從 HTTP Request 中取得 message
    # --------------------------------------------------------

    message = request.data.get("message")

    # --------------------------------------------------------
    # 2. 從 HTTP Request 中取得 Base64 Secret Key
    # --------------------------------------------------------

    secret_key_b64 = request.data.get("secret_key")


    # --------------------------------------------------------
    # 3. 檢查必要參數
    # --------------------------------------------------------

    # 如果沒有 message
    if message is None:
        return Response(
            {
                "error": "message is required"
            },
            status=400
        )

    # 如果沒有 secret_key
    if secret_key_b64 is None:
        return Response(
            {
                "error": "secret_key is required"
            },
            status=400
        )


    # --------------------------------------------------------
    # 4. 將 message 從 string 轉換成 bytes
    # --------------------------------------------------------

    message_bytes = message.encode("utf-8")


    # --------------------------------------------------------
    # 5. 將 Base64 Secret Key 轉回原始 bytes
    # --------------------------------------------------------

    try:

        secret_key = base64.b64decode(
            secret_key_b64,
            validate=True
        )

    except Exception:

        return Response(
            {
                "error": "secret_key is not valid Base64"
            },
            status=400
        )


    # --------------------------------------------------------
    # 6. 使用 MLDSAService 進行簽章
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # 7. Signature bytes → Base64
    # --------------------------------------------------------

    signature_b64 = base64.b64encode(
        signature
    ).decode("utf-8")


    # --------------------------------------------------------
    # 8. 回傳 JSON
    # --------------------------------------------------------

    return Response({

        "algorithm": MLDSAService.ALGORITHM,

        "message": message,

        "signature": signature_b64,

        "signature_length": len(signature)

    })
    
    # ============================================================
# ML-DSA Verification API
# ============================================================

@api_view(["POST"])
def verify(request):
    """
    驗證 ML-DSA-65 數位簽章。

    Request JSON:

    {
        "message": "Hello PQC",
        "signature": "Base64 encoded signature",
        "public_key": "Base64 encoded public key"
    }

    流程：

        message
          ↓
        UTF-8 Encode
          ↓
        bytes

        signature / public_key
          ↓
        Base64 Decode
          ↓
        bytes

          ↓

        ML-DSA-65 Verify

          ↓

        True / False
    """

    # --------------------------------------------------------
    # 1. 從 Request 取得資料
    # --------------------------------------------------------

    message = request.data.get("message")
    signature_b64 = request.data.get("signature")
    public_key_b64 = request.data.get("public_key")


    # --------------------------------------------------------
    # 2. 檢查必要參數
    # --------------------------------------------------------

    if message is None:
        return Response(
            {
                "error": "message is required"
            },
            status=400
        )

    if signature_b64 is None:
        return Response(
            {
                "error": "signature is required"
            },
            status=400
        )

    if public_key_b64 is None:
        return Response(
            {
                "error": "public_key is required"
            },
            status=400
        )


    # --------------------------------------------------------
    # 3. Message string → bytes
    # --------------------------------------------------------

    message_bytes = message.encode("utf-8")


    # --------------------------------------------------------
    # 4. Base64 Signature → bytes
    # --------------------------------------------------------

    try:
        signature = base64.b64decode(
            signature_b64,
            validate=True
        )

    except Exception:
        return Response(
            {
                "error": "signature is not valid Base64"
            },
            status=400
        )


    # --------------------------------------------------------
    # 5. Base64 Public Key → bytes
    # --------------------------------------------------------

    try:
        public_key = base64.b64decode(
            public_key_b64,
            validate=True
        )

    except Exception:
        return Response(
            {
                "error": "public_key is not valid Base64"
            },
            status=400
        )


    # --------------------------------------------------------
    # 6. ML-DSA-65 Verification
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # 7. 回傳驗證結果
    # --------------------------------------------------------

    return Response({
        "algorithm": MLDSAService.ALGORITHM,
        "message": message,
        "valid": is_valid
    })