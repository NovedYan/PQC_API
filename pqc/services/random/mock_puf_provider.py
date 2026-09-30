import os

from .base import RandomProvider


class MockPUFRandomProvider(RandomProvider):
    """
    模擬 PUF Random Provider。

    注意：
    這不是真正的 PUF。

    目前只是使用 os.urandom() 來模擬
    未來資工系提供的 PUF-derived random bytes。

    目的：
    先讓我們測試整個 Provider 架構，
    不需要等待真正的 PUF 完成。
    """

    def get_random_bytes(self, length: int) -> bytes:
        """
        模擬取得 PUF-derived random bytes。
        """

        if length <= 0:
            raise ValueError("length must be greater than 0")

        # TODO:
        # 未來資工系完成 PUF 後，
        # 這裡會改成呼叫真正的 PUF API。
        #
        # 目前暫時使用 os.urandom() 模擬。
        random_data = os.urandom(length)

        return random_data