from pqc.services.random.system_provider import SystemRandomProvider
from pqc.services.random.mock_puf_provider import MockPUFRandomProvider


# ============================================================
# 測試 System Random Provider
# ============================================================

system_rng = SystemRandomProvider()

system_random = system_rng.get_random_bytes(32)

print("=== System Random Provider ===")
print("Length:", len(system_random), "bytes")
print("Random:", system_random.hex())


# ============================================================
# 測試 Mock PUF Random Provider
# ============================================================

mock_puf_rng = MockPUFRandomProvider()

mock_puf_random = mock_puf_rng.get_random_bytes(32)

print("\n=== Mock PUF Random Provider ===")
print("Length:", len(mock_puf_random), "bytes")
print("Random:", mock_puf_random.hex())


# ============================================================
# 基本驗證
# ============================================================

print("\n=== Validation ===")

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