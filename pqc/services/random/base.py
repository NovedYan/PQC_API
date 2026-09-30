from abc import ABC, abstractmethod


class RandomProvider(ABC):
    """
    所有亂數來源的共同介面。

    不管底層亂數來自：
    - Windows / macOS / Linux
    - PUF
    - 遠端 REST API
    - FPGA / MCU

    對上層程式而言，都必須提供相同的方法：

        get_random_bytes(length)

    上層不需要知道亂數是如何產生的。
    """

    @abstractmethod
    def get_random_bytes(self, length: int) -> bytes:
        """
        取得指定長度的亂數。

        Args:
            length:
                要求的亂數長度，單位為 bytes。

        Returns:
            bytes:
                恰好 length bytes 的亂數資料。
        """

        pass