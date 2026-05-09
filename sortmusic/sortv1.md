---

## Requirements

- Python 3.8+
- A free [Spotify Developer](https://developer.spotify.com/dashboard) account

### Install dependencies

```bash
pip install spotipy mutagen
```

---

## Setup

### 1. Get Spotify API credentials

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Copy your **Client ID** and **Client Secret**

### 2. Set environment variables

**macOS / Linux**
```bash
export SPOTIPY_CLIENT_ID="your_client_id_here"
export SPOTIPY_CLIENT_SECRET="your_client_secret_here"
```

**Windows — Command Prompt**
```cmd
set SPOTIPY_CLIENT_ID=your_client_id_here
set SPOTIPY_CLIENT_SECRET=your_client_secret_here
```

**Windows — PowerShell**
```powershell
$env:SPOTIPY_CLIENT_ID="your_client_id_here"
$env:SPOTIPY_CLIENT_SECRET="your_client_secret_here"
```

> **Tip:** Add these lines to your `~/.bashrc`, `~/.zshrc`, or Windows Environment Variables so you don't have to set them every session.

---

## Usage

### Basic — rename files in place
```bash
python sort_mp3_by_popularity.py /path/to/your/music
```

### Dry run — preview only, nothing is changed
```bash
python sort_mp3_by_popularity.py /path/to/your/music --dry-run
```

### Safe mode — copy renamed files to a new folder, originals untouched
```bash
python sort_mp3_by_popularity.py /path/to/your/music --output-dir /path/to/sorted
```

### Verbose — show debug info including every Spotify query sent
```bash
python sort_mp3_by_popularity.py /path/to/your/music --verbose
```

### Custom rate limit — useful for large libraries
```bash
python sort_mp3_by_popularity.py /path/to/your/music --rate-limit 1.0
```

### Combine flags
```bash
# Preview with full debug output
python sort_mp3_by_popularity.py /path/to/music --dry-run --verbose

# Safe copy with slower rate limit
python sort_mp3_by_popularity.py /path/to/music --output-dir ~/sorted --rate-limit 1.0
```

---

## All Options

| Flag | Default | Description |
|---|---|---|
| `folder` | *(required)* | Path to the folder containing your MP3 files |
| `--dry-run` | off | Preview renames without touching any files |
| `--output-dir DIR` | off | Copy renamed files to `DIR` instead of renaming in place |
| `--verbose` | off | Enable debug logging (shows every Spotify query) |
| `--rate-limit N` | `0.5` | Seconds to wait between Spotify API requests |

---

## Output Example
