# liboqs RNG 控制
from oqs.rand import randombytes_switch_algorithm

# 我們原本建立的 ML-DSA Service
from pqc.services.mldsa_service import MLDSAService

# 透過 HTTP 呼叫 PUF Server 的 Provider
from pqc.services.random.puf_provider import PUFRandomProvider

# 將 RandomProvider 接入 liboqs
from pqc.services.random.oqs_adapter import OQSRandomAdapter


# ============================================================
# 建立 PUF Random Provider
# ============================================================

# 現在使用本機 Mock PUF Server
# 未來只需要把這個 endpoint 換成資工系的 PUF Server
provider = PUFRandomProvider(
    endpoint="http://127.0.0.1:9000/api/random/"
)


try:

    # ========================================================
    # 1. 將 PUF Provider 安裝到 liboqs
    # ========================================================

    OQSRandomAdapter.install(provider)

    print("PUF Random Provider installed into liboqs.")


    # ========================================================
    # 2. 清除舊的 RNG Error
    # ========================================================

    OQSRandomAdapter.clear_error()


    # ========================================================
    # 3. 執行 ML-DSA-65 Key Generation
    # ========================================================

    print("\nGenerating ML-DSA-65 keypair...")

    public_key, secret_key = MLDSAService.generate_keypair()


    # ========================================================
    # 4. 檢查 PUF callback 是否發生錯誤
    # ========================================================

    OQSRandomAdapter.raise_if_error()


    # ========================================================
    # 5. 顯示結果
    # ========================================================

    print("\n=== ML-DSA-65 + PUF KeyGen ===")

    print(
        "Public key length:",
        len(public_key),
        "bytes"
    )

    print(
        "Secret key length:",
        len(secret_key),
        "bytes"
    )


    # ========================================================
    # 6. 基本驗證
    # ========================================================

    print("\n=== Validation ===")

    print(
        "Public key created:",
        len(public_key) > 0
    )

    print(
        "Secret key created:",
        len(secret_key) > 0
    )


finally:

    # ========================================================
    # 7. 測試完成後恢復 liboqs 系統 RNG
    # ========================================================

    randombytes_switch_algorithm("system")

    print("\nliboqs RNG restored to system.")