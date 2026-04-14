#!/usr/bin/env python3
"""
ePUB → M4B Audiobook Converter for macOS
─────────────────────────────────────────
Uses Apple's built-in `say` command (no API key, fully offline).
Zero third-party dependencies — stdlib only (zipfile, xml, html.parser).

Requirements:
  brew install ffmpeg   # needed to stitch chapters → M4B
  pip install tqdm      # optional — enables progress bars

Usage:
  python3 ttxtoMB4.py
  python3 ttxtoMB4.py --voice Samantha --rate 175
  python3 ttxtoMB4.py --epub /path/to/local.epub --out mybook.m4b

List available macOS voices:
  say -v ?
"""

import argparse
import json
import logging
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

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── Logging ──────────────────────────────────────────────────────────────────

LOG_FILE = "epub2m4b.log"

# Root config matches the user's pattern: errors always go to the log file.
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Module logger captures INFO and above so milestones are also recorded.
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
log.addHandler(_file_handler)

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
            path = rf.get("full-path", "")
            log.debug("OPF path from container.xml: %s", path)
            return path
    except Exception:
        log.exception("Failed to parse META-INF/container.xml — falling back to .opf scan")
    # Fallback: find any .opf file
    for name in zf.namelist():
        if name.endswith(".opf"):
            log.warning("Using fallback OPF path: %s", name)
            return name
    raise ValueError("Cannot find OPF file in EPUB")


def extract_chapters(epub_path: str) -> list[dict]:
    log.info("Extracting chapters from: %s", epub_path)
    chapters: list[dict] = []

    try:
        zf_ctx = zipfile.ZipFile(epub_path, "r")
    except (zipfile.BadZipFile, FileNotFoundError):
        log.exception("Failed to open EPUB as ZIP: %s", epub_path)
        raise

    with zf_ctx as zf:
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

        log.debug("Manifest HTML items found: %d", len(manifest))

        # Follow spine order (or fall back to manifest insertion order)
        spine_hrefs: list[str] = []
        for itemref in opf_root.findall(f".//{{{OPF}}}itemref"):
            idref = itemref.get("idref", "")
            if idref in manifest:
                spine_hrefs.append(manifest[idref])
        if not spine_hrefs:
            log.warning("Spine is empty — falling back to manifest order")
            spine_hrefs = list(manifest.values())

        log.debug("Spine items to process: %d", len(spine_hrefs))

        spine_iter = (
            tqdm(spine_hrefs, desc="📖 Parsing chapters", unit="file", colour="cyan")
            if HAS_TQDM
            else spine_hrefs
        )

        for href in spine_iter:
            if SKIP_NAME_PATTERNS.search(href.split("/")[-1]):
                log.debug("Skipping front/back-matter file: %s", href)
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
                log.warning("Could not read spine entry (not found in ZIP): %s", href)
                continue

            title, text = _extract_chapter_text(content)
            word_count = len(text.split())
            if word_count < 50:
                log.debug("Skipping '%s' — only %d words (below threshold)", href, word_count)
                continue

            chapters.append({
                "title": title or f"Section {len(chapters) + 1}",
                "text":  text,
            })
            log.info("Accepted chapter %d: '%s' (%d words)",
                     len(chapters), chapters[-1]["title"], word_count)

    log.info("Chapter extraction complete — %d chapter(s) found", len(chapters))
    return chapters


# ── macOS TTS ─────────────────────────────────────────────────────────────────

def say_to_m4a(text: str, out_path: str, voice: str, rate: int) -> None:
    txt_path = out_path + ".txt"
    Path(txt_path).write_text(text, encoding="utf-8")
    log.debug("Running `say` → %s  (voice=%s, rate=%d)", out_path, voice, rate)
    try:
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", out_path,
             "--data-format=aac", "-f", txt_path],
            check=True,
            capture_output=True,
        )
        log.debug("TTS complete: %s", out_path)
    except subprocess.CalledProcessError as exc:
        log.error(
            "`say` failed for '%s': returncode=%d stderr=%s",
            out_path, exc.returncode,
            exc.stderr.decode(errors="replace").strip(),
        )
        raise
    finally:
        if os.path.exists(txt_path):
            os.unlink(txt_path)


def check_say_voice(voice: str) -> str:
    log.info("Checking available macOS voices (requested: '%s')", voice)
    try:
        result = subprocess.run(
            ["say", "-v", "?"], capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        log.exception("Failed to list macOS voices")
        sys.exit("❌ Could not query macOS voices.")

    available = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    if not available:
        log.error("No macOS voices found")
        sys.exit("❌ No macOS voices found. Check System Settings → Accessibility → Spoken Content.")
    if voice not in available:
        fallback = available[0]
        log.warning("Voice '%s' not found — falling back to '%s'", voice, fallback)
        print(f"⚠️  Voice '{voice}' not found — using '{fallback}' instead.")
        return fallback
    log.info("Voice confirmed: '%s'", voice)
    return voice


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def _check_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True)
            log.debug("%s found and functional", tool)
        except FileNotFoundError:
            log.error("%s not found on PATH", tool)
            sys.exit(f"❌ {tool} not found. Install with:  brew install ffmpeg")


def _get_duration_ms(path: str) -> int:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        duration_ms = int(float(data["format"]["duration"]) * 1000)
        log.debug("Duration of '%s': %d ms", path, duration_ms)
        return duration_ms
    except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError):
        log.exception("Failed to probe duration of '%s'", path)
        raise


def build_m4b(audio_files: list[str], chapter_titles: list[str],
              book_title: str, output_path: str) -> None:
    log.info("Building M4B: '%s' from %d audio file(s)", output_path, len(audio_files))
    base = Path(output_path).parent
    concat_txt = base / "_concat.txt"
    concat_txt.write_text(
        "".join(f"file '{f}'\n" for f in audio_files), encoding="utf-8"
    )

    meta_txt = base / "_meta.txt"
    lines = [";FFMETADATA1\n", f"title={book_title}\n", "artist=Apple TTS\n\n"]

    duration_iter = (
        tqdm(zip(chapter_titles, audio_files), desc="⏱️  Computing durations",
             total=len(audio_files), unit="ch", colour="blue")
        if HAS_TQDM
        else zip(chapter_titles, audio_files)
    )

    offset_ms = 0
    for title, path in duration_iter:
        dur = _get_duration_ms(path)
        lines += [
            "[CHAPTER]\n", "TIMEBASE=1/1000\n",
            f"START={offset_ms}\n", f"END={offset_ms + dur}\n",
            f"title={title}\n\n",
        ]
        log.debug("Chapter '%s': start=%d ms, duration=%d ms", title, offset_ms, dur)
        offset_ms += dur

    meta_txt.write_text("".join(lines), encoding="utf-8")
    log.info("Total M4B duration: %d ms (%.1f min)", offset_ms, offset_ms / 60_000)

    print("🎬 Stitching M4B …")
    log.info("Running ffmpeg stitch → %s", output_path)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat_txt), "-i", str(meta_txt),
             "-map_metadata", "1", "-c:a", "aac", "-b:a", "64k", output_path],
            check=True, capture_output=True,
        )
        log.info("ffmpeg stitch successful: %s", output_path)
    except subprocess.CalledProcessError as exc:
        log.exception(
            "ffmpeg failed: returncode=%d stderr=%s",
            exc.returncode,
            exc.stderr.decode(errors="replace").strip(),
        )
        raise
    finally:
        concat_txt.unlink(missing_ok=True)
        meta_txt.unlink(missing_ok=True)


# ── Download with progress ────────────────────────────────────────────────────

def _download_epub(url: str, dest: Path) -> None:
    """Download a file with a tqdm progress bar (falls back to plain urlretrieve)."""
    log.info("Downloading EPUB from: %s → %s", url, dest)
    try:
        if not HAS_TQDM:
            print("⬇️  Downloading EPUB …")
            urllib.request.urlretrieve(url, dest)
        else:
            with urllib.request.urlopen(url) as response:
                total = int(response.headers.get("Content-Length", 0)) or None
                with (
                    tqdm(total=total, unit="B", unit_scale=True,
                         desc="⬇️  Downloading EPUB", colour="green") as bar,
                    open(dest, "wb") as fh,
                ):
                    chunk_size = 8192
                    while chunk := response.read(chunk_size):
                        fh.write(chunk)
                        bar.update(len(chunk))
        log.info("Download complete: %s (%.1f KB)", dest, dest.stat().st_size / 1024)
    except Exception:
        log.exception("Download failed for URL: %s", url)
        raise


# ── Main conversion ───────────────────────────────────────────────────────────

def convert(epub_source: str, output_path: str = DEFAULT_OUTPUT,
            voice: str = DEFAULT_VOICE, rate: int = DEFAULT_RATE) -> None:
    log.info("=== Conversion started: epub=%s out=%s voice=%s rate=%d ===",
             epub_source, output_path, voice, rate)

    if not HAS_TQDM:
        print("💡 Tip: install tqdm for progress bars  (pip install tqdm)")

    _check_ffmpeg()
    voice = check_say_voice(voice)

    with tempfile.TemporaryDirectory(prefix="epub2m4b_") as tmp_dir:
        tmp = Path(tmp_dir)
        log.debug("Temporary directory: %s", tmp_dir)

        if epub_source.startswith("http"):
            epub_path = tmp / "book.epub"
            _download_epub(epub_source, epub_path)
        else:
            epub_path = Path(epub_source)
            if not epub_path.exists():
                log.error("Local EPUB not found: %s", epub_path)
                sys.exit(f"❌ File not found: {epub_path}")

        chapters = extract_chapters(str(epub_path))
        if not chapters:
            log.error("No content chapters found in EPUB: %s", epub_source)
            sys.exit("❌ No content chapters found in EPUB.")
        print(f"✅ Found {len(chapters)} chapter(s).")

        audio_files: list[str] = []
        titles:      list[str] = []

        chapter_iter = (
            tqdm(enumerate(chapters, start=1), desc="🔊 Synthesising audio",
                 total=len(chapters), unit="ch", colour="yellow")
            if HAS_TQDM
            else enumerate(chapters, start=1)
        )

        for i, ch in chapter_iter:
            if HAS_TQDM:
                chapter_iter.set_postfix(chapter=ch["title"][:40])  # type: ignore[union-attr]
            else:
                print(f"🔊 [{i}/{len(chapters)}] {ch['title']}")

            log.info("Synthesising chapter %d/%d: '%s'", i, len(chapters), ch["title"])
            m4a = str(tmp / f"ch_{i:03d}.m4a")
            try:
                say_to_m4a(ch["text"], m4a, voice=voice, rate=rate)
                audio_files.append(m4a)
                titles.append(ch["title"])
                log.info("Chapter %d synthesised OK → %s", i, m4a)
            except subprocess.CalledProcessError as exc:
                log.warning("Chapter %d skipped due to `say` error: %s", i, exc)
                print(f"   ⚠️  Skipped (say error): {exc}")

        if not audio_files:
            log.error("No audio was generated — all chapters failed")
            sys.exit("❌ No audio was generated.")

        log.info("Audio synthesis complete: %d/%d chapter(s) succeeded",
                 len(audio_files), len(chapters))

        book_title = Path(output_path).stem.replace("_", " ")
        build_m4b(audio_files, titles, book_title, output_path)

    log.info("=== Conversion finished: %s ===", output_path)
    print(f"\n✅ Done!  →  {output_path}")
    print(f"📋 Log written to: {LOG_FILE}")


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
    try:
        args = _parse_args()
        convert(epub_source=args.epub, output_path=args.out,
                voice=args.voice, rate=args.rate)
    except Exception:
        logging.exception("Unhandled exception occurred")
        sys.exit(1)
