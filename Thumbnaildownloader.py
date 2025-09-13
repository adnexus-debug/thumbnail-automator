import os
from flask import Flask, request, jsonify
import yt_dlp
import requests
import re

app = Flask(__name__)

# Set this in Replit Secrets as N8N_WEBHOOK_URL
WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "")

@app.route("/process", methods=["GET", "POST"])
def process():
    # accept JSON body or form/query params
    if request.is_json:
        data = request.get_json()
    else:
        data = request.values

    video_url = data.get("video_url")
    chanbox_url = data.get("chanbox_url")

    if not video_url or not chanbox_url:
        return jsonify({"error": "Provide video_url and chanbox_url"}), 400

    try:
        ydl_opts = {'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        thumbnail_url = info.get('thumbnail')
        video_title = info.get('title')
    except Exception as e:
        return jsonify({"error": "yt-dlp failed", "details": str(e)}), 500

    payload = {
        "video_title": video_title,
        "thumbnail_url": thumbnail_url,
        "chanbox_url": chanbox_url
    }

    if not WEBHOOK_URL:
        # for quick testing, return the payload instead of posting
        return jsonify({"status": "no_webhook_configured", "payload": payload}), 200

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": "Failed to call n8n webhook", "details": str(e)}), 500

    return jsonify({"status": "ok", "payload": payload}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    # enable reloader in dev; Replit manages process in production
    app.run(host="0.0.0.0", port=port)
