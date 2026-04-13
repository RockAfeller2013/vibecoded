#!/usr/bin/env python3
"""
ePUB → M4B Audiobook Converter for macOS
─────────────────────────────────────────
Uses Apple's built-in `say` command (no API key, fully offline).
Filters out page numbers, TOC, navigation, cover pages, etc.
Adds chapter markers so you can skip between chapters in any M4B player.

Requirements (install once):
    pip install ebooklib beautifulsoup4
    brew install ffmpeg          # needed to stitch chapters → M4B

Usage:
    python epub_to_m4b.py
    python epub_to_m4b.py --voice Samantha --rate 175
    python epub_to_m4b.py --epub /path/to/local.epub --out mybook.m4b

List available macOS voices:
    say -v ?
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# ── Auto-install Python deps if missing ──────────────────────────────────────
def _ensure_packages():
    missing = []
    for pkg in ("ebooklib", "bs4"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append({"ebooklib": "ebooklib", "bs4": "beautifulsoup4"}[pkg])
    if missing:
        print(f"📦 Installing: {', '.join(missing)} …")
        subprocess.run([sys.executable, "-m", "pip", "install", *missing], check=True)

_ensure_packages()

import ebooklib                            # noqa: E402
from ebooklib import epub                  # noqa: E402
from bs4 import BeautifulSoup, NavigableString  # noqa: E402


# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_EPUB_URL = (
    "https://raw.githubusercontent.com/RockAfeller2013/vibecoded/"
    "refs/heads/main/Affirmations%20%26%20Principles%202026/"
    "Affirmations%20%26%20Principles%202026%20v2.epub"
)
DEFAULT_OUTPUT   = "Affirmations_Principles_2026.m4b"
DEFAULT_VOICE    = "Samantha"   # run `say -v ?` to list all voices
DEFAULT_RATE     = 175          # words per minute (175 is natural pace)

# ePUB document names that are almost certainly non-content
SKIP_NAME_PATTERNS = re.compile(
    r"(toc|nav|cover|copyright|title.?page|colophon|halftitle|frontmatter)",
    re.IGNORECASE,
)

# CSS class / epub:type patterns for page-number markup
PAGE_CLASS_RE  = re.compile(r"page.?num|pagebreak|page.?break|folio|pgnum", re.IGNORECASE)
PAGE_TYPE_RE   = re.compile(r"page", re.IGNORECASE)

# Lines that are just page numbers or short noise
PAGE_LINE_RE   = re.compile(r"^\s*(\d{1,4}|[ivxlcdmIVXLCDM]{1,6})\s*$")
NOISE_LINE_RE  = re.compile(
    r"^\s*(page|pg|p\.?)\s*\d+\s*$"
    r"|^\s*[-–—·•]\s*$"
    r"|^\s*\*{1,5}\s*$",
    re.IGNORECASE,
)


# ── Text extraction ───────────────────────────────────────────────────────────

def _clean_soup(soup: BeautifulSoup) -> None:
    """Remove all non-content tags in-place."""
    # Hard removes
    for tag in soup.find_all(["script", "style", "nav", "head"]):
        tag.decompose()
    # Page-number spans/divs by class
    for tag in soup.find_all(class_=PAGE_CLASS_RE):
        tag.decompose()
    # epub:type="pagebreak" etc.
    for tag in soup.find_all(attrs={"epub:type": PAGE_TYPE_RE}):
        tag.decompose()
    # aria-hidden elements (decorative)
    for tag in soup.find_all(attrs={"aria-hidden": "true"}):
        tag.decompose()


def _is_noise(text: str) -> bool:
    """Return True if text is a page number or short decorative line."""
    t = text.strip()
    if not t:
        return True
    if PAGE_LINE_RE.match(t):
        return True
    if NOISE_LINE_RE.match(t):
        return True
    if len(t) <= 2:          # single char / punctuation
        return True
    return False


def _extract_chapter_text(html_bytes: bytes) -> tuple[str | None, str]:
    """Parse one ePUB HTML document → (title, body_text)."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    _clean_soup(soup)

    # Chapter title from first heading
    title = None
    for htag in soup.find_all(["h1", "h2", "h3"]):
        t = htag.get_text(" ", strip=True)
        if t and not _is_noise(t):
            title = t
            break

    # Collect meaningful text blocks
    lines: list[str] = []
    for elem in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "div"]):
        # Skip nested: only top-level semantic blocks
        if elem.parent and elem.parent.name in {"li", "blockquote"}:
            continue
        text = elem.get_text(" ", strip=True)
        if not _is_noise(text):
            lines.append(text)

    return title, "\n\n".join(lines)


def extract_chapters(epub_path: str) -> list[dict]:
    """
    Read an ePUB and return a list of dicts:
        {"title": str, "text": str}
    Skips TOC, nav, cover, copyright, and any document with < 50 words.
    """
    book = epub.read_epub(epub_path, options={"ignore_ncx": False})
    chapters: list[dict] = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()

        # Skip navigation / boilerplate by filename
        if SKIP_NAME_PATTERNS.search(name):
            print(f"  ⏭  Skipping (non-content): {name}")
            continue

        title, text = _extract_chapter_text(item.get_content())

        word_count = len(text.split())
        if word_count < 50:
            print(f"  ⏭  Skipping (too short, {word_count} words): {name}")
            continue

        chapter_title = title or f"Section {len(chapters) + 1}"
        print(f"  ✅  Extracted: {chapter_title!r}  ({word_count} words)")
        chapters.append({"title": chapter_title, "text": text})

    return chapters


# ── macOS TTS ─────────────────────────────────────────────────────────────────

def say_to_m4a(text: str, out_path: str, voice: str, rate: int) -> None:
    """
    Use macOS `say` to synthesise `text` → AAC M4A file.
    Text is written to a temp file to avoid shell-argument length limits.
    """
    txt_path = out_path + ".txt"
    Path(txt_path).write_text(text, encoding="utf-8")
    try:
        subprocess.run(
            [
                "say",
                "-v", voice,
                "-r", str(rate),
                "-o", out_path,
                "--data-format=aac",   # output AAC inside M4A container
                "-f", txt_path,        # read from file (no arg-length limit)
            ],
            check=True,
            capture_output=True,
        )
    finally:
        os.unlink(txt_path)


def check_say_voice(voice: str) -> None:
    """Warn if the requested voice isn't installed."""
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
    available = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    if voice not in available:
        print(f"\n⚠️  Voice '{voice}' not found. Available voices include:")
        for v in available[:20]:
            print(f"     {v}")
        print("   Run `say -v ?` for the full list.")
        print(f"   Defaulting to '{available[0]}'\n")
        return available[0]
    return voice


# ── Audio utilities ──────────────────────────────────────────────────────────

def _check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit(
            "❌  ffmpeg not found.\n"
            "   Install it with:  brew install ffmpeg\n"
            "   (Homebrew: https://brew.sh)"
        )


def _get_duration_ms(path: str) -> int:
    """Return audio duration in milliseconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", path,
        ],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    return int(float(data["format"]["duration"]) * 1000)


def build_m4b(
    audio_files: list[str],
    chapter_titles: list[str],
    book_title: str,
    output_path: str,
) -> None:
    """
    Concatenate M4A chapter files → single M4B with chapter markers.
    """
    base = Path(output_path).parent

    # ── concat list ──
    concat_txt = base / "_concat.txt"
    concat_txt.write_text(
        "".join(f"file '{f}'\n" for f in audio_files), encoding="utf-8"
    )

    # ── ffmetadata with chapters ──
    meta_txt  = base / "_meta.txt"
    lines     = [";FFMETADATA1\n", f"title={book_title}\n", "artist=Apple TTS\n\n"]
    offset_ms = 0
    for title, path in zip(chapter_titles, audio_files):
        dur = _get_duration_ms(path)
        lines += [
            "[CHAPTER]\n",
            "TIMEBASE=1/1000\n",
            f"START={offset_ms}\n",
            f"END={offset_ms + dur}\n",
            f"title={title}\n\n",
        ]
        offset_ms += dur
    meta_txt.write_text("".join(lines), encoding="utf-8")

    # ── ffmpeg stitch ──
    print("\n🔧  Stitching chapters → M4B …")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-i", str(meta_txt),
            "-map_metadata", "1",
            "-c:a", "aac",
            "-b:a", "64k",
            output_path,
        ],
        check=True,
        capture_output=True,      # suppress verbose ffmpeg output
    )

    concat_txt.unlink(missing_ok=True)
    meta_txt.unlink(missing_ok=True)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def convert(
    epub_source: str,
    output_path: str = DEFAULT_OUTPUT,
    voice: str       = DEFAULT_VOICE,
    rate: int        = DEFAULT_RATE,
) -> None:
    _check_ffmpeg()
    voice = check_say_voice(voice)

    with tempfile.TemporaryDirectory(prefix="epub2m4b_") as tmp:
        tmp = Path(tmp)

        # 1. Acquire ePUB
        if epub_source.startswith("http"):
            epub_path = tmp / "book.epub"
            print(f"⬇️   Downloading ePUB …")
            urllib.request.urlretrieve(epub_source, epub_path)
            print(f"    Saved to {epub_path}")
        else:
            epub_path = Path(epub_source)
            if not epub_path.exists():
                sys.exit(f"❌  File not found: {epub_path}")

        # 2. Extract text chapters
        print("\n📖  Extracting text from ePUB …")
        chapters = extract_chapters(str(epub_path))
        if not chapters:
            sys.exit("❌  No content chapters found. Check the ePUB structure.")

        book_title = Path(output_path).stem.replace("_", " ")
        print(f"\n🗣   Synthesising {len(chapters)} chapter(s) with voice '{voice}' at {rate} wpm …")

        # 3. TTS each chapter
        audio_files: list[str]  = []
        titles:      list[str]  = []

        for i, ch in enumerate(chapters, start=1):
            m4a = str(tmp / f"ch_{i:03d}.m4a")
            label = ch["title"]
            words = len(ch["text"].split())
            print(f"  [{i}/{len(chapters)}] {label!r}  ({words} words) …", end=" ", flush=True)
            try:
                say_to_m4a(ch["text"], m4a, voice=voice, rate=rate)
                audio_files.append(m4a)
                titles.append(label)
                print("✅")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  SKIPPED — {e.stderr.decode()[:80]}")

        if not audio_files:
            sys.exit("❌  No audio was generated.")

        # 4. Combine → M4B
        build_m4b(audio_files, titles, book_title, output_path)

    # Report
    size_mb = Path(output_path).stat().st_size / 1_048_576
    print(f"\n🎧  Audiobook ready: {output_path}  ({size_mb:.1f} MB)")
    print(f"    Open in: Finder → double-click, or Books.app, VLC, Overcast …")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(description="Convert ePUB → M4B audiobook using macOS TTS")
    p.add_argument("--epub",  default=DEFAULT_EPUB_URL, help="Local path or URL to .epub")
    p.add_argument("--out",   default=DEFAULT_OUTPUT,   help="Output .m4b filename")
    p.add_argument("--voice", default=DEFAULT_VOICE,    help="macOS voice name  (run `say -v ?`)")
    p.add_argument("--rate",  default=DEFAULT_RATE, type=int, help="Words per minute (default 175)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    convert(
        epub_source=args.epub,
        output_path=args.out,
        voice=args.voice,
        rate=args.rate,
    )
