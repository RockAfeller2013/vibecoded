#!/usr/bin/env python3
"""
Create an M3U/M3U8 playlist of MP3s sorted by Spotify popularity,
using parallel lookups and fuzzy matching for maximum accuracy and speed.
Files are never renamed or moved — only a playlist file is written.

# Quick run: 4 parallel workers, default fuzzy threshold 75
python sort_mp3_to_playlist.py /path/to/music --workers 4

# More aggressive parallelism (respects --rate-limit)
python sort_mp3_to_playlist.py /path/to/music --workers 10 --rate-limit 0.2

# Stricter matching (only very high confidence hits)
python sort_mp3_to_playlist.py /path/to/music --match-threshold 90

"""

import os
import sys
import time
import json
import logging
import argparse
import re
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Friendly import checks
# ---------------------------------------------------------------------------
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    sys.exit(
        "The 'spotipy' package is required.\n"
        "Install it with: pip install spotipy"
    )

try:
    from mutagen.mp3 import MP3
except ImportError:
    sys.exit(
        "The 'mutagen' package is required.\n"
        "Install it with: pip install mutagen"
    )

try:
    from rapidfuzz import fuzz
except ImportError:
    sys.exit(
        "The 'rapidfuzz' package is required for fuzzy matching.\n"
        "Install it with: pip install rapidfuzz"
    )

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FILENAME_NOISE_RE = re.compile(
    r"\[.*?\]|\(.*?\)|\d{3,4}\s*kbps|official\s*(audio|video|lyric)",
    flags=re.IGNORECASE,
)
CACHE_FILENAME = ".spotify_popularity_cache.json"

# Number of top Spotify search results to compare with fuzzy matching
SPOTIFY_SEARCH_LIMIT = 5
# Default minimum fuzzy match score (0-100) to accept a track
DEFAULT_MATCH_THRESHOLD = 75

# ---------------------------------------------------------------------------
# Rate limiter for parallel API calls
# ---------------------------------------------------------------------------
class RateLimiter:
    """Ensure a minimum interval between consecutive API calls, even across threads."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self.lock = threading.Lock()
        self.last_call = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            wait_time = self.min_interval - (now - self.last_call)
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_call = time.monotonic()

# ---------------------------------------------------------------------------
# Spotify client
# ---------------------------------------------------------------------------
def get_spotify_client() -> Optional[spotipy.Spotify]:
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.error("Missing Spotify credentials.")
        logger.error("Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET env vars.")
        return None
    try:
        auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        return spotipy.Spotify(auth_manager=auth)
    except Exception as e:
        logger.error(f"Failed to initialise Spotify client: {e}")
        return None

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------
def load_cache(folder: Path) -> Dict[str, Any]:
    cache_path = folder / CACHE_FILENAME
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            logger.info(f"Cache loaded — {len(data)} entries from {cache_path.name}")
            return data
        except Exception as e:
            logger.warning(f"Could not read cache: {e}")
    return {}

def save_cache(folder: Path, cache: Dict[str, Any]) -> None:
    try:
        with (folder / CACHE_FILENAME).open("w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=2)
    except Exception as e:
        logger.warning(f"Could not write cache: {e}")

# ---------------------------------------------------------------------------
# ID3 helpers
# ---------------------------------------------------------------------------
def get_track_info_from_id3(file_path: Path) -> Tuple[Optional[str], Optional[str], int]:
    try:
        audio = MP3(str(file_path))
        duration = int(audio.info.length) if audio.info else 0
        if audio.tags is None:
            logger.warning(f"No ID3 tags: {file_path.name}")
            return None, None, duration
        title = str(audio.tags.get("TIT2", "")).strip() or None
        artist = str(audio.tags.get("TPE1", "")).strip() or None
        return title, artist, duration
    except Exception as e:
        logger.warning(f"Error reading {file_path.name}: {e}")
        return None, None, 0

# ---------------------------------------------------------------------------
# Spotify lookup (fuzzy)
# ---------------------------------------------------------------------------
def _clean_filename(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = FILENAME_NOISE_RE.sub("", stem)
    return re.sub(r"\s{2,}", " ", cleaned).strip()

def _fuzzy_score(query: str, track_name: str, track_artist: str) -> float:
    """Return a 0-100 similarity score between query artist+title and track."""
    # Combine track name and artist for comparison
    track_str = f"{track_artist} {track_name}".lower()
    return fuzz.token_sort_ratio(query.lower(), track_str)

def _search_spotify(sp: spotipy.Spotify, query: str) -> List[dict]:
    """Search Spotify (up to 3 retries with backoff) and return a list of track dicts."""
    for attempt in range(3):
        try:
            result = sp.search(q=query, type="track", limit=SPOTIFY_SEARCH_LIMIT)
            return result.get("tracks", {}).get("items", [])
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                wait = int(getattr(e, "headers", {}).get("Retry-After", 5))
                logger.warning(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                logger.error(f"Spotify error: {e}")
                return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    return []

def get_best_spotify_match(
    sp: spotipy.Spotify,
    title: Optional[str],
    artist: Optional[str],
    filename: str,
    threshold: int = DEFAULT_MATCH_THRESHOLD,
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Search Spotify using ID3 data (or filename) and return the best fuzzy match.
    Returns (popularity, matched_title, matched_artist) or (None, None, None).
    """
    # Build query string
    if title and artist:
        query = f"track:{title} artist:{artist}"
        raw_query = f"{artist} {title}"
        description = raw_query
    elif title:
        query = f"track:{title}"
        raw_query = title
        description = title
    else:
        query = _clean_filename(filename)
        raw_query = query
        description = query

    if not query.strip():
        logger.warning(f"Could not build a Spotify search query for: {filename}")
        return None, None, None

    # Fetch candidates
    items = _search_spotify(sp, query)
    if not items:
        logger.warning(f"✗ No results: {description}")
        return None, None, None

    # Fuzzy match against each candidate
    best_score = 0
    best_track = None
    for track in items:
        track_name = track.get("name", "")
        track_artist = track["artists"][0]["name"] if track.get("artists") else ""
        score = _fuzzy_score(raw_query, track_name, track_artist)
        if score > best_score:
            best_score = score
            best_track = track

    if best_track and best_score >= threshold:
        pop = best_track.get("popularity")
        t_title = best_track.get("name")
        t_artist = best_track["artists"][0]["name"] if best_track.get("artists") else "Unknown"
        logger.info(f"✓ {t_artist} - {t_title} (popularity: {pop}, score: {best_score})")
        return pop, t_title, t_artist
    else:
        logger.warning(f"✗ No good match (best score {best_score}) for: {description}")
        return None, None, None

# ---------------------------------------------------------------------------
# Processing (parallel)
# ---------------------------------------------------------------------------
def _build_track_dict(
    file_path: Path,
    title: Optional[str],
    artist: Optional[str],
    duration: int,
    popularity: Optional[int],
    spotify_title: Optional[str],
    spotify_artist: Optional[str],
) -> dict:
    return {
        "file_path": file_path,
        "title": title or spotify_title or file_path.stem,
        "artist": artist or spotify_artist or "Unknown",
        "duration": duration,
        "popularity": popularity,
        "spotify_title": spotify_title,
        "spotify_artist": spotify_artist,
    }

def process_files(
    folder: Path,
    sp: spotipy.Spotify,
    rate_limit_delay: float,
    recursive: bool,
    workers: int = 4,
    match_threshold: int = DEFAULT_MATCH_THRESHOLD,
) -> List[dict]:
    """
    Walk the folder, query Spotify in parallel, and return a list of track dicts.
    Cache is used to skip already‑processed files.
    """
    glob_fn = folder.rglob if recursive else folder.glob
    mp3_files = sorted(f for f in glob_fn("*") if f.suffix.lower() == ".mp3")
    if not mp3_files:
        logger.warning("No MP3 files found.")
        return []

    logger.info(f"Found {len(mp3_files)} MP3 file(s)")
    logger.info(f"Using {workers} workers, fuzzy threshold {match_threshold}")
    logger.info("-" * 60)

    cache = load_cache(folder)
    rate_limiter = RateLimiter(rate_limit_delay)

    # Pre‑check cache to skip files we already know
    to_process = []
    for idx, file_path in enumerate(mp3_files, 1):
        cache_key = str(file_path.relative_to(folder))
        if cache_key in cache:
            # We'll build track dict later from cache
            continue
        to_process.append((file_path, cache_key))

    logger.info(f"{len(mp3_files) - len(to_process)} files already cached, {len(to_process)} to query.")
    if not to_process:
        logger.info("All files cached – no Spotify calls needed.")

    # Process uncached files in parallel
    def process_one(file_path, cache_key):
        # Wait for rate limit slot
        rate_limiter.wait()
        # Read ID3 tags (lightweight)
        title, artist, duration = get_track_info_from_id3(file_path)
        # Perform fuzzy Spotify lookup
        popularity, spotify_title, spotify_artist = get_best_spotify_match(
            sp, title, artist, file_path.name, threshold=match_threshold
        )

        entry = {
            "popularity": popularity,
            "duration": duration,
            "spotify_title": spotify_title,
            "spotify_artist": spotify_artist,
            "id3_title": title,
            "id3_artist": artist,
        }
        # Build track dict for immediate return
        track = _build_track_dict(
            file_path, title, artist, duration,
            popularity, spotify_title, spotify_artist,
        )
        return cache_key, entry, track

    # Use ThreadPoolExecutor with limited workers
    new_entries = {}
    processed_tracks = []  # for the ones we just fetched
    if to_process:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_one, fp, ck): (fp, ck) for fp, ck in to_process}
            for future in as_completed(futures):
                try:
                    cache_key, entry, track = future.result()
                    new_entries[cache_key] = entry
                    processed_tracks.append(track)
                except Exception as e:
                    logger.error(f"Worker error: {e}")

        # Update and save cache after all parallel calls
        for cache_key, entry in new_entries.items():
            cache[cache_key] = entry
        save_cache(folder, cache)

    # Now assemble the full track list in original order
    tracks = []
    for file_path in mp3_files:
        cache_key = str(file_path.relative_to(folder))
        if cache_key in cache:
            cached = cache[cache_key]
            id3_title = cached.get("id3_title")
            id3_artist = cached.get("id3_artist")
            # Duration re‑reading if needed
            if "duration" in cached and cached["duration"] > 0:
                duration = cached["duration"]
            else:
                _, _, duration = get_track_info_from_id3(file_path)
            track = _build_track_dict(
                file_path, id3_title, id3_artist,
                duration,
                cached.get("popularity"),
                cached.get("spotify_title"),
                cached.get("spotify_artist"),
            )
        else:
            # Shouldn't happen if we covered all, but just in case
            track = _build_track_dict(file_path, None, None, 0, None, None, None)
        tracks.append(track)

    logger.info("-" * 60)
    return tracks

# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------
def sort_tracks(tracks: List[dict], order: str) -> List[dict]:
    found = [t for t in tracks if t["popularity"] is not None]
    not_found = [t for t in tracks if t["popularity"] is None]
    sign = -1 if order == "desc" else 1
    found.sort(key=lambda t: (
        sign * t["popularity"],
        t["artist"].lower(),
        t["title"].lower(),
    ))
    not_found.sort(key=lambda t: (t["artist"].lower(), t["title"].lower()))
    return found + not_found

# ---------------------------------------------------------------------------
# Playlist writers (unchanged from previous robust version)
# ---------------------------------------------------------------------------
def _relative_path_safe(file_path: Path, anchor: Path) -> str:
    try:
        rel = os.path.relpath(str(file_path.resolve()), str(anchor.resolve()))
    except ValueError:
        logger.warning(
            f"Cannot create relative path for {file_path.name} (different drives); "
            "using absolute path instead."
        )
        rel = str(file_path.resolve())
    return rel.replace("\\", "/")

def _track_path_str(file_path: Path, output_path: Path, use_relative: bool) -> str:
    if use_relative:
        return _relative_path_safe(file_path, output_path.parent)
    return file_path.resolve().as_posix()

def _extinf_line(track: dict, emby_mode: bool) -> str:
    duration = track["duration"] if track["duration"] else -1
    display = f"{track['artist']} - {track['title']}"
    if emby_mode:
        return f"#EXTINF:{duration},{display}"
    pop_tag = (
        f" [popularity: {track['popularity']}]"
        if track["popularity"] is not None
        else " [not on Spotify]"
    )
    return f"#EXTINF:{duration},{display}{pop_tag}"

def write_m3u(
    tracks: List[dict],
    output_path: Path,
    use_relative_paths: bool,
    extended: bool,
    emby_mode: bool = False,
    emby_music_root: Optional[Path] = None,
) -> None:
    with output_path.open("w", encoding="utf-8") as fh:
        if extended:
            fh.write("#EXTM3U\n")
            fh.write(f"# Generated by {os.path.basename(__file__)}\n")
            fh.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"# Tracks: {len(tracks)}\n\n")
        for track in tracks:
            if emby_music_root and use_relative_paths:
                path_str = _relative_path_safe(track["file_path"], emby_music_root)
            else:
                path_str = _track_path_str(track["file_path"], output_path, use_relative_paths)
            if extended:
                if emby_mode:
                    fh.write(f"#EXTART:{track['artist']}\n")
                    pop_comment = (
                        f"# spotify-popularity: {track['popularity']}"
                        if track["popularity"] is not None
                        else "# spotify-popularity: not found"
                    )
                    fh.write(f"{pop_comment}\n")
                fh.write(f"{_extinf_line(track, emby_mode)}\n")
            fh.write(f"{path_str}\n")
    logger.info(f"✓ M3U playlist written: {output_path}")

def write_m3u8(
    tracks: List[dict],
    output_path: Path,
    use_relative_paths: bool,
    emby_mode: bool = False,
    emby_music_root: Optional[Path] = None,
) -> None:
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write("#EXTM3U\n")
        fh.write(f"# Generated by {os.path.basename(__file__)}\n")
        fh.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        fh.write(f"# Tracks: {len(tracks)}\n\n")
        for track in tracks:
            if emby_music_root and use_relative_paths:
                path_str = _relative_path_safe(track["file_path"], emby_music_root)
            else:
                path_str = _track_path_str(track["file_path"], output_path, use_relative_paths)
            if emby_mode:
                fh.write(f"#EXTART:{track['artist']}\n")
                pop_comment = (
                    f"# spotify-popularity: {track['popularity']}"
                    if track["popularity"] is not None
                    else "# spotify-popularity: not found"
                )
                fh.write(f"{pop_comment}\n")
            fh.write(f"{_extinf_line(track, emby_mode)}\n")
            fh.write(f"{path_str}\n")
    logger.info(f"✓ M3U8 playlist written: {output_path}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def print_summary(tracks: List[dict]) -> None:
    found = [t for t in tracks if t["popularity"] is not None]
    not_found = [t for t in tracks if t["popularity"] is None]
    logger.info("\nPlaylist Summary:")
    logger.info(f"  Matched on Spotify : {len(found)}")
    logger.info(f"  Not found          : {len(not_found)}")
    logger.info(f"  Total              : {len(tracks)}")
    logger.info("-" * 70)
    logger.info(f"{'Rank':>5}  {'Pop':>5}  {'Artist':<25}  Title")
    logger.info("-" * 70)
    for i, t in enumerate(tracks, 1):
        pop = str(t["popularity"]) if t["popularity"] is not None else "N/A"
        artist = (t["artist"] or "")[:24]
        title = (t["title"] or "")[:30]
        logger.info(f"{i:>5}  {pop:>5}  {artist:<25}  {title}")
    logger.info("-" * 70)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parallel Spotify‑powered M3U playlist creator with fuzzy matching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sort_mp3_to_playlist.py /path/to/music --workers 8
  python sort_mp3_to_playlist.py /path/to/music --workers 5 --match-threshold 80
  python sort_mp3_to_playlist.py /path/to/music --emby --output-dir playlists/ --emby-music-root /music
        """,
    )
    parser.add_argument("folder", help="Folder containing MP3 files")
    parser.add_argument("--format", choices=["m3u", "m3u8", "both"], default="m3u8")
    parser.add_argument("--name", default=None, help="Playlist filename without extension")
    parser.add_argument("--output-dir", metavar="DIR", default=None)
    parser.add_argument("--order", choices=["desc", "asc"], default="desc")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--absolute-paths", action="store_true")
    parser.add_argument("--rate-limit", type=float, default=0.5,
                        help="Seconds between API calls (default: 0.5)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel Spotify lookups (default: 4)")
    parser.add_argument("--match-threshold", type=int, default=DEFAULT_MATCH_THRESHOLD,
                        help=f"Minimum fuzzy match score (0-100) to accept (default: {DEFAULT_MATCH_THRESHOLD})")
    emby_group = parser.add_argument_group("Emby options")
    emby_group.add_argument("--emby", action="store_true")
    emby_group.add_argument("--emby-music-root", metavar="DIR", default=None)

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    folder = Path(args.folder)
    if not folder.is_dir():
        logger.error(f"Not a valid folder: {folder}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else folder
    output_dir.mkdir(parents=True, exist_ok=True)

    playlist_name = args.name or folder.name or "playlist"
    use_relative = not args.absolute_paths

    emby_music_root = Path(args.emby_music_root) if args.emby_music_root else None
    if args.emby and output_dir.resolve() != folder.resolve() and not emby_music_root:
        logger.error(
            "Emby mode with an --output-dir outside the music folder requires "
            "--emby-music-root to be set."
        )
        sys.exit(1)

    if args.emby:
        logger.info("Emby mode enabled")
        if emby_music_root:
            logger.info(f"  Emby music root : {emby_music_root}")
        logger.info(f"  Playlist output : {output_dir}")

    sp = get_spotify_client()
    if not sp:
        sys.exit(1)

    tracks = process_files(
        folder, sp, args.rate_limit, args.recursive,
        workers=args.workers, match_threshold=args.match_threshold,
    )
    if not tracks:
        logger.info("No tracks to process. Exiting.")
        sys.exit(0)

    sorted_tracks = sort_tracks(tracks, args.order)
    print_summary(sorted_tracks)

    if args.format in ("m3u8", "both"):
        write_m3u8(
            sorted_tracks,
            output_dir / f"{playlist_name}.m3u8",
            use_relative,
            emby_mode=args.emby,
            emby_music_root=emby_music_root,
        )
    if args.format in ("m3u", "both"):
        write_m3u(
            sorted_tracks,
            output_dir / f"{playlist_name}.m3u",
            use_relative,
            extended=True,
            emby_mode=args.emby,
            emby_music_root=emby_music_root,
        )

    logger.info("\n✓ Done!")

if __name__ == "__main__":
    main()
