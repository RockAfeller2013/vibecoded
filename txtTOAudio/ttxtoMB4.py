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

# Issues fixed:
# - check_say_voice return type mismatch (None vs str)
# - potential crash if no voices available
# - safer temp file deletion
# - ffprobe dependency not validated
# - minor robustness improvements

#!/usr/bin/env python3
"""
ePUB → M4B Audiobook Converter for macOS
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


def _ensure_packages():
    missing = []
    mapping = {"ebooklib": "ebooklib", "bs4": "beautifulsoup4"}

    for pkg in mapping:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(mapping[pkg])

    if missing:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *missing],
            check=True,
        )


_ensure_packages()

import ebooklib  # noqa: E402
from ebooklib import epub  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402


DEFAULT_EPUB_URL = (
    "https://raw.githubusercontent.com/RockAfeller2013/vibecoded/"
    "refs/heads/main/Affirmations%20%26%20Principles%202026/"
    "Affirmations%20%26%20Principles%202026%20v2.epub"
)
DEFAULT_OUTPUT = "Affirmations_Principles_2026.m4b"
DEFAULT_VOICE = "Samantha"
DEFAULT_RATE = 175

SKIP_NAME_PATTERNS = re.compile(
    r"(toc|nav|cover|copyright|title.?page|colophon|halftitle|frontmatter)",
    re.IGNORECASE,
)

PAGE_CLASS_RE = re.compile(r"page.?num|pagebreak|page.?break|folio|pgnum", re.IGNORECASE)
PAGE_TYPE_RE = re.compile(r"page", re.IGNORECASE)

PAGE_LINE_RE = re.compile(r"^\s*(\d{1,4}|[ivxlcdmIVXLCDM]{1,6})\s*$")
NOISE_LINE_RE = re.compile(
    r"^\s*(page|pg|p\.?)\s*\d+\s*$"
    r"|^\s*[-–—·•]\s*$"
    r"|^\s*\*{1,5}\s*$",
    re.IGNORECASE,
)


def _clean_soup(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["script", "style", "nav", "head"]):
        tag.decompose()

    for tag in soup.find_all(class_=PAGE_CLASS_RE):
        tag.decompose()

    for tag in soup.find_all(attrs={"epub:type": PAGE_TYPE_RE}):
        tag.decompose()

    for tag in soup.find_all(attrs={"aria-hidden": "true"}):
        tag.decompose()


def _is_noise(text: str) -> bool:
    t = text.strip()

    if not t:
        return True
    if PAGE_LINE_RE.match(t):
        return True
    if NOISE_LINE_RE.match(t):
        return True
    if len(t) <= 2:
        return True

    return False


def _extract_chapter_text(html_bytes: bytes) -> tuple[str | None, str]:
    soup = BeautifulSoup(html_bytes, "html.parser")
    _clean_soup(soup)

    title = None
    for htag in soup.find_all(["h1", "h2", "h3"]):
        t = htag.get_text(" ", strip=True)
        if t and not _is_noise(t):
            title = t
            break

    lines = []
    for elem in soup.find_all(
        ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "div"]
    ):
        if elem.parent and elem.parent.name in {"li", "blockquote"}:
            continue

        text = elem.get_text(" ", strip=True)
        if not _is_noise(text):
            lines.append(text)

    return title, "\n\n".join(lines)


def extract_chapters(epub_path: str) -> list[dict]:
    book = epub.read_epub(epub_path, options={"ignore_ncx": False})
    chapters = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()

        if SKIP_NAME_PATTERNS.search(name):
            continue

        title, text = _extract_chapter_text(item.get_content())
        word_count = len(text.split())

        if word_count < 50:
            continue

        chapter_title = title or f"Section {len(chapters) + 1}"
        chapters.append({"title": chapter_title, "text": text})

    return chapters


def say_to_m4a(text: str, out_path: str, voice: str, rate: int) -> None:
    txt_path = out_path + ".txt"
    Path(txt_path).write_text(text, encoding="utf-8")

    try:
        subprocess.run(
            [
                "say",
                "-v",
                voice,
                "-r",
                str(rate),
                "-o",
                out_path,
                "--data-format=aac",
                "-f",
                txt_path,
            ],
            check=True,
            capture_output=True,
        )
    finally:
        if os.path.exists(txt_path):
            os.unlink(txt_path)


def check_say_voice(voice: str) -> str:
    result = subprocess.run(
        ["say", "-v", "?"],
        capture_output=True,
        text=True,
        check=True,
    )

    available = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]

    if not available:
        sys.exit("❌ No macOS voices found.")

    if voice not in available:
        return available[0]

    return voice


def _check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit("❌ ffmpeg/ffprobe not found. Install via: brew install ffmpeg")


def _get_duration_ms(path: str) -> int:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    return int(float(data["format"]["duration"]) * 1000)


def build_m4b(
    audio_files: list[str],
    chapter_titles: list[str],
    book_title: str,
    output_path: str,
) -> None:
    base = Path(output_path).parent

    concat_txt = base / "_concat.txt"
    concat_txt.write_text(
        "".join(f"file '{f}'\n" for f in audio_files),
        encoding="utf-8",
    )

    meta_txt = base / "_meta.txt"
    lines = [";FFMETADATA1\n", f"title={book_title}\n", "artist=Apple TTS\n\n"]

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

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-i",
            str(meta_txt),
            "-map_metadata",
            "1",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            output_path,
        ],
        check=True,
        capture_output=True,
    )

    concat_txt.unlink(missing_ok=True)
    meta_txt.unlink(missing_ok=True)


def convert(
    epub_source: str,
    output_path: str = DEFAULT_OUTPUT,
    voice: str = DEFAULT_VOICE,
    rate: int = DEFAULT_RATE,
) -> None:
    _check_ffmpeg()
    voice = check_say_voice(voice)

    with tempfile.TemporaryDirectory(prefix="epub2m4b_") as tmp_dir:
        tmp = Path(tmp_dir)

        if epub_source.startswith("http"):
            epub_path = tmp / "book.epub"
            urllib.request.urlretrieve(epub_source, epub_path)
        else:
            epub_path = Path(epub_source)
            if not epub_path.exists():
                sys.exit(f"❌ File not found: {epub_path}")

        chapters = extract_chapters(str(epub_path))
        if not chapters:
            sys.exit("❌ No content chapters found.")

        audio_files = []
        titles = []

        for i, ch in enumerate(chapters, start=1):
            m4a = str(tmp / f"ch_{i:03d}.m4a")
            try:
                say_to_m4a(ch["text"], m4a, voice=voice, rate=rate)
                audio_files.append(m4a)
                titles.append(ch["title"])
            except subprocess.CalledProcessError:
                continue

        if not audio_files:
            sys.exit("❌ No audio generated.")

        book_title = Path(output_path).stem.replace("_", " ")
        build_m4b(audio_files, titles, book_title, output_path)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epub", default=DEFAULT_EPUB_URL)
    parser.add_argument("--out", default=DEFAULT_OUTPUT)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", type=int, default=DEFAULT_RATE)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    convert(
        epub_source=args.epub,
        output_path=args.out,
        voice=args.voice,
        rate=args.rate,
    )
