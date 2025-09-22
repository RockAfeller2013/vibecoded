from PIL import Image, ImageOps, ImageFilter
import os, subprocess, sys, textwrap

image_path = "/mnt/data/m.png"
output_path = "/mnt/data/lovable_prompt_directory.md"

# Load image
img = Image.open(image_path)
w, h = img.size

# Prepare tiles
tile_w = min(2000, w)
tile_h = min(2000, h)

texts = []

def ocr_with_pytesseract(pil_img):
    try:
        import pytesseract
    except Exception as e:
        return None, str(e)
    # Preprocess
    gray = pil_img.convert("L")
    # Increase contrast and sharpen
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.SHARPEN)
    config = "--oem 3 --psm 6"
    try:
        txt = pytesseract.image_to_string(gray, config=config, lang='eng')
    except Exception as e:
        return None, str(e)
    return txt, None

def ocr_with_tesseract_cli(pil_img):
    # Save temporary crop
    tmp = "/mnt/data/_tmp_crop.png"
    pil_img.save(tmp)
    try:
        proc = subprocess.run(["tesseract", tmp, "stdout", "-l", "eng", "--psm", "6"],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            return proc.stdout, None
        else:
            return None, proc.stderr
    except Exception as e:
        return None, str(e)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

# Run OCR on full image first
full_txt, err = ocr_with_pytesseract(img)
if full_txt is None or len(full_txt.strip()) == 0:
    # try CLI tesseract
    full_txt, err = ocr_with_tesseract_cli(img)

if full_txt and len(full_txt.strip()) > 0:
    texts.append(full_txt)

# Slide over tiles
y = 0
while y < h:
    x = 0
    while x < w:
        box = (x, y, min(x + tile_w, w), min(y + tile_h, h))
        crop = img.crop(box)
        txt, err = ocr_with_pytesseract(crop)
        if txt is None or len(txt.strip()) == 0:
            txt, err = ocr_with_tesseract_cli(crop)
        if txt and len(txt.strip()) > 0:
            texts.append(txt)
        x += tile_w
    y += tile_h

# Combine and dedupe lines while preserving order
seen = set()
out_lines = []
for piece in texts:
    for line in piece.splitlines():
        line = line.strip()
        if not line:
            continue
        # Normalize common OCR errors
        norm = line.replace('\u2019', "'")
        if norm not in seen:
            seen.add(norm)
            out_lines.append(norm)

# If no text found, write a simple note
if len(out_lines) == 0:
    content = "# Lovable Prompt Directory\n\n*OCR returned no text. Tesseract may be unavailable or image is unreadable.*\n"
else:
    # Build markdown: group headings when possible
    content = "# Lovable Prompt Directory\n\n"
    content += "\n".join(out_lines)
    content += "\n"

# Save file
with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

output_path
