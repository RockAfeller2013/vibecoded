# pip install yt-dlp
# python download_fb.py https://www.facebook.com/reel/801096865803336

import sys
import yt_dlp

def download_facebook_video(url: str, output_path: str = "."):
    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "format": "best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_fb.py <facebook_video_url> [output_path]")
        sys.exit(1)

    video_url = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else "."
    download_facebook_video(video_url, path)
