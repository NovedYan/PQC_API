import os

from .base import RandomProvider


class SystemRandomProvider(RandomProvider):
    """
    使用作業系統提供的安全亂數來源。

    Python 的 os.urandom() 會使用作業系統的
    cryptographically secure random source。

    目前開發與測試階段使用這個 Provider。
    """

    def get_random_bytes(self, length: int) -> bytes:
        """
        取得指定長度的系統安全亂數。
        """

        # 不允許要求 0 或負數 bytes
        if length <= 0:
            raise ValueError("length must be greater than 0")

        # 從作業系統取得 length bytes 的安全亂數
        random_data = os.urandom(length)

        return random_data