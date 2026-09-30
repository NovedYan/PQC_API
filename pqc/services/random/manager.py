import os

# 讀取專案根目錄的 .env 設定檔
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

# liboqs RNG 控制
from oqs.rand import randombytes_switch_algorithm

# PUF Provider
from .puf_provider import PUFRandomProvider

# liboqs Custom RNG Adapter
from .oqs_adapter import OQSRandomAdapter


class RandomManager:
    """
    管理 ML-DSA 使用的亂數來源。

    支援：

    1. system
       使用作業系統 / liboqs 預設安全亂數。

    2. puf
       使用外部 PUF Random API。

    設定全部透過環境變數控制，
    因此這一層不依賴 Django。
    """

    _configured = False
    _mode = None

    @classmethod
    def configure(cls):
        """
        根據環境變數設定 liboqs RNG。

        環境變數：

        PQC_RANDOM_MODE
            system 或 puf

        PUF_ENDPOINT
            PUF API 網址

        PUF_TIMEOUT
            HTTP timeout 秒數
        """

        # 同一個 Python process 只設定一次
        if cls._configured:
            return

        # --------------------------------------------
        # 讀取亂數模式
        # --------------------------------------------

        mode = os.getenv(
            "PQC_RANDOM_MODE",
            "system"
        ).lower()

        # ============================================
        # SYSTEM MODE
        # ============================================

        if mode == "system":

            randombytes_switch_algorithm(
                "system"
            )

            cls._mode = "system"

        # ============================================
        # PUF MODE
        # ============================================

        elif mode == "puf":

            # PUF API Endpoint
            endpoint = os.getenv(
                "PUF_ENDPOINT",
                "http://127.0.0.1:9000/api/random/"
            )

            # HTTP Timeout
            timeout = int(
                os.getenv(
                    "PUF_TIMEOUT",
                    "5"
                )
            )

            # 建立 PUF HTTP Provider
            provider = PUFRandomProvider(
                endpoint=endpoint,
                timeout=timeout
            )

            # 將 PUF Provider 接入 liboqs
            OQSRandomAdapter.install(
                provider
            )

            cls._mode = "puf"

        # ============================================
        # 錯誤設定
        # ============================================

        else:

            raise ValueError(
                "Invalid PQC_RANDOM_MODE. "
                "Allowed values are 'system' or 'puf'."
            )

        cls._configured = True

    @classmethod
    def get_mode(cls):
        """
        取得目前 RNG 模式。
        """

        return cls._mode