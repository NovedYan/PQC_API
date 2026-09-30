# 匯入真正的 PUF Random Provider Client
from pqc.services.random.puf_provider import PUFRandomProvider


# ============================================================
# 建立 PUF Provider
# ============================================================

# 現在連線到我們的 Mock PUF Server
#
# 未來只需要把這個網址換成資工系的電腦 IP。
provider = PUFRandomProvider(
    endpoint="http://127.0.0.1:9000/api/random/"
)


# ============================================================
# 向 PUF 要求 32 bytes
# ============================================================

print("Requesting 32 bytes from PUF...")

random_32 = provider.get_random_bytes(32)

print("Received:", len(random_32), "bytes")
print("Random:", random_32.hex())


# ============================================================
# 向 PUF 要求 64 bytes
# ============================================================

print("\nRequesting 64 bytes from PUF...")

random_64 = provider.get_random_bytes(64)

print("Received:", len(random_64), "bytes")
print("Random:", random_64.hex())


# ============================================================
# Validation
# ============================================================

print("\n=== Validation ===")

print(
    "32-byte request correct:",
    len(random_32) == 32
)

print(
    "64-byte request correct:",
    len(random_64) == 64
)

print(
    "Outputs are different:",
    random_32 != random_64[:32]
)