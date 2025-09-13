from flask import Flask, request, jsonify
import yt_dlp
import requests
import re

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    video_url = data.get("video_url")
    chanbox_url = data.get("chanbox_url")

    if not video_url or not chanbox_url:
        return jsonify({"error": "Missing video_url or chanbox_url"}), 400

    # Step 1: Extract metadata
    ydl_opts = {'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        thumbnail_url = info.get('thumbnail')
        video_title = info.get('title')

    # Step 2: Clean title
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_title)

    # Step 3: Send data to n8n webhook (optional)
    payload = {
        "video_title": video_title,
        "thumbnail_url": thumbnail_url,
        "chanbox_url": chanbox_url
    }

    return jsonify(payload), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
