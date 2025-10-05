import os
import re
from urllib.parse import unquote
from flask import Flask, request, jsonify
import requests
import yt_dlp
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ----------------------------------
# CONFIG: put your proxy string here
# ----------------------------------
# Example formats:
#   HTTP proxy:  "http://username:password@1.2.3.4:8080"
#   SOCKS5 proxy: "socks5://username:password@1.2.3.4:1080"
# If you prefer, set PROXY via environment variable PROXY_STRING and leave this blank.
PROXY = os.environ.get("PROXY_STRING", "") or "http://cjillzpc:gmnxgwo6ij8e@64.137.96.74:6641"
# ----------------------------------

# Build proxies dict for requests
REQUESTS_PROXIES = {"http": PROXY, "https": PROXY} if PROXY else None

# Helper to sanitize filename/title
def sanitize_title(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", title or "untitled")

@app.route("/process", methods=["POST"])
def process():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "invalid_json", "details": str(e)}), 400

    video_url = unquote((data or {}).get("video_url", "") or "")
    chanbox_url = (data or {}).get("chanbox_url", "")

    if not video_url or not chanbox_url:
        return jsonify({"error": "missing_parameters", "details": "video_url and chanbox_url are required"}), 400

    logging.info("Processing video_url=%s chanbox_url=%s via proxy=%s", video_url, chanbox_url, bool(PROXY))

    # Step 1: Extract metadata with yt-dlp using the single proxy (if set)
    try:
        ydl_opts = {"skip_download": True, "quiet": True, "no_warnings": True}
        if PROXY:
            # yt-dlp accepts 'proxy' option
            ydl_opts["proxy"] = PROXY

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            thumbnail_url = info.get("thumbnail")
            title = info.get("title", "untitled")
    except Exception as e:
        logging.exception("yt-dlp extract failed")
        return jsonify({"error": "yt_dlp_failed", "details": str(e)}), 502

    safe_title = sanitize_title(title)

    # Step 2: Optionally verify chanbox_url reachable using same proxy
    chanbox_status = None
    try:
        if REQUESTS_PROXIES:
            resp = requests.get(chanbox_url, proxies=REQUESTS_PROXIES, timeout=10)
        else:
            resp = requests.get(chanbox_url, timeout=10)
        chanbox_status = {"status_code": resp.status_code}
    except Exception as e:
        logging.exception("chanbox check failed")
        chanbox_status = {"error": str(e)}

    # Build response
    payload = {
        "video_title": title,
        "safe_title": safe_title,
        "thumbnail_url": thumbnail_url,
        "chanbox_url": chanbox_url,
        "proxy_used": PROXY if PROXY else None,
        "chanbox_check": chanbox_status,
    }

    return jsonify(payload), 200


if __name__ == "__main__":
    # Run dev server. For production use gunicorn/uvicorn.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
