#!/usr/bin/env python3
"""
ePUB → M4B Audiobook Converter for macOS
─────────────────────────────────────────
Uses Apple's built-in `say` command (no API key, fully offline).
Zero third-party dependencies — stdlib only (zipfile, xml, html.parser).

Requirements:
  brew install ffmpeg   # needed to stitch chapters → M4B

Usage:
  python3 ttxtoMB4.py
  python3 ttxtoMB4.py --voice Samantha --rate 175
  python3 ttxtoMB4.py --epub /path/to/local.epub --out mybook.m4b

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
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

# ── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_EPUB_URL = (
    "https://raw.githubusercontent.com/RockAfeller2013/vibecoded/"
    "refs/heads/main/Affirmations%20%26%20Principles%202026/"
    "Affirmations%20%26%20Principles%202026%20v2.epub"
)
DEFAULT_OUTPUT = "Affirmations_Principles_2026.m4b"
DEFAULT_VOICE  = "Samantha"
DEFAULT_RATE   = 175

# ── Filters ──────────────────────────────────────────────────────────────────

SKIP_NAME_PATTERNS = re.compile(
    r"(toc|nav|cover|copyright|title.?page|colophon|halftitle|frontmatter)",
    re.IGNORECASE,
)
PAGE_LINE_RE = re.compile(r"^\s*(\d{1,4}|[ivxlcdmIVXLCDM]{1,6})\s*$")
NOISE_LINE_RE = re.compile(
    r"^\s*(page|pg|p\.?)\s*\d+\s*$"
    r"|^\s*[-–—·•]\s*$"
    r"|^\s*\*{1,5}\s*$",
    re.IGNORECASE,
)

# ── HTML text extractor (replaces BeautifulSoup) ─────────────────────────────

class _TextExtractor(HTMLParser):
    """Pulls plain text out of HTML, skipping nav/script/style tags."""

    SKIP_TAGS    = {"script", "style", "nav", "head"}
    BLOCK_TAGS   = {"p", "h1", "h2", "h3", "h4", "h5", "h6",
                    "li", "blockquote", "div", "br"}
    HEADING_TAGS = {"h1", "h2", "h3"}

    def __init__(self):
        super().__init__()
        self.lines: list[str] = []
        self._current: list[str] = []
        self._skip_depth = 0
        self.title: str | None = None
        self._in_heading = False
        self._heading_buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if self._skip_depth:
            return
        if tag in self.HEADING_TAGS:
            self._in_heading = True
            self._heading_buf = []
        if tag in self.BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag in self.HEADING_TAGS and self._in_heading:
            self._in_heading = False
            heading = " ".join(self._heading_buf).strip()
            if heading and not self.title:
                self.title = heading

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self._current.append(text)
            if self._in_heading:
                self._heading_buf.append(text)

    def _flush(self):
        if self._current:
            self.lines.append(" ".join(self._current).strip())
            self._current = []

    def get_lines(self) -> list[str]:
        self._flush()
        return self.lines


# ── EPUB parsing (replaces ebooklib) ─────────────────────────────────────────

def _is_noise(text: str) -> bool:
    t = text.strip()
    return (not t) or len(t) <= 2 or bool(PAGE_LINE_RE.match(t)) or bool(NOISE_LINE_RE.match(t))


def _extract_chapter_text(html_bytes: bytes) -> tuple[str | None, str]:
    html = html_bytes.decode("utf-8", errors="replace")
    parser = _TextExtractor()
    parser.feed(html)
    lines = [l for l in parser.get_lines() if not _is_noise(l)]
    return parser.title, "\n\n".join(lines)


def _opf_path_from_zip(zf: zipfile.ZipFile) -> str:
    """Read META-INF/container.xml to locate the OPF manifest."""
    try:
        container = zf.read("META-INF/container.xml")
        root = ET.fromstring(container)
        ns = "urn:oasis:names:tc:opendocument:xmlns:container"
        rf = root.find(f".//{{{ns}}}rootfile")
        if rf is not None:
            return rf.get("full-path", "")
    except Exception:
        pass
    # Fallback: find any .opf file
    for name in zf.namelist():
        if name.endswith(".opf"):
            return name
    raise ValueError("Cannot find OPF file in EPUB")


def extract_chapters(epub_path: str) -> list[dict]:
    chapters: list[dict] = []
    with zipfile.ZipFile(epub_path, "r") as zf:
        opf_path = _opf_path_from_zip(zf)
        opf_dir  = str(Path(opf_path).parent)
        if opf_dir == ".":
            opf_dir = ""

        opf_root = ET.fromstring(zf.read(opf_path))
        OPF = "http://www.idpf.org/2007/opf"

        # Build id → href map for HTML items
        manifest: dict[str, str] = {}
        for item in opf_root.findall(f".//{{{OPF}}}item"):
            media = item.get("media-type", "")
            href  = item.get("href", "")
            if "html" in media or href.endswith((".html", ".xhtml", ".htm")):
                manifest[item.get("id", "")] = href

        # Follow spine order (or fall back to manifest insertion order)
        spine_hrefs: list[str] = []
        for itemref in opf_root.findall(f".//{{{OPF}}}itemref"):
            idref = itemref.get("idref", "")
            if idref in manifest:
                spine_hrefs.append(manifest[idref])
        if not spine_hrefs:
            spine_hrefs = list(manifest.values())

        for href in spine_hrefs:
            if SKIP_NAME_PATTERNS.search(href.split("/")[-1]):
                continue

            # Resolve path inside the ZIP
            candidates = [
                (opf_dir + "/" + href).lstrip("/") if opf_dir else href,
                href,
            ]
            content = None
            for candidate in candidates:
                try:
                    content = zf.read(candidate)
                    break
                except KeyError:
                    continue
            if content is None:
                continue

            title, text = _extract_chapter_text(content)
            if len(text.split()) < 50:
                continue

            chapters.append({
                "title": title or f"Section {len(chapters) + 1}",
                "text":  text,
            })

    return chapters


# ── macOS TTS ─────────────────────────────────────────────────────────────────

def say_to_m4a(text: str, out_path: str, voice: str, rate: int) -> None:
    txt_path = out_path + ".txt"
    Path(txt_path).write_text(text, encoding="utf-8")
    try:
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", out_path,
             "--data-format=aac", "-f", txt_path],
            check=True,
            capture_output=True,
        )
    finally:
        if os.path.exists(txt_path):
            os.unlink(txt_path)


def check_say_voice(voice: str) -> str:
    result = subprocess.run(
        ["say", "-v", "?"], capture_output=True, text=True, check=True
    )
    available = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    if not available:
        sys.exit("❌ No macOS voices found. Check System Settings → Accessibility → Spoken Content.")
    if voice not in available:
        print(f"⚠️  Voice '{voice}' not found — using '{available[0]}' instead.")
        return available[0]
    return voice


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def _check_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True)
        except FileNotFoundError:
            sys.exit(f"❌ {tool} not found. Install with:  brew install ffmpeg")


def _get_duration_ms(path: str) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    return int(float(data["format"]["duration"]) * 1000)


def build_m4b(audio_files: list[str], chapter_titles: list[str],
              book_title: str, output_path: str) -> None:
    base = Path(output_path).parent
    concat_txt = base / "_concat.txt"
    concat_txt.write_text(
        "".join(f"file '{f}'\n" for f in audio_files), encoding="utf-8"
    )

    meta_txt = base / "_meta.txt"
    lines = [";FFMETADATA1\n", f"title={book_title}\n", "artist=Apple TTS\n\n"]
    offset_ms = 0
    for title, path in zip(chapter_titles, audio_files):
        dur = _get_duration_ms(path)
        lines += [
            "[CHAPTER]\n", "TIMEBASE=1/1000\n",
            f"START={offset_ms}\n", f"END={offset_ms + dur}\n",
            f"title={title}\n\n",
        ]
        offset_ms += dur
    meta_txt.write_text("".join(lines), encoding="utf-8")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-i", str(meta_txt),
         "-map_metadata", "1", "-c:a", "aac", "-b:a", "64k", output_path],
        check=True, capture_output=True,
    )
    concat_txt.unlink(missing_ok=True)
    meta_txt.unlink(missing_ok=True)


# ── Main conversion ───────────────────────────────────────────────────────────

def convert(epub_source: str, output_path: str = DEFAULT_OUTPUT,
            voice: str = DEFAULT_VOICE, rate: int = DEFAULT_RATE) -> None:
    _check_ffmpeg()
    voice = check_say_voice(voice)

    with tempfile.TemporaryDirectory(prefix="epub2m4b_") as tmp_dir:
        tmp = Path(tmp_dir)

        if epub_source.startswith("http"):
            epub_path = tmp / "book.epub"
            print("⬇️  Downloading EPUB …")
            urllib.request.urlretrieve(epub_source, epub_path)
        else:
            epub_path = Path(epub_source)
            if not epub_path.exists():
                sys.exit(f"❌ File not found: {epub_path}")

        print("📖 Extracting chapters …")
        chapters = extract_chapters(str(epub_path))
        if not chapters:
            sys.exit("❌ No content chapters found in EPUB.")
        print(f"✅ Found {len(chapters)} chapter(s).")

        audio_files: list[str] = []
        titles:      list[str] = []
        for i, ch in enumerate(chapters, start=1):
            print(f"🔊 [{i}/{len(chapters)}] {ch['title']}")
            m4a = str(tmp / f"ch_{i:03d}.m4a")
            try:
                say_to_m4a(ch["text"], m4a, voice=voice, rate=rate)
                audio_files.append(m4a)
                titles.append(ch["title"])
            except subprocess.CalledProcessError as exc:
                print(f"   ⚠️  Skipped (say error): {exc}")

        if not audio_files:
            sys.exit("❌ No audio was generated.")

        print("🎬 Stitching M4B …")
        book_title = Path(output_path).stem.replace("_", " ")
        build_m4b(audio_files, titles, book_title, output_path)

    print(f"\n✅ Done!  →  {output_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ePUB → M4B converter (stdlib only, macOS)")
    p.add_argument("--epub",  default=DEFAULT_EPUB_URL,
                   help="Path or URL to the .epub file")
    p.add_argument("--out",   default=DEFAULT_OUTPUT,
                   help="Output .m4b filename")
    p.add_argument("--voice", default=DEFAULT_VOICE,
                   help="macOS voice name  (run: say -v ?)")
    p.add_argument("--rate",  default=DEFAULT_RATE, type=int,
                   help="Speech rate in words/minute")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    convert(epub_source=args.epub, output_path=args.out,
            voice=args.voice, rate=args.rate)
