#!/usr/bin/env python3
"""
ePUB → MP3 Audiobook Converter for macOS
─────────────────────────────────────────
Uses Apple's built-in `say` command (no API key, fully offline).
Zero third-party dependencies — stdlib only (zipfile, xml, html.parser).

Requirements:
  brew install ffmpeg                         # stitch chapters → MP3
  pip install alive-progress halo             # progress bars + spinners

Usage:
  python3 epub2mp3.py
  python3 epub2mp3.py --voice Samantha --rate 175
  python3 epub2mp3.py --epub /path/to/local.epub --out mybook.mp3

List available macOS voices:
  say -v ?
"""

import argparse
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

# ── Optional UI libraries ─────────────────────────────────────────────────────

try:
    from alive_progress import alive_bar
    HAS_ALIVE = True
except ImportError:
    HAS_ALIVE = False

try:
    from halo import Halo
    HAS_HALO = True
except ImportError:
    HAS_HALO = False

if not HAS_ALIVE or not HAS_HALO:
    _missing = ", ".join(
        p for p, ok in [("alive-progress", HAS_ALIVE), ("halo", HAS_HALO)] if not ok
    )
    print(f"💡 Tip: pip install {_missing}  — enables progress bars & spinners")


def _spinner(text: str):
    """Return a Halo spinner context-manager, or a no-op shim if Halo is absent."""
    if HAS_HALO:
        return Halo(text=text, spinner="dots", color="cyan")

    class _Noop:
        def __enter__(self): print(f"  {text}"); return self
        def __exit__(self, *_): pass
        def succeed(self, msg=""): print(f"  ✔  {msg or text}")
        def fail(self, msg=""):    print(f"  ✖  {msg or text}")
        def warn(self, msg=""):    print(f"  ⚠  {msg or text}")

    return _Noop()


# ── Logging ──────────────────────────────────────────────────────────────────

LOG_FILE = "epub2mp3.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
DEFAULT_OUTPUT = "Affirmations_Principles_2026.mp3"
DEFAULT_VOICE  = "Samantha"
DEFAULT_RATE   = 175

# ── Filters ──────────────────────────────────────────────────────────────────

SKIP_NAME_PATTERNS = re.compile(
    r"(toc|nav|cover|copyright|title.?page|colophon|halftitle|frontmatter)",
    re.IGNORECASE,
)
PAGE_LINE_RE  = re.compile(r"^\s*(\d{1,4}|[ivxlcdmIVXLCDM]{1,6})\s*$")
NOISE_LINE_RE = re.compile(
    r"^\s*(page|pg|p\.?)\s*\d+\s*$"
    r"|^\s*[-–—·•]\s*$"
    r"|^\s*\*{1,5}\s*$",
    re.IGNORECASE,
)

# ── HTML text extractor ───────────────────────────────────────────────────────

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


# ── EPUB parsing ──────────────────────────────────────────────────────────────

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

        manifest: dict[str, str] = {}
        for item in opf_root.findall(f".//{{{OPF}}}item"):
            media = item.get("media-type", "")
            href  = item.get("href", "")
            if "html" in media or href.endswith((".html", ".xhtml", ".htm")):
                manifest[item.get("id", "")] = href

        log.debug("Manifest HTML items found: %d", len(manifest))

        spine_hrefs: list[str] = []
        for itemref in opf_root.findall(f".//{{{OPF}}}itemref"):
            idref = itemref.get("idref", "")
            if idref in manifest:
                spine_hrefs.append(manifest[idref])
        if not spine_hrefs:
            log.warning("Spine is empty — falling back to manifest order")
            spine_hrefs = list(manifest.values())

        log.debug("Spine items to process: %d", len(spine_hrefs))

        # ── alive_bar: spine parsing ──────────────────────────────────────
        def _parse_spine(bar=None):
            for href in spine_hrefs:
                if SKIP_NAME_PATTERNS.search(href.split("/")[-1]):
                    log.debug("Skipping front/back-matter: %s", href)
                    if bar:
                        bar()
                    continue

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
                    log.warning("Spine entry not found in ZIP: %s", href)
                    if bar:
                        bar()
                    continue

                title, text = _extract_chapter_text(content)
                word_count = len(text.split())
                if word_count < 50:
                    log.debug("Skipping '%s' — %d words (below threshold)", href, word_count)
                    if bar:
                        bar()
                    continue

                chapters.append({
                    "title": title or f"Section {len(chapters) + 1}",
                    "text":  text,
                })
                log.info("Accepted chapter %d: '%s' (%d words)",
                         len(chapters), chapters[-1]["title"], word_count)
                if bar:
                    bar.text(f"→ {chapters[-1]['title'][:50]}")
                    bar()

        if HAS_ALIVE:
            with alive_bar(len(spine_hrefs), title="📖 Parsing EPUB",
                           bar="filling", spinner="classic") as bar:
                _parse_spine(bar)
        else:
            print("📖 Parsing EPUB …")
            _parse_spine()

    log.info("Chapter extraction complete — %d chapter(s) found", len(chapters))
    return chapters


# ── macOS TTS ─────────────────────────────────────────────────────────────────

_CHUNK_SIZE = 5  # paragraphs per `say` call


def _say_chunk(text: str, out_path: str, voice: str, rate: int) -> None:
    """Synthesise a text chunk to an MP3 file.

    `say` natively outputs AIFF; ffmpeg then converts that to MP3.
    The intermediate AIFF is deleted on exit regardless of success/failure.
    """
    txt_path  = out_path + ".txt"
    aiff_path = out_path + ".aiff"
    Path(txt_path).write_text(text, encoding="utf-8")
    try:
        # Step 1 — Apple TTS → AIFF
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", aiff_path, "-f", txt_path],
            check=True,
            capture_output=True,
        )
        # Step 2 — AIFF → MP3  (128 kbps, good quality for speech)
        subprocess.run(
            ["ffmpeg", "-y", "-i", aiff_path,
             "-codec:a", "libmp3lame", "-b:a", "128k", "-q:a", "2", out_path],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        log.error(
            "`say`/ffmpeg failed for chunk '%s': returncode=%d stderr=%s",
            out_path, exc.returncode,
            exc.stderr.decode(errors="replace").strip(),
        )
        raise
    finally:
        if os.path.exists(txt_path):
            os.unlink(txt_path)
        if os.path.exists(aiff_path):
            os.unlink(aiff_path)


def _concat_chunks(chunk_paths: list[str], out_path: str) -> None:
    concat_file = out_path + "_concat.txt"
    Path(concat_file).write_text(
        "".join(f"file '{p}'\n" for p in chunk_paths), encoding="utf-8"
    )
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", concat_file, "-c:a", "copy", out_path],
            check=True,
            capture_output=True,
        )
    finally:
        if os.path.exists(concat_file):
            os.unlink(concat_file)


def say_to_mp3(text: str, out_path: str, voice: str, rate: int,
               chapter_label: str = "") -> None:
    """
    Synthesise *text* → *out_path* (.mp3).
    Text is split into paragraph chunks; alive_bar ticks on every chunk.
    """
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks = [
        "\n\n".join(paragraphs[i : i + _CHUNK_SIZE])
        for i in range(0, len(paragraphs), _CHUNK_SIZE)
    ]

    log.debug("say_to_mp3: %d paragraph(s) → %d chunk(s) → %s",
              len(paragraphs), len(chunks), out_path)

    base = Path(out_path).parent
    stem = Path(out_path).stem
    chunk_paths: list[str] = []

    short_label = (chapter_label[:42] + "…") if len(chapter_label) > 42 else chapter_label
    title_str   = f"  ↳ {short_label}" if short_label else "  ↳ synthesising"

    # ── alive_bar: per-chunk synthesis ────────────────────────────────────
    def _synth(bar=None):
        for idx, chunk_text in enumerate(chunks):
            chunk_path = str(base / f"{stem}_chunk{idx:04d}.mp3")
            _say_chunk(chunk_text, chunk_path, voice, rate)
            chunk_paths.append(chunk_path)
            log.debug("Chunk %d/%d done: %s", idx + 1, len(chunks), chunk_path)
            if bar:
                bar()

    try:
        if HAS_ALIVE:
            with alive_bar(len(chunks), title=title_str,
                           bar="smooth", spinner="waves", force_tty=True) as bar:
                _synth(bar)
        else:
            print(f"{title_str} ({len(chunks)} chunk(s))")
            _synth()

        if len(chunk_paths) == 1:
            os.rename(chunk_paths[0], out_path)
        else:
            _concat_chunks(chunk_paths, out_path)
            log.debug("Chunks concatenated → %s", out_path)
    finally:
        for p in chunk_paths:
            if os.path.exists(p):
                os.unlink(p)


def check_say_voice(voice: str) -> str:
    log.info("Checking available macOS voices (requested: '%s')", voice)
    with _spinner(f"Checking voice '{voice}' …") as sp:
        try:
            result = subprocess.run(
                ["say", "-v", "?"], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError:
            log.exception("Failed to list macOS voices")
            sp.fail("Could not query macOS voices")
            sys.exit(1)

        available = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
        if not available:
            log.error("No macOS voices found")
            sp.fail("No macOS voices found")
            sys.exit("❌ Check System Settings → Accessibility → Spoken Content.")

        if voice not in available:
            fallback = available[0]
            log.warning("Voice '%s' not found — falling back to '%s'", voice, fallback)
            sp.warn(f"Voice '{voice}' not found — using '{fallback}'")
            return fallback

        sp.succeed(f"Voice ready: {voice}")
        log.info("Voice confirmed: '%s'", voice)
        return voice


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def _check_ffmpeg():
    with _spinner("Checking ffmpeg …") as sp:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            log.debug("ffmpeg found and functional")
            sp.succeed("ffmpeg found")
        except FileNotFoundError:
            log.error("ffmpeg not found on PATH")
            sp.fail("ffmpeg not found — install with: brew install ffmpeg")
            sys.exit(1)

def build_mp3(audio_files: list[str], chapter_titles: list[str],
              book_title: str, output_path: str) -> None:
    """Concatenate per-chapter MP3s into one final MP3.

    Note: the MP3 format does not support native chapter markers, so chapters
    are simply joined in order.  ID3 tags (title / artist) are written via
    ffmpeg's metadata flags.
    """
    log.info("Building MP3: '%s' from %d audio file(s)", output_path, len(audio_files))
    base = Path(output_path).parent
    concat_txt = base / "_concat.txt"
    concat_txt.write_text(
        "".join(f"file '{f}'\n" for f in audio_files), encoding="utf-8"
    )

    with _spinner("🎬 Stitching MP3 …") as sp:
        log.info("Running ffmpeg stitch → %s", output_path)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(concat_txt),
                 "-codec:a", "libmp3lame", "-b:a", "128k", "-q:a", "2",
                 "-metadata", f"title={book_title}",
                 "-metadata", "artist=Apple TTS",
                 output_path],
                check=True, capture_output=True,
            )
            log.info("ffmpeg stitch successful: %s", output_path)
            sp.succeed(f"MP3 written → {output_path}")
        except subprocess.CalledProcessError as exc:
            log.exception(
                "ffmpeg failed: returncode=%d stderr=%s",
                exc.returncode, exc.stderr.decode(errors="replace").strip(),
            )
            sp.fail("ffmpeg stitch failed — see log for details")
            raise
        finally:
            concat_txt.unlink(missing_ok=True)


# ── Download with progress ────────────────────────────────────────────────────

def _download_epub(url: str, dest: Path) -> None:
    log.info("Downloading EPUB from: %s → %s", url, dest)
    try:
        if HAS_ALIVE:
            with urllib.request.urlopen(url) as response:
                total = int(response.headers.get("Content-Length", 0)) or None
                with alive_bar(total, title="⬇  Downloading EPUB",
                               bar="filling", spinner="classic",
                               unit="B", scale="SI") as bar:
                    chunk_size = 8192
                    with open(dest, "wb") as fh:
                        while chunk := response.read(chunk_size):
                            fh.write(chunk)
                            bar(len(chunk))
        else:
            with _spinner("⬇  Downloading EPUB …") as sp:
                urllib.request.urlretrieve(url, dest)
                sp.succeed("Download complete")

        log.info("Download complete: %s (%.1f KB)", dest, dest.stat().st_size / 1024)
    except Exception:
        log.exception("Download failed for URL: %s", url)
        raise


# ── Main conversion ───────────────────────────────────────────────────────────

def convert(epub_source: str, output_path: str = DEFAULT_OUTPUT,
            voice: str = DEFAULT_VOICE, rate: int = DEFAULT_RATE) -> None:
    log.info("=== Conversion started: epub=%s out=%s voice=%s rate=%d ===",
             epub_source, output_path, voice, rate)

    _check_ffmpeg()
    voice = check_say_voice(voice)

    with tempfile.TemporaryDirectory(prefix="epub2mp3_") as tmp_dir:
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
        print(f"\n✅ Found {len(chapters)} chapter(s).\n")

        audio_files: list[str] = []
        titles:      list[str] = []

        # ── alive_bar: outer chapter loop ─────────────────────────────────
        def _process_chapters(bar=None):
            for i, ch in enumerate(chapters, start=1):
                label = f"[{i}/{len(chapters)}] {ch['title']}"
                if bar:
                    bar.text(f"🔊 {ch['title'][:55]}")
                else:
                    print(f"\n🔊 {label}")

                log.info("Synthesising chapter %d/%d: '%s'", i, len(chapters), ch["title"])
                mp3 = str(tmp / f"ch_{i:03d}.mp3")
                try:
                    say_to_mp3(ch["text"], mp3, voice=voice, rate=rate,
                               chapter_label=ch["title"])
                    audio_files.append(mp3)
                    titles.append(ch["title"])
                    log.info("Chapter %d synthesised OK → %s", i, mp3)
                except subprocess.CalledProcessError as exc:
                    log.warning("Chapter %d skipped due to `say` error: %s", i, exc)
                    print(f"   ⚠️  Skipped (say error): {exc}")

                if bar:
                    bar()

        if HAS_ALIVE:
            with alive_bar(len(chapters), title="🔊 Synthesising chapters",
                           bar="smooth", spinner="waves") as bar:
                _process_chapters(bar)
        else:
            _process_chapters()

        if not audio_files:
            log.error("No audio was generated — all chapters failed")
            sys.exit("❌ No audio was generated.")

        log.info("Audio synthesis complete: %d/%d chapter(s) succeeded",
                 len(audio_files), len(chapters))

        book_title = Path(output_path).stem.replace("_", " ")
        build_mp3(audio_files, titles, book_title, output_path)

    log.info("=== Conversion finished: %s ===", output_path)
    print(f"\n✅ Done!  →  {output_path}")
    print(f"📋 Log written to: {LOG_FILE}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ePUB → MP3 converter (stdlib only, macOS)")
    p.add_argument("--epub",  default=DEFAULT_EPUB_URL,
                   help="Path or URL to the .epub file")
    p.add_argument("--out",   default=DEFAULT_OUTPUT,
                   help="Output .mp3 filename")
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
