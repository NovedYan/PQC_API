# ============================================================
# ML-DSA Service
# ============================================================

# liboqs-python
import oqs

# Random Manager
# 負責選擇 System RNG 或 PUF RNG
from .random.manager import RandomManager

# Custom RNG Adapter
# 負責檢查 PUF / Custom RNG 是否發生錯誤
from .random.oqs_adapter import OQSRandomAdapter


class MLDSAService:
    """
    ML-DSA-65 密碼服務。

    提供：

    1. Key Generation
    2. Signing
    3. Verification

    Random Source 可以由：

    - System RNG
    - PUF RNG

    提供。

    使用哪一個 RNG，
    由環境變數 PQC_RANDOM_MODE 決定。
    """

    # ========================================================
    # Algorithm
    # ========================================================

    ALGORITHM = "ML-DSA-65"


    # ========================================================
    # RNG Preparation
    # ========================================================

    @classmethod
    def _prepare_rng(cls):
        """
        在需要 Randomness 的 ML-DSA 操作之前，
        確認 liboqs 已經設定好 RNG。

        PQC_RANDOM_MODE=system
            使用作業系統 RNG

        PQC_RANDOM_MODE=puf
            使用 PUF REST API
        """

        # 設定目前 RNG
        RandomManager.configure()

        # 清除之前可能留下的 RNG Error
        OQSRandomAdapter.clear_error()


    # ========================================================
    # RNG Error Check
    # ========================================================

    @classmethod
    def _check_rng(cls):
        """
        檢查 Custom RNG 是否發生錯誤。

        例如：

        - PUF Server 無法連線
        - PUF API 回傳錯誤
        - Base64 格式錯誤
        - 回傳長度不正確
        """

        OQSRandomAdapter.raise_if_error()


    # ========================================================
    # Key Generation
    # ========================================================

    @classmethod
    def generate_keypair(cls):
        """
        產生 ML-DSA-65 金鑰對。

        Returns:
            tuple:
                public_key:
                    ML-DSA-65 Public Key bytes

                secret_key:
                    ML-DSA-65 Secret Key bytes
        """

        # ----------------------------------------------------
        # 1. 準備 RNG
        # ----------------------------------------------------

        cls._prepare_rng()


        # ----------------------------------------------------
        # 2. 建立 ML-DSA-65 Key Pair
        # ----------------------------------------------------

        with oqs.Signature(
            cls.ALGORITHM
        ) as signer:

            # generate_keypair()
            # 回傳 Public Key
            public_key = signer.generate_keypair()

            # Secret Key 儲存在 signer 內部
            # 因此需要另外 export
            secret_key = signer.export_secret_key()


        # ----------------------------------------------------
        # 3. 檢查 PUF / RNG 是否發生錯誤
        # ----------------------------------------------------

        cls._check_rng()


        # ----------------------------------------------------
        # 4. 回傳 Key Pair
        # ----------------------------------------------------

        return public_key, secret_key


    # ========================================================
    # Signing
    # ========================================================

    @classmethod
    def sign(
        cls,
        message: bytes,
        secret_key: bytes
    ):
        """
        使用 ML-DSA-65 Secret Key 對訊息進行數位簽章。

        Args:
            message:
                要簽章的資料，bytes。

            secret_key:
                ML-DSA-65 Secret Key，bytes。

        Returns:
            bytes:
                ML-DSA-65 Signature。
        """

        # ----------------------------------------------------
        # 1. 準備 RNG
        # ----------------------------------------------------

        # Sign 必須自己準備 RNG，
        # 不能假設之前一定執行過 KeyGen。
        cls._prepare_rng()


        # ----------------------------------------------------
        # 2. ML-DSA-65 Signing
        # ----------------------------------------------------

        with oqs.Signature(
            cls.ALGORITHM,
            secret_key=secret_key
        ) as signer:

            signature = signer.sign(
                message
            )


        # ----------------------------------------------------
        # 3. 檢查 PUF / RNG 是否發生錯誤
        # ----------------------------------------------------

        cls._check_rng()


        # ----------------------------------------------------
        # 4. 回傳 Signature
        # ----------------------------------------------------

        return signature


    # ========================================================
    # Verification
    # ========================================================

    @classmethod
    def verify(
        cls,
        message: bytes,
        signature: bytes,
        public_key: bytes
    ):
        """
        驗證 ML-DSA-65 數位簽章。

        Verification 不需要產生新的 Randomness。

        Args:
            message:
                原始訊息。

            signature:
                ML-DSA-65 Signature。

            public_key:
                ML-DSA-65 Public Key。

        Returns:
            bool:
                True:
                    Signature 正確

                False:
                    Signature 不正確
        """

        with oqs.Signature(
            cls.ALGORITHM
        ) as verifier:

            is_valid = verifier.verify(
                message,
                signature,
                public_key
            )

        return is_valid