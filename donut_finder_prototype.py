import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
import pytesseract
import csv
import os
import datetime

# CONFIGURATION
# If on Windows, point to your tesseract.exe if it's not in your PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

OUTPUT_FILE = 'output.csv'

class SnippingTool:
    def __init__(self):
        self.root = tk.Tk()
        
        # Make the window fullscreen and semi-transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(background='grey')
        
        # Variables to store coordinates
        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # Escape to exit without scanning
        self.root.bind("<Escape>", lambda e: self.root.quit())

        print("Select the area on your screen containing the 3 lines of text...")
        self.root.mainloop()

    def on_button_press(self, event):
        # Save starting coordinates
        self.start_x = event.x
        self.start_y = event.y
        # Create a rectangle (initially empty)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=2)

    def on_move_press(self, event):
        # Update the rectangle as the user drags
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        # Calculate coordinates
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        # Close the overlay immediately so it doesn't block the screenshot
        self.root.withdraw()
        self.root.quit()

        # Capture the screen area
        # Note: If you have a high-DPI display (Retina/4k), you might need coordinate scaling here.
        bbox = (x1, y1, x2, y2)
        print(f"Capturing area: {bbox}")
        
        # Provide a small delay to ensure the window is fully gone
        self.root.after(100, self.process_image(bbox))

    def process_image(self, bbox):
        try:
            # Grab the image
            img = ImageGrab.grab(bbox)
            
            # Run OCR
            # --psm 6 assumes a single uniform block of text
            text = pytesseract.image_to_string(img, config='--psm 6')
            
            # Clean up the text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            self.save_to_csv(lines)
            
        except Exception as e:
            print(f"Error: {e}")

    def save_to_csv(self, lines):
        # Ensure we have data
        if not lines:
            print("No text detected!")
            return

        # Handle cases where OCR might see more or fewer than 3 lines
        # We will pad with empty strings or truncate to fit 3 columns
        row_data = lines[:3]
        while len(row_data) < 3:
            row_data.append("")

        # Check if file exists to determine if we need a header
        file_exists = os.path.isfile(OUTPUT_FILE)
        
        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Optional: Write header if new file
            if not file_exists:
                writer.writerow(['Timestamp', 'Line 1', 'Line 2', 'Line 3'])
            
            # Add timestamp for record keeping
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp] + row_data)
            
        print(f"Success! Saved: {row_data}")

if __name__ == "__main__":
    SnippingTool()