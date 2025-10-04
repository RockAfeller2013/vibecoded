# Paul Graham articles in EPUB format

Another Vibe-coded weekend project, I never had a chance to read all of Paul Graham’s essays as they are all online, and I prefer to read long form on my Kindle or Apple Books using the Speak Text feature. So this Python script converts all of his essays into an EPUB, or you can just download the EPUB

This will produce an EPUB with:

All Paul Graham articles.

Inline images downloaded and embedded properly

Roboto font embedded and styled

Clean chapter filenames to avoid EPUB errors

## How to use

Make sure you have dependencies installed:

```bash
pip install requests beautifulsoup4 ebooklib
python paulgraham_epub.py
```
