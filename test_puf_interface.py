import base64
import requests


# ============================================================
# PUF API 設定
# ============================================================

# 測試階段使用 Mock PUF Server
#
# 未來交給資工系時，
# 只需要將這個網址改成他們的 PUF Server IP。
PUF_ENDPOINT = "http://127.0.0.1:9000/api/random/"

# HTTP timeout
TIMEOUT = 5


# ============================================================
# 顯示測試結果
# ============================================================

def show_result(test_name: str, passed: bool, detail: str = ""):
    """
    統一顯示測試結果。

    PASS:
        測試成功

    FAIL:
        測試失敗
    """

    status = "PASS" if passed else "FAIL"

    print(f"[{status}] {test_name}")

    if detail:
        print(f"       {detail}")


# ============================================================
# 測試正常的 Random Request
# ============================================================

def test_random_request(length: int):
    """
    測試要求指定長度的 random bytes。

    檢查：

    1. HTTP Status = 200
    2. Response 是 JSON
    3. 包含 random
    4. 包含 length
    5. Base64 格式正確
    6. Decode 後長度正確
    """

    try:

        response = requests.post(
            PUF_ENDPOINT,
            json={
                "length": length
            },
            timeout=TIMEOUT
        )

    except requests.RequestException as error:

        show_result(
            f"{length}-byte request",
            False,
            f"Connection failed: {error}"
        )

        return None


    # --------------------------------------------------------
    # HTTP Status
    # --------------------------------------------------------

    if response.status_code != 200:

        show_result(
            f"{length}-byte request",
            False,
            f"HTTP {response.status_code}"
        )

        return None


    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        show_result(
            f"{length}-byte request",
            False,
            "Response is not valid JSON"
        )

        return None


    # --------------------------------------------------------
    # random 欄位
    # --------------------------------------------------------

    if "random" not in data:

        show_result(
            f"{length}-byte request",
            False,
            "Missing 'random' field"
        )

        return None


    # --------------------------------------------------------
    # length 欄位
    # --------------------------------------------------------

    if "length" not in data:

        show_result(
            f"{length}-byte request",
            False,
            "Missing 'length' field"
        )

        return None


    # --------------------------------------------------------
    # 檢查 Response 宣告的 length
    # --------------------------------------------------------

    if data["length"] != length:

        show_result(
            f"{length}-byte request",
            False,
            (
                "Incorrect length field: "
                f"expected {length}, "
                f"received {data['length']}"
            )
        )

        return None


    # --------------------------------------------------------
    # Base64 Decode
    # --------------------------------------------------------

    try:

        random_bytes = base64.b64decode(
            data["random"],
            validate=True
        )

    except Exception:

        show_result(
            f"{length}-byte request",
            False,
            "random is not valid Base64"
        )

        return None


    # --------------------------------------------------------
    # 檢查真正 bytes 長度
    # --------------------------------------------------------

    if len(random_bytes) != length:

        show_result(
            f"{length}-byte request",
            False,
            (
                "Decoded byte length incorrect: "
                f"expected {length}, "
                f"received {len(random_bytes)}"
            )
        )

        return None


    show_result(
        f"{length}-byte request",
        True,
        f"Received exactly {length} bytes"
    )

    return random_bytes


# ============================================================
# 測試錯誤輸入
# ============================================================

def test_invalid_length(value):
    """
    確認 PUF API 不接受不合法的 length。

    預期：
        HTTP 400
    """

    try:

        response = requests.post(
            PUF_ENDPOINT,
            json={
                "length": value
            },
            timeout=TIMEOUT
        )

    except requests.RequestException as error:

        show_result(
            f"Reject invalid length: {value}",
            False,
            str(error)
        )

        return


    passed = response.status_code == 400

    show_result(
        f"Reject invalid length: {value}",
        passed,
        f"HTTP {response.status_code}"
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print("====================================")
    print("PUF Random API Compliance Test")
    print("====================================")

    print(f"Endpoint: {PUF_ENDPOINT}")
    print()


    # --------------------------------------------------------
    # 1. 正常長度測試
    # --------------------------------------------------------

    random_16 = test_random_request(16)
    random_32_a = test_random_request(32)
    random_32_b = test_random_request(32)
    random_64 = test_random_request(64)


    # --------------------------------------------------------
    # 2. 基本重複輸出檢查
    # --------------------------------------------------------

    if (
        random_32_a is not None
        and random_32_b is not None
    ):

        different = random_32_a != random_32_b

        show_result(
            "Repeated requests produce different output",
            different,
            "Sanity check only; this does NOT prove randomness quality"
        )


    # --------------------------------------------------------
    # 3. 錯誤輸入測試
    # --------------------------------------------------------

    print()

    test_invalid_length(0)
    test_invalid_length(-1)
    test_invalid_length("32")


    print()
    print("====================================")
    print("Test completed")
    print("====================================")