# MP3 Popularity Sorter

Sort your MP3 files by Spotify popularity. This script reads ID3 tags from your MP3 files, queries the Spotify API for popularity scores, and renames files with a numeric prefix based on their ranking.

## Features

- ✅ Reads ID3 tags (title, artist) for accurate track matching
- ✅ Queries Spotify API for popularity scores (0-100)
- ✅ Dry-run mode to preview changes before applying
- ✅ Detailed logging with progress information
- ✅ Rate limiting to avoid API throttling
- ✅ Handles files without ID3 tags (falls back to filename)
- ✅ Collision-safe renaming

## Prerequisites

- Python 3.7 or higher
- Spotify Developer Account (free)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account (or create one)
3. Click "Create an App"
4. Fill in the app name and description (e.g., "MP3 Sorter")
5. Accept the terms and click "Create"
6. You'll see your **Client ID** and **Client Secret**

### 3. Set Environment Variables

#### On Linux/Mac:

```bash
export SPOTIPY_CLIENT_ID="your_client_id_here"
export SPOTIPY_CLIENT_SECRET="your_client_secret_here"
```

To make these permanent, add them to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export SPOTIPY_CLIENT_ID="your_client_id_here"' >> ~/.bashrc
echo 'export SPOTIPY_CLIENT_SECRET="your_client_secret_here"' >> ~/.bashrc
source ~/.bashrc
```

#### On Windows (Command Prompt):

```cmd
set SPOTIPY_CLIENT_ID=your_client_id_here
set SPOTIPY_CLIENT_SECRET=your_client_secret_here
```

#### On Windows (PowerShell):

```powershell
$env:SPOTIPY_CLIENT_ID="your_client_id_here"
$env:SPOTIPY_CLIENT_SECRET="your_client_secret_here"
```

To make these permanent on Windows, set them as System Environment Variables through Control Panel.

## Usage

### Basic Usage

```bash
python sort_mp3_by_popularity.py /path/to/your/music/folder
```

### Dry Run (Recommended First!)

Preview what will be renamed without making any changes:

```bash
python sort_mp3_by_popularity.py /path/to/your/music/folder --dry-run
```

### Verbose Mode

Get detailed debug information:

```bash
python sort_mp3_by_popularity.py /path/to/your/music/folder --verbose
```

### Custom Rate Limiting

Adjust the delay between API requests (default is 0.1 seconds):

```bash
python sort_mp3_by_popularity.py /path/to/your/music/folder --rate-limit 0.2
```

### Combined Options

```bash
python sort_mp3_by_popularity.py /path/to/your/music/folder --dry-run --verbose
```

## How It Works

1. **Scans** the specified folder for MP3 files
2. **Reads ID3 tags** (title and artist) from each file
3. **Searches Spotify** using the track title and artist
4. **Retrieves popularity score** (0-100, where 100 is most popular)
5. **Sorts tracks** by popularity (highest first)
6. **Renames files** with a 5-digit prefix (e.g., `00001_song.mp3`, `00002_song.mp3`)
7. **Places unmatched tracks** at the end, sorted alphabetically

## Example Output

```
2025-01-11 10:30:15 - INFO - Found 10 MP3 file(s)
------------------------------------------------------------
2025-01-11 10:30:15 - INFO - [1/10] Processing: song1.mp3
2025-01-11 10:30:15 - INFO - ✓ Found: Artist Name - Song Title (popularity: 85)
2025-01-11 10:30:16 - INFO - [2/10] Processing: song2.mp3
2025-01-11 10:30:16 - INFO - ✓ Found: Another Artist - Another Song (popularity: 72)
...
------------------------------------------------------------
2025-01-11 10:30:25 - INFO - 
Ranking Summary:
  Tracks with popularity: 8
  Tracks without popularity: 2
  Total: 10
------------------------------------------------------------
2025-01-11 10:30:25 - INFO - ✓ Renamed: song1.mp3
2025-01-11 10:30:25 - INFO -        to: 00001_song1.mp3 (popularity: 85)
...
```

## File Naming

Files are renamed with a 5-digit numeric prefix:

- `00001_song.mp3` - Most popular track
- `00002_song.mp3` - Second most popular
- ...
- `00009_song.mp3` - Least popular (with data)
- `00010_song.mp3` - No popularity data (alphabetical)

## Troubleshooting

### "Spotify credentials not found"

Make sure you've set the environment variables correctly:

```bash
echo $SPOTIPY_CLIENT_ID
echo $SPOTIPY_CLIENT_SECRET
```

Both should output your credentials. If they're empty, refer to the installation section.

### "No ID3 tags found"

Some MP3 files don't have ID3 tags. The script will fall back to using the filename for searching, but results may be less accurate. Consider using a tool like [MusicBrainz Picard](https://picard.musicbrainz.org/) to add proper ID3 tags.

### Tracks not found on Spotify

- Ensure your MP3 files have accurate ID3 tags
- Some tracks may not be available on Spotify
- Local/unreleased tracks won't have popularity data

### Rate limiting errors

If you get rate limit errors, increase the delay:

```bash
python sort_mp3_by_popularity.py /path/to/folder --rate-limit 0.5
```

## Important Notes

⚠️ **Always run with `--dry-run` first** to preview changes before actually renaming files.

⚠️ **Backup your files** before running the script, especially on important music libraries.

⚠️ The script **does not modify** the actual MP3 files or their ID3 tags, only the filenames.

## Requirements File Contents

The script requires these Python packages (see `requirements.txt`):

- `spotipy` - Spotify API wrapper
- `mutagen` - MP3 ID3 tag reading

## License

This script is provided as-is for personal use. Spotify API usage is subject to [Spotify's Terms of Service](https://developer.spotify.com/terms).

## Contributing

Feel free to submit issues or pull requests for improvements!
