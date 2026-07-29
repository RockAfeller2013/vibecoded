# This script, deletes all facebook comments continuously

- Based on https://github.com/g-h-0-S-t/bot-del-fb-comments/tree/main, but this is old and facebook has changed its page.

- Open Facebook | Settings & Privacy | Activity Log | Comments | Posts
- Open Chrome | View | Developer Tools | JavaScript Console
- Tyoe allow pasting or allow posting
- then paste the script
- If Facebook starts skipping items, increase: const INTERVAL = 1500;

```javascript

const INTERVAL = 3500;

const timer = setInterval(() => {
  const options = [
    ...document.querySelectorAll('div[aria-label^="More options for"]')
  ];

  if (options.length === 0) {
    console.log("No more comments found");
    clearInterval(timer);
    return;
  }

  options[0].click();

  setTimeout(() => {
    const remove = [...document.querySelectorAll('*')]
      .find(x =>
        x.offsetParent &&
        x.innerText &&
        x.innerText.trim() === "Remove"
      );

    if (remove) {
      remove.click();

      setTimeout(() => {
        const confirm = [...document.querySelectorAll('*')]
          .find(x =>
            x.offsetParent &&
            x.innerText &&
            x.innerText.trim() === "Remove"
          );

        if (confirm) {
          confirm.click();
        }
      }, 800);
    }
  }, 800);

}, INTERVAL);

```

Click All | Click Remove | Click Remove popup

```
const INTERVAL = 8000;

function clickElement(el) {
    if (el) {
        el.click();
        console.log("Clicked:", el.innerText || el.getAttribute("aria-label"));
        return true;
    }
    return false;
}

function findRemoveButtons() {
    return [...document.querySelectorAll('*')]
        .filter(x =>
            x.offsetParent &&
            x.innerText &&
            x.innerText.trim() === "Remove"
        );
}

const timer = setInterval(() => {

    // 1. Select All checkbox
    const checkbox = document.querySelector(
        'input[name="comet_activity_log_select_all_checkbox"]'
    );

    if (!checkbox) {
        console.log("No select all checkbox found");
        return;
    }

    if (checkbox.getAttribute("aria-checked") !== "true") {
        clickElement(checkbox);
        return;
    }

    // 2. Click toolbar Remove
    const removes = findRemoveButtons();

    if (removes.length > 0) {
        clickElement(removes[0]);

        setTimeout(() => {
            // 3. Click confirmation Remove
            const confirmButtons = findRemoveButtons();

            if (confirmButtons.length > 0) {
                clickElement(confirmButtons[confirmButtons.length - 1]);
            }

        }, 2000);
    }

}, INTERVAL);
```

# Capture events - https://chatgpt.com/c/6a69dc7b-8d9c-83ec-bed9-3541c83154ad
