
- Startup Landing Page Deployment https://aws.amazon.com/startups/prompt-library/startup-landing-page-deployment

# Always add Python Loging

```python
import logging
import sys

LOG_FILE = "log.txt"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    try:
        # Example code that may fail
        x = 10 / 0
        print(x)
    except Exception as e:
        logging.exception("Unhandled exception occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
```
