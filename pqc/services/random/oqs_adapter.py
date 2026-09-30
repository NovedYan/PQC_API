# ctypes 用來把 Python function
# 轉成 liboqs C library 可以呼叫的 callback
import ctypes as ct

# threading.local() 用來保存目前執行緒發生的 RNG error
import threading

# liboqs-python
import oqs

# 我們自己定義的 Random Provider 介面
from .base import RandomProvider


# ============================================================
# liboqs Custom RNG Callback Type
# ============================================================

# liboqs 的 custom random callback 在 C 裡概念為：
#
# void randombytes(
#     uint8_t *random_array,
#     size_t bytes_to_read
# );
#
# 所以 Python 必須建立相同格式的 callback。
OQS_RANDOM_CALLBACK = ct.CFUNCTYPE(
    None,
    ct.POINTER(ct.c_uint8),
    ct.c_size_t
)


class OQSRandomAdapter:
    """
    將我們的 RandomProvider 接到 liboqs。

    架構：

        RandomProvider
              ↓
        OQSRandomAdapter
              ↓
    OQS_randombytes_custom_algorithm()
              ↓
           liboqs
              ↓
          ML-DSA-65

    RandomProvider 可以是：

        SystemRandomProvider

    或：

        PUFRandomProvider

    因此 ML-DSA 不需要知道真正的亂數來源。
    """

    # --------------------------------------------------------
    # callback 一定要保存 reference
    #
    # 如果 Python Garbage Collector 把 callback 回收，
    # liboqs 再呼叫它時可能造成 crash。
    # --------------------------------------------------------

    _callback = None

    # 目前使用的 RandomProvider
    _provider = None

    # 儲存 callback 發生的錯誤
    _thread_state = threading.local()


    # ========================================================
    # Install Provider
    # ========================================================

    @classmethod
    def install(cls, provider: RandomProvider):
        """
        將 RandomProvider 註冊成 liboqs 的亂數來源。

        Args:
            provider:
                RandomProvider implementation

                例如：

                SystemRandomProvider()

                或：

                PUFRandomProvider(...)
        """

        cls._provider = provider

        # 清除之前的 error
        cls.clear_error()


        # ----------------------------------------------------
        # 建立 C Callback
        # ----------------------------------------------------

        @OQS_RANDOM_CALLBACK
        def random_callback(
            output_buffer,
            bytes_to_read
        ):

            try:

                # C size_t → Python int
                length = int(bytes_to_read)

                # --------------------------------------------
                # 向我們的 Provider 要求亂數
                # --------------------------------------------

                random_data = (
                    cls._provider.get_random_bytes(
                        length
                    )
                )

                # --------------------------------------------
                # 再次確認長度
                # --------------------------------------------

                if len(random_data) != length:

                    raise RuntimeError(
                        "Random provider returned "
                        "incorrect number of bytes"
                    )


                # --------------------------------------------
                # Python bytes → C memory
                # --------------------------------------------

                ct.memmove(
                    output_buffer,
                    random_data,
                    length
                )


            except Exception as error:

                # ------------------------------------------------
                # liboqs custom RNG callback 本身沒有
                # return error 的機制。
                #
                # 因此先記錄錯誤，
                # 並清零 output buffer。
                #
                # 上層操作結束後一定要呼叫
                # raise_if_error()。
                # ------------------------------------------------

                cls._thread_state.error = error

                ct.memset(
                    output_buffer,
                    0,
                    int(bytes_to_read)
                )


        # ----------------------------------------------------
        # 保存 callback
        #
        # 非常重要：
        # 避免 Python GC 回收 callback。
        # ----------------------------------------------------

        cls._callback = random_callback


        # ----------------------------------------------------
        # 取得 liboqs native library
        # ----------------------------------------------------

        native = oqs.native()


        # 告訴 ctypes C function 的參數格式
        native.OQS_randombytes_custom_algorithm.argtypes = [
            OQS_RANDOM_CALLBACK
        ]

        # C function 沒有回傳值
        native.OQS_randombytes_custom_algorithm.restype = None


        # ----------------------------------------------------
        # 將 Python Callback 註冊進 liboqs
        # ----------------------------------------------------

        native.OQS_randombytes_custom_algorithm(
            cls._callback
        )


    # ========================================================
    # Error Handling
    # ========================================================

    @classmethod
    def clear_error(cls):
        """
        清除之前的 RNG error。
        """

        cls._thread_state.error = None


    @classmethod
    def raise_if_error(cls):
        """
        如果 Random Provider 在 callback 執行期間失敗，
        在 Python 層重新拋出錯誤。

        這避免 PUF 連線失敗時，
        系統卻假裝 KeyGen / Sign 成功。
        """

        error = getattr(
            cls._thread_state,
            "error",
            None
        )

        if error is not None:

            # 清除 error
            cls._thread_state.error = None

            raise RuntimeError(
                f"Custom RNG failed: {error}"
            )