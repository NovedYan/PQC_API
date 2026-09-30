import base64

import requests

from .base import RandomProvider


class PUFRandomProvider(RandomProvider):
    """
    真正用來連接外部 PUF 系統的 Random Provider。

    這個類別不需要知道 PUF 底層如何實作。

    PUF 可以是：
    - Python
    - C / C++
    - FPGA
    - MCU
    - Raspberry Pi
    - 另一台電腦

    只要對方提供符合規格的 HTTP REST API 即可。


    預期 API：

        POST /api/random/

    Request:

        {
            "length": 32
        }

    Response:

        {
            "random": "Base64 encoded random data",
            "length": 32
        }
    """

    def __init__(
        self,
        endpoint: str,
        timeout: int = 5
    ):
        """
        Args:
            endpoint:
                資工系提供的 PUF Random API 網址。

                例如：
                http://192.168.1.100:8000/api/random/

            timeout:
                等待 PUF 回應的最長秒數。
        """

        self.endpoint = endpoint
        self.timeout = timeout


    def get_random_bytes(self, length: int) -> bytes:
        """
        向外部 PUF 系統要求指定長度的亂數。

        Args:
            length:
                需要多少 bytes。

        Returns:
            bytes:
                PUF 系統產生的亂數。
        """

        # ----------------------------------------------------
        # 1. 檢查 length
        # ----------------------------------------------------

        if length <= 0:
            raise ValueError(
                "length must be greater than 0"
            )


        # ----------------------------------------------------
        # 2. 建立送給 PUF API 的 JSON
        # ----------------------------------------------------

        payload = {
            "length": length
        }


        # ----------------------------------------------------
        # 3. 呼叫資工系的 PUF REST API
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # 4. 確認 HTTP 狀態碼
        # ----------------------------------------------------

        if response.status_code != 200:

            raise RuntimeError(
                "PUF service returned "
                f"HTTP {response.status_code}"
            )


        # ----------------------------------------------------
        # 5. 將 Response 轉成 JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            raise RuntimeError(
                "PUF service did not return valid JSON"
            )


        # ----------------------------------------------------
        # 6. 確認必要欄位存在
        # ----------------------------------------------------

        if "random" not in data:

            raise RuntimeError(
                "PUF response missing 'random'"
            )

        if "length" not in data:

            raise RuntimeError(
                "PUF response missing 'length'"
            )


        # ----------------------------------------------------
        # 7. 檢查 PUF 宣告的長度
        # ----------------------------------------------------

        if data["length"] != length:

            raise RuntimeError(
                "PUF returned incorrect length value"
            )


        # ----------------------------------------------------
        # 8. Base64 → bytes
        # ----------------------------------------------------

        try:

            random_bytes = base64.b64decode(
                data["random"],
                validate=True
            )

        except Exception:

            raise RuntimeError(
                "PUF random data is not valid Base64"
            )


        # ----------------------------------------------------
        # 9. 再檢查真正 bytes 長度
        # ----------------------------------------------------

        if len(random_bytes) != length:

            raise RuntimeError(
                "PUF returned incorrect number of bytes"
            )


        # ----------------------------------------------------
        # 10. 回傳 PUF Random Bytes
        # ----------------------------------------------------

        return random_bytes