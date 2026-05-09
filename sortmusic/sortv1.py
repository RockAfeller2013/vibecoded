#!/usr/bin/env python3
"""
Sort MP3 files by Spotify popularity.
Reads ID3 tags for accurate track matching and renames files with popularity ranking.
"""

import os
import sys
import time
import json
import logging
import argparse
import re
from pathlib import Path
from typing import Optional, Tuple, List

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.mp3 import MP3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# FIX: regex to strip noise from filenames before using as Spotify search fallback
FILENAME_NOISE_RE = re.compile(
    r'\[.*?\]|\(.*?\)|\d{3,4}\s*kbps|official\s*(audio|video|lyric)',
    flags=re.IGNORECASE
)

CACHE_FILENAME = ".spotify_popularity_cache.json"


# ---------------------------------------------------------------------------
# Spotify client
# ---------------------------------------------------------------------------

def get_spotify_client() -> Optional[spotipy.Spotify]:
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.error("Spotify credentials not found in environment variables")
        logger.error("Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET")
        return None

    try:
        auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        return spotipy.Spotify(auth_manager=auth)
    except Exception as e:
        logger.error(f"Failed to initialize Spotify client: {e}")
        return None


# ---------------------------------------------------------------------------
# Cache helpers  (NEW)
# ---------------------------------------------------------------------------

def load_cache(folder: Path) -> dict:
    """Load popularity cache from disk so interrupted runs can be resumed."""
    cache_path = folder / CACHE_FILENAME
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            logger.info(f"Loaded cache with {len(data)} entries from {cache_path.name}")
            return data
        except Exception as e:
            logger.warning(f"Could not read cache file: {e}")
    return {}


def save_cache(folder: Path, cache: dict) -> None:
    """Persist the popularity cache to disk after every lookup."""
    cache_path = folder / CACHE_FILENAME
    try:
        with cache_path.open("w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=2)
        logger.debug(f"Cache saved to {cache_path.name}")
    except Exception as e:
        logger.warning(f"Could not write cache file: {e}")


# ---------------------------------------------------------------------------
# ID3 tag extraction
# ---------------------------------------------------------------------------

def get_track_info_from_id3(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        audio = MP3(str(file_path))

        # FIX: audio.tags is None when there's no ID3 header — MP3() does NOT
        # raise ID3NoHeaderError, so the original except block never fired.
        if audio.tags is None:
            logger.warning(f"No ID3 tags found in: {file_path.name}")
            return None, None

        title = str(audio.tags.get("TIT2", "")).strip() or None
        artist = str(audio.tags.get("TPE1", "")).strip() or None
        return title, artist

    except Exception as e:
        logger.warning(f"Error reading ID3 tags from {file_path.name}: {e}")
        return None, None


# ---------------------------------------------------------------------------
# Spotify lookup
# ---------------------------------------------------------------------------

def _clean_filename_query(filename: str) -> str:
    """Strip common noise from a filename to improve Spotify search accuracy."""
    stem = Path(filename).stem
    cleaned = FILENAME_NOISE_RE.sub("", stem)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def get_spotify_popularity(
    sp: spotipy.Spotify,
    title: Optional[str],
    artist: Optional[str],
    filename: str,
    rate_limit_delay: float = 0.5,
) -> Optional[int]:
    if not sp:
        return None

    if title and artist:
        query = f"track:{title} artist:{artist}"
        search_description = f"{artist} - {title}"
    elif title:
        query = f"track:{title}"
        search_description = title
    else:
        # FIX: clean filename before using as fallback (removes kbps, brackets, etc.)
        query = _clean_filename_query(filename)
        search_description = query

    for attempt in range(3):
        try:
            logger.debug(f"Searching Spotify for: {search_description}")
            result = sp.search(q=query, type="track", limit=1)
            items = result.get("tracks", {}).get("items", [])

            if items:
                track = items[0]
                popularity = track["popularity"]
                matched_title = track["name"]
                matched_artist = track["artists"][0]["name"] if track["artists"] else "Unknown"
                logger.info(f"✓ Found: {matched_artist} - {matched_title} (popularity: {popularity})")
                return popularity
            else:
                logger.warning(f"✗ Not found on Spotify: {search_description}")
                return None

        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                # FIX: honour the Retry-After header instead of crashing
                retry_after = int(getattr(e, "headers", {}).get("Retry-After", 5))
                logger.warning(f"Rate limited. Waiting {retry_after}s (attempt {attempt + 1}/3)...")
                time.sleep(retry_after)
            else:
                logger.error(f"Spotify API error for '{search_description}': {e}")
                return None
        except Exception as e:
            logger.error(f"Error searching Spotify for '{search_description}': {e}")
            return None

    logger.error(f"Giving up on '{search_description}' after 3 retries.")
    return None


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_mp3_files(
    folder: Path,
    spotify: spotipy.Spotify,
    rate_limit_delay: float = 0.5,
) -> List[Tuple[str, Optional[int]]]:
    # FIX: sort() for deterministic order across all OS/filesystems
    # FIX: skip already-prefixed files so re-runs don't double-prefix them
    mp3_files = sorted(
        f.name for f in folder.glob("*.mp3")
        if not re.match(r"^\d{5}_", f.name)
    )

    if not mp3_files:
        logger.warning("No MP3 files found (or all are already prefixed).")
        return []

    logger.info(f"Found {len(mp3_files)} MP3 file(s)")
    logger.info("-" * 60)

    cache = load_cache(folder)
    tracks: List[Tuple[str, Optional[int]]] = []

    for index, file_name in enumerate(mp3_files, 1):
        logger.info(f"[{index}/{len(mp3_files)}] Processing: {file_name}")

        if file_name in cache:
            popularity = cache[file_name]
            logger.info(f"  (cache hit — popularity: {popularity})")
            tracks.append((file_name, popularity))
            continue

        file_path = folder / file_name
        title, artist = get_track_info_from_id3(file_path)
        popularity = get_spotify_popularity(spotify, title, artist, file_name, rate_limit_delay)

        cache[file_name] = popularity
        tracks.append((file_name, popularity))
        save_cache(folder, cache)  # persist after every lookup

        if index < len(mp3_files):
            time.sleep(rate_limit_delay)

    logger.info("-" * 60)
    return tracks


# ---------------------------------------------------------------------------
# Renaming
# ---------------------------------------------------------------------------

def rename_files(
    folder: Path,
    tracks: List[Tuple[str, Optional[int]]],
    output_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> None:
    found = [t for t in tracks if t[1] is not None]
    not_found = [t for t in tracks if t[1] is None]

    # Sort by popularity descending, then alphabetically within ties
    found.sort(key=lambda x: (-x[1], x[0].lower()))
    not_found.sort(key=lambda x: x[0].lower())
    ordered = found + not_found

    logger.info("\nRanking Summary:")
    logger.info(f"  Tracks with popularity   : {len(found)}")
    logger.info(f"  Tracks without popularity: {len(not_found)}")
    logger.info(f"  Total                    : {len(ordered)}")
    logger.info("-" * 60)

    if dry_run:
        logger.info("DRY RUN MODE — no files will be renamed")
        logger.info("-" * 60)

    dest_folder = output_dir if output_dir else folder
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # NEW: summary table
    logger.info(f"{'Rank':>5}  {'Popularity':>10}  File")
    logger.info("-" * 60)

    for index, (file_name, popularity) in enumerate(ordered, start=1):
        src_path = folder / file_name
        new_name = f"{index:05d}_{file_name}"
        dest_path = dest_folder / new_name

        counter = 1
        while dest_path.exists():
            stem = Path(file_name).stem
            ext = Path(file_name).suffix
            new_name = f"{index:05d}_{stem}_{counter}{ext}"
            dest_path = dest_folder / new_name
            counter += 1

        popularity_str = str(popularity) if popularity is not None else "N/A"
        logger.info(f"{index:>5}  {popularity_str:>10}  {file_name}")

        if dry_run:
            logger.info(f"         -> {new_name}")
            continue

        try:
            if output_dir:
                import shutil
                shutil.copy2(src_path, dest_path)
            else:
                src_path.rename(dest_path)
        except Exception as e:
            logger.error(f"✗ Failed for {file_name}: {e}")

    if dry_run:
        logger.info("-" * 60)
        logger.info("DRY RUN COMPLETE — run without --dry-run to apply changes")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sort MP3 files by Spotify popularity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sort_mp3_by_popularity.py /path/to/music
  python sort_mp3_by_popularity.py /path/to/music --dry-run
  python sort_mp3_by_popularity.py /path/to/music --output-dir /path/to/sorted
  python sort_mp3_by_popularity.py /path/to/music --verbose

Required environment variables:
  SPOTIPY_CLIENT_ID     - Your Spotify API client ID
  SPOTIPY_CLIENT_SECRET - Your Spotify API client secret
        """,
    )

    parser.add_argument("folder", help="Path to folder containing MP3 files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be renamed without actually renaming files")
    parser.add_argument("--output-dir", metavar="DIR",
                        help="Copy renamed files here instead of renaming in place (safer)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose debug logging")
    parser.add_argument("--rate-limit", type=float, default=0.5,
                        # FIX: raised from 0.1 to 0.5 — safer default for Spotify
                        help="Delay between API requests in seconds (default: 0.5)")

    args = parser.parse_args()

    # FIX: set the ROOT logger level — the original code set only the named
    # logger, leaving the basicConfig handler still at INFO, so --verbose did nothing.
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    folder = Path(args.folder)
    if not folder.is_dir():
        logger.error(f"Invalid folder path: {folder}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    spotify = get_spotify_client()
    if not spotify:
        logger.error("Failed to initialize Spotify client. Exiting.")
        sys.exit(1)

    tracks = process_mp3_files(folder, spotify, args.rate_limit)
    if not tracks:
        logger.info("No tracks to process. Exiting.")
        sys.exit(0)

    rename_files(folder, tracks, output_dir=output_dir, dry_run=args.dry_run)
    logger.info("\n✓ Processing complete!")


if __name__ == "__main__":
    main()
