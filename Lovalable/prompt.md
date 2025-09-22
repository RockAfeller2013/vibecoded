I have a sprite sheet that contains all frames of a GIF animation. Each frame has repeated text. I need you to perform OCR across the full sprite sheet, deduplicate any repeated text, and output the unique content in a single Markdown file.

Requirements:

Extract text from all frames (114 items).

Remove duplicates so each unique item appears once.

Structure the Markdown as:

# {Number}. {Title}
**Category:** {Category if present}

## Prompt
{Prompt content}

## Description
{Description content}


Ensure the final result is in one .md file that I can download.

Do not include frame images, only text.

Fix common OCR errors (quotes, spacing, dashes).
