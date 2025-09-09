import os
import zipfile
from datetime import datetime

output_file = "Affirmations_Principles_2026.epub"

book_xhtml = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
    <title>Affirmations &amp; Principles 2026</title>
    <meta charset="utf-8"/>
    <style>
        body { font-family: serif; line-height: 1.6; margin: 5%; text-align: justify; }
        h1, h2 { text-align: center; page-break-after: avoid; }
        h1 { margin-bottom: 2em; }
        h2 { margin-top: 3em; margin-bottom: 1em; }
        .poem { font-style: italic; margin-left: 10%; margin-right: 10%; }
        .list { margin-left: 5%; }
    </style>
</head>
<body>
    <h1>Affirmations &amp; Principles 2026</h1>

    <h2>Affirmations</h2>
    <ul class="list">
        <li>I am confident and calm in all situations.</li>
        <li>I approach challenges with clarity and purpose.</li>
        <li>I trust my instincts and decisions.</li>
        <li>I communicate clearly and assertively.</li>
        <li>I am in control of my emotions and actions.</li>
        <li>I focus on solutions, not problems.</li>
        <li>I am resilient and adaptable to change.</li>
        <li>I learn and grow from every experience.</li>
        <li>I set boundaries with confidence and respect.</li>
        <li>I am worthy of success and happiness.</li>
    </ul>

    <h2>Mindset Principles</h2>
    <ul class="list">
        <li>Clarity over confusion – simplify decisions.</li>
        <li>Respond, don’t react.</li>
        <li>Focus on what you can control, release what you can’t.</li>
        <li>Progress is better than perfection.</li>
        <li>Discomfort means growth.</li>
        <li>Act with intent, not impulse.</li>
        <li>Patience compounds results.</li>
        <li>Consistency beats intensity.</li>
        <li>Silence can be power.</li>
        <li>Confidence comes from preparation and repetition.</li>
    </ul>

    <h2>Resilience Reminders</h2>
    <ul class="list">
        <li>Breathe, then act.</li>
        <li>Obstacles are stepping stones.</li>
        <li>Every setback carries a lesson.</li>
        <li>Persistence breaks resistance.</li>
        <li>Stay grounded, not shaken.</li>
        <li>You’ve overcome before, you’ll overcome again.</li>
    </ul>

    <h2>Closing Thought</h2>
    <p class="poem">
        “Confidence is silent. Strength is calm. Growth is steady.  
        Keep moving forward, one step at a time.”
    </p>
</body>
</html>
"""

title_xhtml = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <title>Affirmations &amp; Principles 2026</title>
  <meta charset="utf-8"/>
  <style>
    body { font-family: serif; text-align: center; margin-top: 40%; }
    h1 { font-size: 2em; }
    h2 { font-size: 1.5em; margin-top: 1em; }
  </style>
</head>
<body>
  <h1>Affirmations &amp; Principles 2026</h1>
  <h2>By Your Name</h2>
</body>
</html>
"""

container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0"
  xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf"
              media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package version="3.0"
         xmlns="http://www.idpf.org/2007/opf"
         unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">urn:uuid:12345678-1234-5678-1234-567812345678</dc:identifier>
    <dc:title>Affirmations &amp; Principles 2026</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>Your Name</dc:creator>
    <meta property="dcterms:modified">{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
  </metadata>

  <manifest>
    <item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>
    <item id="book" href="book.xhtml" media-type="application/xhtml+xml"/>
  </manifest>

  <spine>
    <itemref idref="title"/>
    <itemref idref="book"/>
  </spine>
</package>
"""

with zipfile.ZipFile(output_file, "w") as epub:
    epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    epub.writestr("META-INF/container.xml", container_xml)
    epub.writestr("OEBPS/title.xhtml", title_xhtml)
    epub.writestr("OEBPS/book.xhtml", book_xhtml)
    epub.writestr("OEBPS/content.opf", content_opf)

print(f"EPUB created: {output_file}")
