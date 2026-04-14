# My research to convert EPUB to a Reader app;

# ePUB → M4B Audiobook Converter

Convert any ePUB to a chapter-marked M4B audiobook using **Apple's built-in text-to-speech** — no API key, no internet connection required for synthesis, fully offline.

---

## Requirements

- macOS (uses the built-in `say` command)
- Python 3.8+
- [Homebrew](https://brew.sh) (for ffmpeg)

---

## One-Time Setup

Run these in Terminal before using the script for the first time:

```bash
pip install ebooklib beautifulsoup4 tqdm logging
brew install ffmpeg
```

---

## Usage

### Basic — downloads the ePUB automatically

```bash
python epub_to_m4b.py
```

### With options

```bash

python3 txt.py --voice Karen --rate 175 --epub book.epub --out book.m4b

python epub_to_m4b.py --voice Daniel --rate 160       # British voice, slower pace
python epub_to_m4b.py --voice Alex   --rate 190       # Alex voice, slightly faster
python epub_to_m4b.py --epub /path/to/local.epub --out mybook.m4b
```

### List all available voices on your Mac

```bash
say -v "?"
```

### All flags

| Flag | Default | Description |
|------|---------|-------------|
| `--epub` | Remote URL | Local path or URL to a `.epub` file |
| `--out` | `Affirmations_Principles_2026.m4b` | Output filename |
| `--voice` | `Samantha` | macOS voice name (see `say -v ?`) |
| `--rate` | `175` | Speaking rate in words per minute |

---

## How It Works

### 1 · Filtering

Before text-to-speech runs, the script strips all non-content from the ePUB:

- Documents named `toc`, `nav`, `cover`, `copyright`, `title-page`, etc. are skipped entirely
- Any HTML element with a class matching `pagenum`, `pagebreak`, `folio`, etc. is removed
- Any tag with `epub:type="pagebreak"` is removed
- Lines that are bare numbers (`42`), Roman numerals (`xiv`), or patterns like `Page 5` are dropped
- Any section with fewer than 50 words (decorative or boilerplate pages) is skipped

### 2 · Text-to-Speech

Each chapter is written to a temporary text file, then synthesised with:

```bash
say -v <voice> -r <rate> -f chapter.txt -o chapter.m4a --data-format=aac
```

Writing to a file (rather than passing text as an argument) avoids shell argument-length limits on long chapters.

### 3 · Assembly

`ffmpeg` concatenates all per-chapter M4A files into a single `.m4b` and injects an `ffmetadata` chapter map — so you get **named chapter markers** you can skip between in Books.app, Overcast, VLC, or any M4B-compatible player.

---

## Output

The finished `.m4b` file can be opened directly in:

- **Books.app** — double-click in Finder
- **VLC** — full chapter navigation
- **Overcast / Pocket Casts** — import via Files
- Any app that supports the M4B audiobook format

---

## Recommended Voices

| Voice | Character |
|-------|-----------|
| `Samantha` | Default US English, clear and natural |
| `Daniel` | British English, warm tone |
| `Alex` | US English, older macOS classic |
| `Karen` | Australian English |
| `Moira` | Irish English |
| `Tessa` | South African English |

Run `say -v ?` to see every voice installed on your machine. Additional voices can be downloaded in **System Settings → Accessibility → Spoken Content → System Voice → Manage Voices**.

---

## Troubleshooting

**`ffmpeg` not found**
```bash
brew install ffmpeg
```

**Voice not found warning**
Run `say -v ?` to list installed voices, then pass a valid name with `--voice`.

**Empty or very short audiobook**
The ePUB structure may use non-standard class names for page numbers. Open the `.epub` as a zip and inspect the HTML to identify the classes, then add them to `PAGE_CLASS_RE` in the script.

```
cd ~/Desktop/Audio
python3 -m venv venv
source venv/bin/activate
pip install ebooklib beautifulsoup4
python3 epub_to_m4b.py
```

```
source ~/Desktop/Audio/venv/bin/activate
python3 epub_to_m4b.py

```
---

## License

MIT — do whatever you like with it.
## Other
- https://claude.ai/chat/bbc7ef39-089e-4ce9-af3a-ee8eda58b99c
- Convert EPUB to MP3
- PWA App to read Epub
- Read a EPUB and convert to M4B using built in Apple Voice and create a MP3
- It automatically ignore pages numbers, etc. 
- https://www.google.com/search?q=python+text+to+voice+apple+speach&rlz=1C5CHFA_enAU890AU890&oq=python+text+to+voice+apple+speach&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIHCAEQIRigATIHCAIQIRigATIHCAMQIRigATIHCAQQIRigATIHCAUQIRiPAtIBCDY0MTFqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8#fpstate=ive&vld=cid:090d345c,vid:92Vy3N4VorI,st:170
- https://www.youtube.com/watch?v=L7n-5JhJFWY&t=22s
- https://developer.apple.com/documentation/appkit/nsspeechsynthesizer?changes=_2&changes=_2


```
# Simple macOS TTS using subprocess
import subprocess

def speak_macos(text):
    subprocess.call(['say', text])

speak_macos("Hello from Apple speech")

```

```
import os
os.system("say 'Hello World'")

```

```
import pyttsx3
engine = pyttsx3.init()
engine.say("Hello, this is offline speech.")
engine.runAndWait()

```

```
pip install pyobjc-framework-Cocoa
```

```
from AppKit import NSSpeechSynthesizer
import time

# Initialize the synthesizer
synth = NSSpeechSynthesizer.alloc().init()

# List available voices (optional)
# print(synth.availableVoices())

# Set a specific voice
voice = 'com.apple.speech.synthesis.voice.Alex'
synth.setVoice_(voice)

# Speak text
print("Speaking...")
synth.startSpeakingString_("Hello from Python using AppKit")

# Wait for speech to finish
while synth.isSpeaking():
    time.sleep(0.5)
print("Finished.")

```
