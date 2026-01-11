import sys
from pathlib import Path
from yt_dlp import YoutubeDL
import shutil

# Check for FFmpeg
if not shutil.which('ffmpeg'):
    print("❌ FFmpeg is not installed. Please install it first.")
    sys.exit(1)

if len(sys.argv) != 2:
    print("Usage: python3 down.py <filename.txt>")
    sys.exit(1)

input_file = Path(sys.argv[1])
if not input_file.exists():
    print(f"❌ File not found: {input_file}")
    sys.exit(1)

output_folder = Path("output_music")
output_folder.mkdir(exist_ok=True)

def download_song(ydl, query):
    try:
        ydl.download([query])
        return True
    except Exception as e:
        print(f"❌ Failed to download '{query}': {e}")
        return False

def cleanup_mhtml_files(folder):
    removed = False
    for file in folder.glob("*.mhtml"):
        print(f"⚠️ Removing unwanted .mhtml file: {file.name}")
        file.unlink()
        removed = True
    return removed

def extract_song_title(line):
    """
    Extract song title from either:
    - A file path: /Volumes/music/Feel/Song Name.mp3
    - A plain song title: Song Name
    
    Returns the song title without extension.
    """
    line = line.strip()
    if not line:
        return None
    
    # If it looks like a file path, extract the filename
    if '/' in line or '\\' in line:
        # Get the filename from the path
        path = Path(line)
        # Get stem (filename without extension)
        return path.stem
    else:
        # Plain text, just strip and return
        return line

# Load song titles from file
with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

song_titles = []
for line in lines:
    title = extract_song_title(line)
    if title:
        song_titles.append(title)

if not song_titles:
    print("❌ No valid song titles found in the input file.")
    sys.exit(1)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': str(output_folder / '%(title)s.%(ext)s'),
    'noplaylist': True,
    'quiet': False,
    'default_search': 'ytsearch1:',
    'ignoreerrors': True,
    'no_warnings': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

with YoutubeDL(ydl_opts) as ydl:
    print(f"📥 Downloading {len(song_titles)} songs from {input_file}...")
    
    for i, title in enumerate(song_titles, 1):
        query = f"{title} official audio"
        print(f"\n[{i}/{len(song_titles)}] 🔍 Searching: {query}")
        
        success = download_song(ydl, query)
        if not success:
            continue
        
        if cleanup_mhtml_files(output_folder):
            retry_query = f"{title} audio only"
            print(f"🔄 Retrying with fallback query: {retry_query}")
            download_song(ydl, retry_query)
            cleanup_mhtml_files(output_folder)

print("\n✅ Download complete!")
