# This script, deletes all facebook comments continuously

- Based on https://github.com/g-h-0-S-t/bot-del-fb-comments/tree/main, but this is old and facebook has changed its page.

- Open Facebook | Settings & Privacy | Activity Log | Comments | Posts
- Open Chrome | View | Developer Tools | JavaScript Console
- Tyoe allow pasting or allow posting
- then paste the script 


```javascript

const INTERVAL = 1500;

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
