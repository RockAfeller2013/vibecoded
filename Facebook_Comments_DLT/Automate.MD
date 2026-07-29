```
Browser UI Reverse Engineering: Capture Mouse Clicks and Export Logs

This process uses the Chrome Developer Console to capture UI interactions,
record the clicked elements, and export the data into ChatGPT for analysis.

Use this when you need to automate a website workflow where the HTML
selectors are unknown or have changed.


1. Open Chrome Developer Tools

1. Open the website.
2. Press:

   macOS:            Cmd + Option + I
   Windows/Linux:     F12

3. Open the Console tab.

If Chrome blocks pasting, type:

    allow pasting

and press Enter.


2. Start the Click Recorder

Paste this into the Console:

    window.fbClickLog = [];

    document.addEventListener('click', function (e) {
        const el = e.target.closest('*');

        if (!el) {
            return;
        }

        const data = {
            time: new Date().toISOString(),
            tag: el.tagName,
            text: (el.innerText || '').trim().substring(0, 200),
            aria: el.getAttribute('aria-label'),
            role: el.getAttribute('role'),
            name: el.getAttribute('name'),
            type: el.getAttribute('type'),
            class: el.className?.toString().substring(0, 200),
            html: el.outerHTML.substring(0, 1000)
        };

        window.fbClickLog.push(data);

        console.log('CLICK:', data);

    }, true);

    console.log('Click recorder enabled');

Expected output:

    Click recorder enabled


3. Perform the Workflow Manually

Now perform the actions you want to automate.

Example:

    Click Select All
    Click Remove
    Click Confirm Remove

Do not refresh the page while recording.

The recorder captures:

  - HTML element type
  - Visible text
  - aria-label
  - role
  - name attributes
  - CSS classes
  - HTML structure
  - Click order
  - Timestamp


4. Check Captured Clicks

See how many clicks were recorded:

    window.fbClickLog.length

Example:

    6

Display the full log:

    JSON.stringify(window.fbClickLog, null, 2)


5. Copy the Log to Clipboard

Run:

    copy(JSON.stringify(window.fbClickLog, null, 2))

Chrome will copy the JSON silently.

Paste directly into ChatGPT:

    Cmd + V
or:
    Ctrl + V


6. Filter Large Logs Before Copying

For large workflows, reduce the noise:

    copy(JSON.stringify(
        window.fbClickLog.map(x => ({
            tag: x.tag,
            text: x.text,
            aria: x.aria,
            role: x.role,
            name: x.name,
            type: x.type,
            class: x.class
        })),
        null,
        2
    ))


7. Capture Only Interesting Actions

Example: only buttons, menus, remove/delete actions:

    copy(JSON.stringify(
        window.fbClickLog.filter(x =>
            x.text.match(/remove|delete|save|submit|confirm|select/i) ||
            x.aria
        ),
        null,
        2
    ))


8. Reset the Recorder

Clear previous recordings:

    window.fbClickLog = [];

Verify:

    window.fbClickLog.length

Expected:

    0


9. Stop the Recorder

Find the event listener:

    getEventListeners(document).click

Remove it by refreshing the page:

    CTRL + R
or:
    CMD + R


10. What to Ask ChatGPT After Uploading the Log

Example prompt:

    Analyse this browser click log.

    Identify:
    1. The stable selector for each action.
    2. Which selectors are dynamic and should be avoided.
    3. Create a JavaScript automation script.
    4. Use the most reliable selectors possible:
       - aria-label
       - name
       - role
       - data attributes
       - text fallback


Recommended Analysis Order

When reviewing captured logs, prioritise selectors in this order:

    1. name attribute
    2. aria-label
    3. data-* attributes
    4. role + text
    5. stable class names
    6. XPath / DOM position (avoid if possible)

Avoid relying on classes like:

    x1i10hfl
    x9f619
    x78zum5

These are React-generated Facebook classes and change frequently.

Prefer:

    <input name="comet_activity_log_select_all_checkbox">

over:

    .x1i10hfl.x9f619.x78zum5

This workflow can be reused for most modern web applications (Facebook,
Jira, ServiceNow, SaaS portals, admin consoles, etc.).
```
