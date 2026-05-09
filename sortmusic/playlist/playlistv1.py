#!/usr/bin/env python3
"""
Create an M3U / M3U8 playlist of MP3 files sorted by Spotify popularity.
Files are never renamed or moved — only a playlist file is written.
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
from datetime import datetime

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.mp3 import MP3

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FILENAME_NOISE_RE = re.compile(
    r'\[.*?\]|\(.*?\)|\d{3,4}\s*kbps|official\s*(audio|video|lyric)',
    flags=re.IGNORECASE
)
CACHE_FILENAME = ".spotify_popularity_cache.json"


# ---------------------------------------------------------------------------
# Spotify client
# ---------------------------------------------------------------------------

def get_spotify_client() -> Optional[spotipy.Spotify]:
    """
    Initialize Spotify client from environment variables.

    Required env vars:
        SPOTIPY_CLIENT_ID
        SPOTIPY_CLIENT_SECRET
    """
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
# Cache
# ---------------------------------------------------------------------------

def load_cache(folder: Path) -> dict:
    """Load the popularity cache so interrupted runs can be resumed."""
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


def save_cache(folder: Path, cache: dict) -> None:
    """Persist cache to disk after every lookup."""
    try:
        with (folder / CACHE_FILENAME).open("w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=2)
    except Exception as e:
        logger.warning(f"Could not write cache: {e}")


# ---------------------------------------------------------------------------
# ID3 helpers
# ---------------------------------------------------------------------------

def get_track_info_from_id3(file_path: Path) -> Tuple[Optional[str], Optional[str], int]:
    """
    Extract title, artist and duration from MP3 ID3 tags.

    Returns:
        (title, artist, duration_seconds)
        title and artist may be None; duration defaults to 0 on error.
    """
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
# Spotify lookup
# ---------------------------------------------------------------------------

def _clean_filename(filename: str) -> str:
    """Strip noise from filename stem before using as Spotify fallback query."""
    stem = Path(filename).stem
    cleaned = FILENAME_NOISE_RE.sub("", stem)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def get_spotify_track(
    sp: spotipy.Spotify,
    title: Optional[str],
    artist: Optional[str],
    filename: str,
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Look up a track on Spotify and return its popularity, matched title, and matched artist.

    Retries up to 3 times on HTTP 429 rate-limit responses.

    Returns:
        (popularity, matched_title, matched_artist)
        All values may be None if the track is not found.
    """
    if title and artist:
        query = f"track:{title} artist:{artist}"
        description = f"{artist} - {title}"
    elif title:
        query = f"track:{title}"
        description = title
    else:
        query = _clean_filename(filename)
        description = query

    # FIX 2: guard against an empty query (e.g. file named "[Official Audio] (320kbps).mp3")
    if not query.strip():
        logger.warning(f"Could not build a Spotify search query for: {filename}")
        return None, None, None

    for attempt in range(3):
        try:
            result = sp.search(q=query, type="track", limit=1)
            items = result.get("tracks", {}).get("items", [])

            if items:
                track = items[0]
                pop = track["popularity"]
                t_title = track["name"]
                t_artist = track["artists"][0]["name"] if track["artists"] else "Unknown"
                logger.info(f"✓ {t_artist} - {t_title} (popularity: {pop})")
                return pop, t_title, t_artist
            else:
                logger.warning(f"✗ Not found: {description}")
                return None, None, None

        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                wait = int(getattr(e, "headers", {}).get("Retry-After", 5))
                logger.warning(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                logger.error(f"Spotify error for '{description}': {e}")
                return None, None, None
        except Exception as e:
            logger.error(f"Error searching '{description}': {e}")
            return None, None, None

    logger.error(f"Giving up on '{description}' after 3 retries.")
    return None, None, None


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def process_files(
    folder: Path,
    sp: spotipy.Spotify,
    rate_limit_delay: float,
    recursive: bool,
) -> List[dict]:
    """
    Walk the folder, query Spotify for each MP3, and return a list of track dicts.

    Each dict contains:
        file_path, title, artist, duration, popularity,
        spotify_title, spotify_artist
    """
    # FIX 4: case-insensitive match so .MP3 / .Mp3 aren't silently skipped on Linux
    glob_fn = folder.rglob if recursive else folder.glob
    mp3_files = sorted(f for f in glob_fn("*") if f.suffix.lower() == ".mp3")

    if not mp3_files:
        logger.warning("No MP3 files found.")
        return []

    logger.info(f"Found {len(mp3_files)} MP3 file(s)")
    logger.info("-" * 60)

    cache = load_cache(folder)
    tracks = []

    for index, file_path in enumerate(mp3_files, 1):
        logger.info(f"[{index}/{len(mp3_files)}] {file_path.name}")

        cache_key = str(file_path.relative_to(folder))

        # FIX 5: check cache BEFORE reading ID3 tags to avoid unnecessary disk I/O
        if cache_key in cache:
            cached = cache[cache_key]
            logger.info(f"  (cache hit — popularity: {cached.get('popularity')})")
            # Still read duration from file if cache entry is missing it
            duration = cached.get("duration") or int(
                MP3(str(file_path)).info.length
            ) if not cached.get("duration") else cached["duration"]
            tracks.append({
                "file_path": file_path,
                "title": cached.get("spotify_title") or file_path.stem,
                "artist": cached.get("spotify_artist") or "Unknown",
                "duration": duration,
                "popularity": cached.get("popularity"),
                "spotify_title": cached.get("spotify_title"),
                "spotify_artist": cached.get("spotify_artist"),
            })
            continue

        # Only read ID3 tags when we actually need them (cache miss)
        title, artist, duration = get_track_info_from_id3(file_path)
        popularity, spotify_title, spotify_artist = get_spotify_track(
            sp, title, artist, file_path.name
        )

        entry = {
            "file_path": file_path,
            "title": title or spotify_title or file_path.stem,
            "artist": artist or spotify_artist or "Unknown",
            "duration": duration,
            "popularity": popularity,
            "spotify_title": spotify_title,
            "spotify_artist": spotify_artist,
        }
        tracks.append(entry)

        cache[cache_key] = {
            "popularity": popularity,
            "duration": duration,
            "spotify_title": spotify_title,
            "spotify_artist": spotify_artist,
        }
        save_cache(folder, cache)

        if index < len(mp3_files):
            time.sleep(rate_limit_delay)

    logger.info("-" * 60)
    return tracks


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def sort_tracks(tracks: List[dict], order: str) -> List[dict]:
    """
    Sort tracks by popularity.

    order:
        'desc'  — most popular first (default)
        'asc'   — least popular first
    """
    found = [t for t in tracks if t["popularity"] is not None]
    not_found = [t for t in tracks if t["popularity"] is None]

    # FIX 3: negate popularity so only it is reversed; artist/title always sort A→Z
    sign = -1 if order == "desc" else 1
    found.sort(key=lambda t: (
        sign * t["popularity"],
        t["artist"].lower(),
        t["title"].lower(),
    ))
    not_found.sort(key=lambda t: (t["artist"].lower(), t["title"].lower()))

    # Tracks not found on Spotify always go at the end
    return found + not_found


# ---------------------------------------------------------------------------
# Playlist writers
# ---------------------------------------------------------------------------

def _track_path_str(file_path: Path, output_path: Path, use_relative: bool) -> str:
    """
    Return the path string to write into the playlist.

    FIX 1: use os.path.relpath() instead of Path.relative_to() so paths
            work correctly when --output-dir is outside the music folder.
    FIX 6: replace backslashes so playlists load correctly on Windows players.
    """
    if use_relative:
        rel = os.path.relpath(str(file_path.resolve()), str(output_path.parent.resolve()))
        return rel.replace("\\", "/")
    return file_path.resolve().as_posix()


def _extinf_line(track: dict, emby_mode: bool) -> str:
    """
    Build the #EXTINF line for a track.

    Emby parses everything after the comma as the display name, so in
    emby_mode we write a clean 'Artist - Title' with no extra tags.
    Popularity is moved to a separate comment line that Emby safely ignores.

    Standard (non-Emby) mode appends [popularity: N] to the display name.

    Duration is -1 when unknown — the M3U spec reserves 0 as a valid
    timestamp, so -1 is the correct sentinel for 'unknown duration'.
    """
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
    """
    Write an M3U (ASCII) playlist file.

    Args:
        tracks:             Sorted list of track dicts.
        output_path:        Where to write the .m3u file.
        use_relative_paths: Write paths relative to the playlist file.
        extended:           Write #EXTM3U header and #EXTINF lines.
        emby_mode:          Produce Emby-compatible output (clean EXTINF,
                            separate popularity comments, #EXTART tags).
        emby_music_root:    When set, relative paths are calculated from this
                            root instead of the playlist file location — needed
                            when the playlist lives in Emby's playlists folder
                            which is separate from the music library.
    """
    with output_path.open("w", encoding="ascii", errors="replace") as fh:
        if extended:
            fh.write("#EXTM3U\n")
            fh.write("# Generated by sort_mp3_to_playlist.py\n")
            fh.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"# Tracks: {len(tracks)}\n\n")

        for track in tracks:
            # Emby music root overrides normal relative-path anchor
            if emby_music_root and use_relative_paths:
                rel = os.path.relpath(
                    str(track["file_path"].resolve()),
                    str(emby_music_root.resolve()),
                )
                path_str = rel.replace("\\", "/")
            else:
                path_str = _track_path_str(track["file_path"], output_path, use_relative_paths)

            if extended:
                if emby_mode:
                    # #EXTART is read by Emby for artist display
                    fh.write(f"#EXTART:{track['artist']}\n")
                    # Popularity as a plain comment — Emby ignores unknown # tags
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
    """
    Write an M3U8 (UTF-8) extended playlist file.

    M3U8 is identical to extended M3U but UTF-8 encoded, making it safe
    for non-ASCII filenames and metadata. Preferred format for Emby.

    Args:
        tracks:             Sorted list of track dicts.
        output_path:        Where to write the .m3u8 file.
        use_relative_paths: Write paths relative to the playlist file.
        emby_mode:          Produce Emby-compatible output (clean EXTINF,
                            separate popularity comments, #EXTART tags).
        emby_music_root:    When set, relative paths are calculated from this
                            root instead of the playlist file location — needed
                            when the playlist lives in Emby's playlists folder.
    """
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write("#EXTM3U\n")
        fh.write("# Generated by sort_mp3_to_playlist.py\n")
        fh.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        fh.write(f"# Tracks: {len(tracks)}\n\n")

        for track in tracks:
            if emby_music_root and use_relative_paths:
                rel = os.path.relpath(
                    str(track["file_path"].resolve()),
                    str(emby_music_root.resolve()),
                )
                path_str = rel.replace("\\", "/")
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
    """Print a ranked table of all processed tracks."""
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
        description="Create an M3U/M3U8 playlist of MP3s sorted by Spotify popularity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard M3U8 playlist
  python sort_mp3_to_playlist.py /path/to/music

  # Emby-compatible playlist saved into Emby's playlists folder
  python sort_mp3_to_playlist.py /path/to/music --emby \\
      --output-dir "/var/lib/emby/data/playlists/Top Hits" \\
      --emby-music-root /path/to/music

  # Plain M3U (ASCII)
  python sort_mp3_to_playlist.py /path/to/music --format m3u

  # Both formats at once
  python sort_mp3_to_playlist.py /path/to/music --format both

  # Custom output name
  python sort_mp3_to_playlist.py /path/to/music --name "My Top Tracks"

  # Least popular first
  python sort_mp3_to_playlist.py /path/to/music --order asc

  # Include sub-folders
  python sort_mp3_to_playlist.py /path/to/music --recursive

  # Use absolute paths inside the playlist
  python sort_mp3_to_playlist.py /path/to/music --absolute-paths

Required environment variables:
  SPOTIPY_CLIENT_ID     - Your Spotify API client ID
  SPOTIPY_CLIENT_SECRET - Your Spotify API client secret
        """,
    )

    parser.add_argument("folder", help="Folder containing MP3 files")

    parser.add_argument(
        "--format", choices=["m3u", "m3u8", "both"], default="m3u8",
        help="Playlist format to write (default: m3u8)",
    )
    parser.add_argument(
        "--name", default=None,
        help="Playlist filename without extension (default: folder name)",
    )
    parser.add_argument(
        "--output-dir", metavar="DIR", default=None,
        help="Where to save the playlist (default: same as music folder)",
    )
    parser.add_argument(
        "--order", choices=["desc", "asc"], default="desc",
        help="Sort order: desc = most popular first (default), asc = least popular first",
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Include MP3s in sub-folders",
    )
    parser.add_argument(
        "--absolute-paths", action="store_true",
        help="Write absolute paths in playlist (default: relative paths)",
    )
    parser.add_argument(
        "--rate-limit", type=float, default=0.5,
        help="Seconds between Spotify API requests (default: 0.5)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging",
    )

    # Emby-specific options
    emby_group = parser.add_argument_group("Emby options")
    emby_group.add_argument(
        "--emby", action="store_true",
        help=(
            "Produce Emby-compatible output: clean #EXTINF display names "
            "(no popularity tags in titles), #EXTART per track, and "
            "popularity moved to safe comment lines Emby ignores"
        ),
    )
    emby_group.add_argument(
        "--emby-music-root", metavar="DIR", default=None,
        help=(
            "Your Emby music library root path. Required when --output-dir "
            "points to Emby's playlists folder (which is outside your music "
            "library). Relative paths in the playlist will be calculated from "
            "this root so Emby can locate each file. "
            "Example: /media/music or Z:\\Music"
        ),
    )

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

    if args.emby:
        logger.info("Emby mode enabled — generating Emby-compatible playlist")
        if emby_music_root:
            logger.info(f"  Emby music root : {emby_music_root}")
        logger.info(f"  Playlist output : {output_dir}")
        logger.info(
            "  Tip: place the playlist in your Emby music library folder OR in\n"
            "  Emby's data/playlists/<PlaylistName>/ directory and refresh your library."
        )

    sp = get_spotify_client()
    if not sp:
        sys.exit(1)

    tracks = process_files(folder, sp, args.rate_limit, args.recursive)
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
