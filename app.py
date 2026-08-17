import os
import sys
import binascii
import requests
from flask import Flask, request, Response

# ------------------------------------------------------------
# Static /GetFriend response (hex -> bytes)
# ------------------------------------------------------------
STATIC_GETFRIEND_HEX = (
    "0a6408cff1acd70210011a19c681ca99e1b49be385a4c6acca9ce1b480e1b48be1b49cca803203494e44405f488cde980bb001f6d7d0ad03b80192a68fae03e00192a68fae03f8018f018002a399a8dd039802beb98bd406980398e0fde205c20304100118010a6d0896aa883610011a20e1b59de1b592cba2cba2efbca1efbcb9efbcb5efbcb3efbca8e385a4c6b3c6ac3203494e44405848e0b6e206b001d4d6d0ad03b801cadb8dae03e001cadb8dae03f801b4018002a399a8dd039002019802b3b68bd4069803e8d9dfd405c20304100118010a5c08e3d5c01d10011a104b4152414ee385a4474d52efa3bf21213203494e44405448bfe2ce04b001c9d6d0ad03b801a7fc8fae03e001a7fc8fae03f801548002a399a8dd039002019802bfa98bd4069803aedc9ad305c20304100118010a6c08c9ce9a0e10011a22e18f92ceb5e1b4a0eaab9dcdb7e385a4e0ae9ae0aea4e0af80e0aeb7e0af8defa3bf3203494e44405548c6849f05b001d5d6d0ad03b8018bdb8dae03e0018bdb8dae03f80187018002a399a8dd039802f2cd8bd4069803f48383d205c20304100118010a5a08ffd2ddc00110011a0d48d19454e385a4efa3bfe385a43203494e44405648dbe8c005b001c9d6d0ad03b801c0dc8dae03e001c0dc8dae03f801628002a399a8dd0390020198029da88bd406980389f693dd05c20304100118010a5d08828e97e00210011a13c6a6c6a6e385a4ce9bca9fe1b48778efa3bf2e3203494e44405a4895f9fa07b001cea9d2ad03b801c0dc8dae03e001c0dc8dae03f8015c8002a399a8dd039802a8b18bd4069803c8b4a4e305c20304100118010a5b08feac8ec30610011a0e524959415ae385a4e0bc8fe0bc8f3203494e44404c48dbe0a802b001bdd8d0ad03b801acdb8dae03e001acdb8dae03f801428002a399a8dd039002019802ddc585d4069803a0d3a4f105c20304100118010a59089689fc941d10011a0f464de385a44e4557544f4ee385a4213203494e44404c48fbdbb302b001d1a9d2ad03b8018dae8fae03e0018dae8fae03f801658002a399a8dd039802ecbd8bd4069803b0fee8a306c20304100118010a5d08d3c189e50210011a10564950e385a4504156494ee385a438343203494e44405748b88bf405b001cda9d2ad03b801cadb8dae03e001cadb8dae03f801468002a399a8dd03900201980298d08ad40698038fc5bae305c20304100118010a6908ef99ba1a10011a1fe18f95e1b48be1ad84e18f95e1b480ca99c9aaca80e1b4aee1b592cba2cba23203494e44406348bdc4bf0eb001d2a9d2ad03b8019af990ae03e0019af990ae03f801bb038002a399a8dd039802a6bb8ad4069803c5b481d305c2030410011801"
)
STATIC_GETFRIEND = bytes.fromhex(STATIC_GETFRIEND_HEX)

REAL_HOST = "client.ind.freefiremobile.com"
REAL_BASE = f"https://{REAL_HOST}"

# Toggle: set to "static" or "forward" via env var FORWARD_GETFRIEND
FORWARD_MODE = os.environ.get("GETFRIEND_MODE", "static").lower()

app = Flask(__name__)

# Simple stdout logging (visible in Vercel logs)
def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
def proxy(path):
    full_path = request.full_path if request.query_string else path
    if not full_path.startswith("/"):
        full_path = "/" + full_path

    log(f"--> {request.method} {full_path}")

    # ---------------------------------------------
    # /GetFriend – static or forwarded
    # ---------------------------------------------
    if full_path == "/GetFriend":
        if FORWARD_MODE == "forward":
            log("  => Forwarding /GetFriend to real server")
            return forward_request(full_path)
        else:
            log("  => Serving static /GetFriend response")
            # Mimic real server headers (as seen in /GetLoginData logs)
            return Response(
                STATIC_GETFRIEND,
                status=200,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(STATIC_GETFRIEND)),
                    "Connection": "close"
                }
            )

    # ---------------------------------------------
    # All other endpoints – forward to real server
    # ---------------------------------------------
    return forward_request(full_path)

def forward_request(full_path):
    real_url = REAL_BASE + full_path
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("content-length", "connection", "transfer-encoding", "host")}
    data = request.get_data()

    try:
        resp = requests.request(
            method=request.method,
            url=real_url,
            headers=headers,
            data=data,
            timeout=15,
            verify=True
        )
        log(f"<-- {real_url} -> {resp.status_code} ({len(resp.content)} bytes)")
        # Build response (strip hop-by-hop headers)
        excluded = ("content-length", "connection", "transfer-encoding")
        response_headers = [(k, v) for k, v in resp.raw.headers.items() if k.lower() not in excluded]
        return Response(resp.content, status=resp.status_code, headers=response_headers)
    except Exception as e:
        log(f"!! Proxy error: {e}")
        return Response(f"Proxy error: {e}", status=502, mimetype="text/plain")

if __name__ == "__main__":
    # For local testing – run with `python app.py`
    app.run(host="0.0.0.0", port=8080)
