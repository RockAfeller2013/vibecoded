# YouTube Music Downloader

A simple Python script to download music from YouTube as MP3 files. Provide a text file with song titles, and the script will search YouTube, download the audio, and convert it to MP3 format.

## Features

- 🎵 Downloads audio from YouTube and converts to MP3
- 📝 Batch download multiple songs from a text file
- 🔍 Automatic YouTube search for each song
- 🔄 Retry mechanism for failed downloads
- 📊 Progress tracking
- 🧹 Automatic cleanup of unwanted files

## Prerequisites

### 1. Python 3.7 or higher
Check your Python version:
```bash
python3 --version
```

### 2. FFmpeg
FFmpeg is required for audio conversion to MP3.

**On macOS:**
```bash
brew install ffmpeg
```

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**On Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add FFmpeg to your system PATH

**Verify installation:**
```bash
ffmpeg -version
```

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
```bash
pip3 install -r requirements.txt
```

Or install manually:
```bash
pip3 install yt-dlp
```

## Usage

### 1. Create a text file with song titles

Create a file (e.g., `songs.txt`) with one song title per line:

```text
Bohemian Rhapsody
Stairway to Heaven
Hotel California
Sweet Child O' Mine
Imagine
```

### 2. Run the script

```bash
python3 down.py songs.txt
```

### 3. Find your downloads

Downloaded MP3 files will be saved in the `output_music` folder.

## Example

```bash
$ python3 down.py my_playlist.txt

📥 Downloading 5 songs from my_playlist.txt...

[1/5] 🔍 Searching: Bohemian Rhapsody official audio
[download] Destination: output_music/Queen - Bohemian Rhapsody.m4a
[download] 100% of 5.23MiB in 00:02
[ExtractAudio] Destination: output_music/Queen - Bohemian Rhapsody.mp3

[2/5] 🔍 Searching: Stairway to Heaven official audio
...

✅ Download complete!
```

## Configuration

You can modify the script's download settings in the `ydl_opts` dictionary:

```python
ydl_opts = {
    'format': 'bestaudio/best',  # Download best quality audio
    'preferredquality': '192',    # MP3 bitrate (128, 192, 256, 320)
}
```

### Quality Options

Change `'preferredquality'` to:
- `'128'` - Lower quality, smaller files
- `'192'` - Good quality (default)
- `'256'` - High quality
- `'320'` - Maximum quality, larger files

## File Structure

```
.
├── down.py              # Main script
├── requirements.txt     # Python dependencies
├── songs.txt           # Your song list (example)
└── output_music/       # Downloaded MP3s (auto-created)
    ├── Song1.mp3
    ├── Song2.mp3
    └── ...
```

## Troubleshooting

### "FFmpeg is not installed"
- Make sure FFmpeg is installed and in your system PATH
- Run `ffmpeg -version` to verify

### "No video formats found"
- The song might not be available on YouTube
- Try adding more specific search terms to your song title
- Check your internet connection

### Downloads are slow
- This depends on your internet speed and YouTube's servers
- Downloads run sequentially (one at a time)

### Wrong song downloaded
- Be more specific in your song titles
- Include artist name: `Artist Name - Song Title`
- Example: `Queen - Bohemian Rhapsody` instead of just `Bohemian Rhapsody`

### File already exists
- The script will overwrite existing files with the same name
- Delete or rename existing files if you want to keep them

## Tips

### Better Search Results

Include artist names for more accurate results:
```text
Queen - Bohemian Rhapsody
Led Zeppelin - Stairway to Heaven
Eagles - Hotel California
```

### Skip Already Downloaded Songs

Before running the script, you can manually remove songs from your text file that you've already downloaded.

## Legal Notice

⚠️ **Important:** Only download content you have the right to download. Respect copyright laws and YouTube's Terms of Service. This tool is intended for:
- Downloading your own content
- Downloading content with appropriate permissions
- Personal archival of legally obtained content

## License

This script is provided as-is for educational purposes.

## Contributing

Feel free to submit issues or pull requests for improvements!

## Credits

- Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Requires [FFmpeg](https://ffmpeg.org/)
