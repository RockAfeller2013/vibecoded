# Playwright (Python) - Record and Replay Facebook Activity Log Actions

> This code is compatible with Python 3.10+

---

# Install

```bash
pip install playwright
playwright install
```

---

# 1. Record Browser Actions

Playwright can generate Python code from your mouse clicks and keyboard input.

```bash
playwright codegen https://www.facebook.com
```

Login to Facebook manually.

Perform:

```
Activity Log
↓
Comments
↓
All
↓
Remove
↓
Remove
```

Playwright continuously generates Python like:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto("https://www.facebook.com")

    page.get_by_role("button", name="All").click()

    page.get_by_role("button", name="Remove").click()

    page.get_by_role("button", name="Remove").click()

    browser.close()
```

---

# 2. Save Login

Login once.

```bash
playwright open https://www.facebook.com
```

After logging in:

```python
context.storage_state(path="facebook.json")
```

---

# 3. Replay Later

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        storage_state="facebook.json"
    )

    page = context.new_page()

    page.goto(
        "https://www.facebook.com/me/allactivity?category_key=COMMENTS"
    )

    browser.close()
```

---

# 4. Example Bulk Remover

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        storage_state="facebook.json"
    )

    page = context.new_page()

    page.goto(
        "https://www.facebook.com/me/allactivity?category_key=COMMENTS"
    )

    while True:

        checkbox = page.locator(
            'input[name="comet_activity_log_select_all_checkbox"]'
        )

        if checkbox.count() == 0:
            break

        checkbox.first.check()

        page.get_by_text(
            "Remove",
            exact=True
        ).first.click()

        page.get_by_text(
            "Remove",
            exact=True
        ).last.click()

        page.wait_for_timeout(5000)

    browser.close()
```

---

# 5. Record Better Selectors

Highlight an element:

```python
page.pause()
```

Playwright Inspector opens.

Click any element and it will show:

- CSS selector
- Playwright locator
- XPath

---

# 6. Useful Locator Examples

```python
page.get_by_text("Remove")
```

```python
page.get_by_role("button", name="Remove")
```

```python
page.get_by_label("Remove")
```

```python
page.locator(
    'input[name="comet_activity_log_select_all_checkbox"]'
)
```

```python
page.locator(
    'div[aria-label^="More options for"]'
)
```

---

# 7. Record an Existing Chrome Session

```bash
playwright codegen --target python https://www.facebook.com
```

or

```bash
playwright codegen --target python --save-storage facebook.json
```

This records your interactions and saves your authenticated session for replay.
