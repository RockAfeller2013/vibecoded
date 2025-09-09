# requirements.txt
# pyautogui
# opencv-python
# pyzbar

# Navigate to your project folder
# cd /path/to/your/project

# Create a virtual environment
# python3 -m venv qr-env

# Activate the virtual environment
# On Windows
# qr-env\Scripts\activate

# On macOS/Linux
# source qr-env/bin/activate

# Install the required packages
# pip install pyautogui opencv-python pyzbar

# Run your Python script
# python3 desktopqr.py

# Deactivate the virtual environment (optional)
# deactivate


import pyautogui
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Capture screenshot of the selected area
def capture_selected_area():
    print("Move your cursor to the top-left of the area, and press Enter")
    x1, y1 = pyautogui.position()
    input("Now move to the bottom-right of the area, and press Enter")
    x2, y2 = pyautogui.position()

    # Calculate width and height
    width = x2 - x1
    height = y2 - y1

    # Capture screenshot of the selected region
    screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
    return np.array(screenshot)

# Read QR code from the captured image
def read_qr_code(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    qr_codes = decode(gray)

    if qr_codes:
        for qr in qr_codes:
            qr_data = qr.data.decode('utf-8')
            print("QR Code Detected:", qr_data)
    else:
        print("No QR Code found")

if __name__ == "__main__":
    # Capture selected area
    img = capture_selected_area()

    # Read QR code from the image
    read_qr_code(img)
