import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from ebooklib import epub

BASE_URL = "https://paulgraham.com/"
INDEX_URL = BASE_URL + "articles.html"

# First three articles in order
PRIORITY_ARTICLES = [
    "https://paulgraham.com/greatwork.html",
    "https://paulgraham.com/selfindulgence.html",
    "https://paulgraham.com/kids.html"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PaulGrahamScraper/1.0)"}

def safe_filename(name):
    """Convert a string to a safe filename."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return re.sub(r'\s+', '_', name).strip('_')

def get_article_links():
    """Scrape all article URLs from the index page."""
    r = requests.get(INDEX_URL, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        if href.endswith(".html") and not href.startswith("index"):
            full_url = urljoin(BASE_URL, href)
            if full_url not in links:
                links.append(full_url)

    # Remove priority articles from the rest of the list to avoid duplication
    rest_links = [link for link in links if link not in PRIORITY_ARTICLES]
    return PRIORITY_ARTICLES + rest_links

def download_image(img_url):
    """Download an image and return its content and extension."""
    try:
        r = requests.get(img_url, headers=HEADERS)
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', '')
        ext = ''
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            ext = os.path.splitext(urlparse(img_url).path)[1] or '.img'
        return r.content, ext
    except Exception as e:
        print(f"Failed to download image {img_url}: {e}")
        return None, None

def extract_article(url):
    """Extract the title, main content, and download/replace inline images."""
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled"

    # Find main content - prefer <font> as Paul Graham uses it, fallback to <body>
    container = soup.find("font") or soup.find("body")
    if not container:
        return title, ""

    # Process images: download and embed, update src to internal epub paths
    imgs = container.find_all("img")
    images = []
    for i, img in enumerate(imgs):
        src = img.get('src')
        if not src:
            continue
        full_img_url = urljoin(url, src)
        content, ext = download_image(full_img_url)
        if content:
            # Create unique image filename
            img_name = f"image_{len(images)}{ext}"
            images.append((img_name, content))
            # Update img tag src to point to local file inside EPUB
            img['src'] = f"images/{img_name}"
        else:
            # Remove broken img tag
            img.decompose()

    # Serialize container content including images updated
    body_content = str(container)

    return title, body_content, images

def create_epub(chapters):
    """Create EPUB file with Roboto font and embedded images."""
    book = epub.EpubBook()
    book.set_identifier("paul-graham-articles")
    book.set_title("Paul Graham Articles")
    book.set_language("en")
    book.add_author("Paul Graham")

    # Add Roboto font
    roboto_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
    font_path = "Roboto-Regular.ttf"
    if not os.path.exists(font_path):
        fr = requests.get(roboto_url)
        with open(font_path, "wb") as f:
            f.write(fr.content)
    with open(font_path, "rb") as f:
        font_content = f.read()
    font_item = epub.EpubItem(uid="Roboto", file_name="fonts/Roboto-Regular.ttf", media_type="application/x-font-ttf", content=font_content)
    book.add_item(font_item)

    # Style with Roboto font
    style = """
    @font-face {
        font-family: 'Roboto';
        src: url('fonts/Roboto-Regular.ttf');
    }
    body { font-family: 'Roboto', sans-serif; }
    img { max-width: 100%; height: auto; }
    """
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/style.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    epub_chapters = []
    # To add all images globally
    added_images = {}

    for idx, (title, content, images) in enumerate(chapters):
        filename = safe_filename(title) + ".xhtml"
        c = epub.EpubHtml(title=title, file_name=filename, lang="en")
        c.set_content(f"<html><head></head><body>{content}</body></html>")
        c.add_item(nav_css)

        # Add images for this chapter if not already added
        for img_name, img_data in images:
            if img_name not in added_images:
                img_item = epub.EpubItem(uid=img_name, file_name=f"images/{img_name}", media_type="image/jpeg", content=img_data)
                book.add_item(img_item)
                added_images[img_name] = img_item
            # EPUB chapters reference images by file_name, so no need to add again

        book.add_item(c)
        epub_chapters.append(c)

    book.toc = tuple(epub_chapters)
    book.spine = ["nav"] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub("PaulGrahamArticles.epub", book)

if __name__ == "__main__":
    all_links = get_article_links()
    chapters = []
    for url in all_links:
        print(f"Fetching {url}...")
        try:
            title, content, images = extract_article(url)
            if content.strip():
                chapters.append((title, content, images))
            else:
                print(f"Skipped {url} — no content found.")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        time.sleep(2)

    if not chapters:
        print("No chapters found. Exiting.")
    else:
        print("Creating EPUB...")
        create_epub(chapters)
        print("Done! Saved as PaulGrahamArticles.epub")
