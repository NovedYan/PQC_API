# Python 內建的 HTTP Server
# 不需要另外安裝 Flask / Django
from http.server import BaseHTTPRequestHandler, HTTPServer

# JSON 編碼與解碼
import json

# Base64 編碼
import base64

# 暫時用作模擬 PUF 亂數
import os


# ============================================================
# Mock PUF HTTP Handler
# ============================================================

class MockPUFHandler(BaseHTTPRequestHandler):
    """
    模擬未來資工系提供的 PUF Random REST API。

    注意：
    這不是真正的 PUF。

    現階段只是使用 os.urandom()
    模擬資工系回傳的 PUF-derived random bytes。

    API:

        POST /api/random/

    Request:

        {
            "length": 32
        }

    Response:

        {
            "random": "Base64 encoded data",
            "length": 32
        }
    """

    def do_POST(self):

        # ----------------------------------------------------
        # 1. 檢查 API Path
        # ----------------------------------------------------

        if self.path != "/api/random/":

            self.send_error(
                404,
                "API endpoint not found"
            )

            return


        # ----------------------------------------------------
        # 2. 取得 Request Body 長度
        # ----------------------------------------------------

        content_length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )


        # ----------------------------------------------------
        # 3. 讀取 Request Body
        # ----------------------------------------------------

        request_body = self.rfile.read(
            content_length
        )


        # ----------------------------------------------------
        # 4. JSON Decode
        # ----------------------------------------------------

        try:

            request_data = json.loads(
                request_body.decode("utf-8")
            )

        except Exception:

            self.send_json(
                {
                    "error": "Invalid JSON"
                },
                status=400
            )

            return


        # ----------------------------------------------------
        # 5. 取得 length
        # ----------------------------------------------------

        length = request_data.get("length")


        # ----------------------------------------------------
        # 6. 驗證 length
        # ----------------------------------------------------

        if not isinstance(length, int):

            self.send_json(
                {
                    "error": "length must be an integer"
                },
                status=400
            )

            return


        if length <= 0:

            self.send_json(
                {
                    "error": "length must be greater than 0"
                },
                status=400
            )

            return


        # ----------------------------------------------------
        # 7. 模擬 PUF 產生指定長度的 bytes
        # ----------------------------------------------------

        # TODO:
        # 未來這一部分就是資工系真正的：
        #
        # PUF
        #  ↓
        # Response Processing
        #  ↓
        # Random Bytes
        #
        
        # 現階段先用 OS Random 模擬。
        # 顯示目前收到的 Random Request
        # 這可以幫助我們確認 ML-DSA 是否真的呼叫 PUF。
        print(
            f"[PUF REQUEST] Client requested {length} bytes"
        )

        # 暫時使用 OS Random 模擬真正的 PUF
        random_bytes = os.urandom(length)


        # ----------------------------------------------------
        # 8. bytes → Base64
        # ----------------------------------------------------

        random_b64 = base64.b64encode(
            random_bytes
        ).decode("utf-8")


        # ----------------------------------------------------
        # 9. 回傳 JSON
        # ----------------------------------------------------

        response = {
            "random": random_b64,
            "length": len(random_bytes)
        }

        self.send_json(
            response,
            status=200
        )


    # ========================================================
    # JSON Response Helper
    # ========================================================

    def send_json(
        self,
        data,
        status=200
    ):
        """
        將 Python dict 轉成 JSON HTTP Response。
        """

        response_body = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response_body))
        )

        self.end_headers()

        self.wfile.write(
            response_body
        )


# ============================================================
# Server Entry Point
# ============================================================

if __name__ == "__main__":

    HOST = "127.0.0.1"

    # 使用 9000 Port
    # 避免跟 Django 的 8000 Port 衝突
    PORT = 9000

    server = HTTPServer(
        (HOST, PORT),
        MockPUFHandler
    )

    print("===================================")
    print("Mock PUF Server")
    print("===================================")

    print(
        f"Running at:"
        f" http://{HOST}:{PORT}/api/random/"
    )

    print(
        "Press Ctrl+C to stop."
    )

    server.serve_forever()