#!/usr/bin/env python3
"""
Sort MP3 files by Spotify popularity.
Reads ID3 tags for accurate track matching and renames files with popularity ranking.
"""

import os
import sys
import time
import logging
import argparse
from typing import Optional, Tuple, List

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_spotify_client() -> Optional[spotipy.Spotify]:
    """
    Initialize and return Spotify client using environment variables.
    
    Returns:
        Spotify client instance or None if credentials are missing
    """
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("Spotify credentials not found in environment variables")
        logger.error("Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET")
        return None
    
    try:
        auth = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        return spotipy.Spotify(auth_manager=auth)
    except Exception as e:
        logger.error(f"Failed to initialize Spotify client: {e}")
        return None


def get_track_info_from_id3(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract track title and artist from MP3 ID3 tags.
    
    Args:
        file_path: Path to the MP3 file
        
    Returns:
        Tuple of (title, artist) or (None, None) if tags not found
    """
    try:
        audio = MP3(file_path)
        title = str(audio.get("TIT2", "")) if audio.get("TIT2") else None
        artist = str(audio.get("TPE1", "")) if audio.get("TPE1") else None
        return title, artist
    except ID3NoHeaderError:
        logger.warning(f"No ID3 tags found in: {os.path.basename(file_path)}")
        return None, None
    except Exception as e:
        logger.warning(f"Error reading ID3 tags from {os.path.basename(file_path)}: {e}")
        return None, None


def get_spotify_popularity(
    sp: spotipy.Spotify,
    title: Optional[str],
    artist: Optional[str],
    filename: str
) -> Optional[int]:
    """
    Get track popularity from Spotify.
    
    Args:
        sp: Spotify client instance
        title: Track title from ID3 tags
        artist: Artist name from ID3 tags
        filename: Filename to use as fallback
        
    Returns:
        Popularity score (0-100) or None if not found
    """
    if not sp:
        return None
    
    # Build search query
    if title and artist:
        query = f"track:{title} artist:{artist}"
        search_description = f"{artist} - {title}"
    elif title:
        query = f"track:{title}"
        search_description = title
    else:
        # Fallback to filename (remove extension)
        query = os.path.splitext(filename)[0]
        search_description = query
    
    try:
        logger.debug(f"Searching Spotify for: {search_description}")
        result = sp.search(q=query, type="track", limit=1)
        items = result.get("tracks", {}).get("items", [])
        
        if items:
            track = items[0]
            popularity = track["popularity"]
            matched_title = track["name"]
            matched_artist = track["artists"][0]["name"] if track["artists"] else "Unknown"
            
            logger.info(
                f"✓ Found: {matched_artist} - {matched_title} "
                f"(popularity: {popularity})"
            )
            return popularity
        else:
            logger.warning(f"✗ Not found on Spotify: {search_description}")
            return None
            
    except Exception as e:
        logger.error(f"Error searching Spotify for '{search_description}': {e}")
        return None


def process_mp3_files(
    folder: str,
    spotify: spotipy.Spotify,
    rate_limit_delay: float = 0.1
) -> List[Tuple[str, Optional[int]]]:
    """
    Process all MP3 files in folder and get their popularity scores.
    
    Args:
        folder: Path to folder containing MP3 files
        spotify: Spotify client instance
        rate_limit_delay: Delay between API requests in seconds
        
    Returns:
        List of tuples (filename, popularity_score)
    """
    mp3_files = [f for f in os.listdir(folder) if f.lower().endswith(".mp3")]
    
    if not mp3_files:
        logger.warning("No MP3 files found in folder")
        return []
    
    logger.info(f"Found {len(mp3_files)} MP3 file(s)")
    logger.info("-" * 60)
    
    tracks = []
    
    for index, file_name in enumerate(mp3_files, 1):
        logger.info(f"[{index}/{len(mp3_files)}] Processing: {file_name}")
        
        file_path = os.path.join(folder, file_name)
        
        # Extract ID3 tags
        title, artist = get_track_info_from_id3(file_path)
        
        # Get Spotify popularity
        popularity = get_spotify_popularity(spotify, title, artist, file_name)
        
        tracks.append((file_name, popularity))
        
        # Rate limiting delay
        if index < len(mp3_files):  # Don't delay after last file
            time.sleep(rate_limit_delay)
    
    logger.info("-" * 60)
    return tracks


def rename_files(
    folder: str,
    tracks: List[Tuple[str, Optional[int]]],
    dry_run: bool = False
) -> None:
    """
    Rename files based on popularity ranking.
    
    Args:
        folder: Path to folder containing MP3 files
        tracks: List of tuples (filename, popularity_score)
        dry_run: If True, only show what would be renamed without actually renaming
    """
    # Separate tracks with and without popularity scores
    found = [t for t in tracks if t[1] is not None]
    not_found = [t for t in tracks if t[1] is None]
    
    # Sort by popularity (descending) and alphabetically
    found.sort(key=lambda x: x[1], reverse=True)
    not_found.sort(key=lambda x: x[0].lower())
    
    ordered = found + not_found
    
    logger.info(f"\nRanking Summary:")
    logger.info(f"  Tracks with popularity: {len(found)}")
    logger.info(f"  Tracks without popularity: {len(not_found)}")
    logger.info(f"  Total: {len(ordered)}")
    logger.info("-" * 60)
    
    if dry_run:
        logger.info("DRY RUN MODE - No files will be renamed")
        logger.info("-" * 60)
    
    for index, (file_name, popularity) in enumerate(ordered, start=1):
        old_path = os.path.join(folder, file_name)
        new_name = f"{index:05d}_{file_name}"
        new_path = os.path.join(folder, new_name)
        
        # Handle naming conflicts
        counter = 1
        while os.path.exists(new_path):
            base, ext = os.path.splitext(file_name)
            new_name = f"{index:05d}_{base}_{counter}{ext}"
            new_path = os.path.join(folder, new_name)
            counter += 1
        
        popularity_str = f"popularity: {popularity}" if popularity is not None else "no data"
        
        if dry_run:
            logger.info(f"Would rename: {file_name}")
            logger.info(f"         to: {new_name} ({popularity_str})")
        else:
            try:
                os.rename(old_path, new_path)
                logger.info(f"✓ Renamed: {file_name}")
                logger.info(f"       to: {new_name} ({popularity_str})")
            except Exception as e:
                logger.error(f"✗ Failed to rename {file_name}: {e}")
    
    if dry_run:
        logger.info("-" * 60)
        logger.info("DRY RUN COMPLETE - Run without --dry-run to apply changes")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Sort MP3 files by Spotify popularity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sort_mp3_by_popularity.py /path/to/music
  python sort_mp3_by_popularity.py /path/to/music --dry-run
  python sort_mp3_by_popularity.py /path/to/music --verbose

Required environment variables:
  SPOTIPY_CLIENT_ID      - Your Spotify API client ID
  SPOTIPY_CLIENT_SECRET  - Your Spotify API client secret
        """
    )
    
    parser.add_argument(
        "folder",
        help="Path to folder containing MP3 files"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming files"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.1,
        help="Delay between API requests in seconds (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate folder
    if not os.path.isdir(args.folder):
        logger.error(f"Invalid folder path: {args.folder}")
        sys.exit(1)
    
    # Initialize Spotify client
    spotify = get_spotify_client()
    if not spotify:
        logger.error("Failed to initialize Spotify client. Exiting.")
        sys.exit(1)
    
    # Process files
    tracks = process_mp3_files(args.folder, spotify, args.rate_limit)
    
    if not tracks:
        logger.info("No tracks to process. Exiting.")
        sys.exit(0)
    
    # Rename files
    rename_files(args.folder, tracks, dry_run=args.dry_run)
    
    logger.info("\n✓ Processing complete!")


if __name__ == "__main__":
    main()
