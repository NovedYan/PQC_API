# liboqs-python 官方 Random API
from oqs.rand import (
    randombytes,
    randombytes_switch_algorithm
)

# 我們建立的 PUF HTTP Client
from pqc.services.random.puf_provider import (
    PUFRandomProvider
)

# 我們剛建立的 liboqs Adapter
from pqc.services.random.oqs_adapter import (
    OQSRandomAdapter
)


# ============================================================
# 建立 PUF Provider
# ============================================================

provider = PUFRandomProvider(
    endpoint="http://127.0.0.1:9000/api/random/"
)


try:

    # ========================================================
    # 把 PUF Provider 註冊進 liboqs
    # ========================================================

    OQSRandomAdapter.install(
        provider
    )

    print(
        "PUF Random Provider installed into liboqs."
    )


    # ========================================================
    # Test 1：向 liboqs 要 32 bytes
    # ========================================================

    OQSRandomAdapter.clear_error()

    random_32 = randombytes(32)

    # 檢查 callback 是否發生問題
    OQSRandomAdapter.raise_if_error()

    print("\n=== liboqs PUF RNG Test ===")

    print(
        "32-byte random length:",
        len(random_32)
    )

    print(
        "Random:",
        random_32.hex()
    )


    # ========================================================
    # Test 2：再要求一次
    # ========================================================

    OQSRandomAdapter.clear_error()

    random_32_second = randombytes(32)

    OQSRandomAdapter.raise_if_error()

    print(
        "\nSecond random:",
        random_32_second.hex()
    )


    # ========================================================
    # Validation
    # ========================================================

    print("\n=== Validation ===")

    print(
        "Length correct:",
        len(random_32) == 32
    )

    print(
        "Outputs different:",
        random_32 != random_32_second
    )


finally:

    # ========================================================
    # 測試完成後恢復 liboqs 系統 RNG
    # ========================================================

    randombytes_switch_algorithm(
        "system"
    )

    print(
        "\nliboqs RNG restored to system."
    )