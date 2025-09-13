import yt_dlp
import requests
import re
import json
import sys

# Default (for testing)
VIDEO_URL = "https://www.pornhub.com/view_video.php?viewkey=ph62178dca8c65e"
CHANBOX_URL = "https://chanbox.app/video/sample"
WEBHOOK_URL = "https://greekgod.app.n8n.cloud/webhook-test/a5c8b1da-8ee5-4929-ac5d-36ca11cebe9a"

# ------------------------------
# Accept dynamic inputs (from n8n / Google Sheets)
# sys.argv[1] = VIDEO_URL
# sys.argv[2] = CHANBOX_URL
# ------------------------------
if len(sys.argv) > 1:
    VIDEO_URL = sys.argv[1]
if len(sys.argv) > 2:
    CHANBOX_URL = sys.argv[2]

print("Processing Video URL:", VIDEO_URL)
print("Chanbox URL:", CHANBOX_URL)

# Step 1: Extract metadata (including thumbnail)
ydl_opts = {'skip_download': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(VIDEO_URL, download=False)
    thumbnail_url = info.get('thumbnail')
    video_title = info.get('title')
    print("Video Title:", video_title)
    print("Thumbnail URL:", thumbnail_url)

# Step 2: Sanitize video title for filename
safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_title)
output_file = f"{safe_title}.jpg"

# Step 3: Download thumbnail image locally (optional — can be skipped)
if thumbnail_url:
    response = requests.get(thumbnail_url)
    with open(output_file, "wb") as f:
        f.write(response.content)
    print("Saved Thumbnail as:", output_file)

# Step 4: Send data to n8n webhook
payload = {
    "video_title": video_title,
    "thumbnail_url": thumbnail_url,
    "chanbox_url": CHANBOX_URL
}

response = requests.post(WEBHOOK_URL, json=payload)
if response.ok:
    print("Webhook sent successfully!")
else:
    print("Failed to send webhook:", response.text)
