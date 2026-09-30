# 匯入我們自己建立的 ML-DSA Service
from pqc.services.mldsa_service import MLDSAService


# 準備測試訊息
message = b"Hello ML-DSA Service"


# =========================
# 1. Key Generation
# =========================

public_key, secret_key = MLDSAService.generate_keypair()

print("--- Key Generation ---")
print("Public key length:", len(public_key), "bytes")
print("Secret key length:", len(secret_key), "bytes")


# =========================
# 2. Signing
# =========================

signature = MLDSAService.sign(
    message,
    secret_key
)

print("\n--- Signing ---")
print("Signature length:", len(signature), "bytes")


# =========================
# 3. Verification
# =========================

is_valid = MLDSAService.verify(
    message,
    signature,
    public_key
)

print("\n--- Verification ---")
print("Signature valid:", is_valid)