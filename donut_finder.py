import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageGrab
import pytesseract
import csv
import os
import datetime
import threading
from pynput import keyboard

# --- CONFIGURATION ---
OUTPUT_FILE = 'donut_data.csv'
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class AreaSelector:
    """Semi-transparent full-screen overlay for selecting the screen region."""
    def __init__(self, parent_callback):
        self.callback = parent_callback
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(background='grey')
        self.root.attributes('-topmost', True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=3)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        self.root.destroy()
        # Send coordinates back to main app
        if x2 - x1 > 10 and y2 - y1 > 10:
            self.callback((x1, y1, x2, y2))

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Donut OCR Dashboard")
        self.root.geometry("500x700")
        
        self.bbox = None
        self.is_monitoring = False
        self.listener = None

        # --- GUI LAYOUT ---
        
        # 1. Inputs Section
        input_frame = ttk.LabelFrame(root, text="User Parameters", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Recipe Name:").grid(row=0, column=0, sticky="w")
        self.entry_recipe = ttk.Entry(input_frame)
        self.entry_recipe.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(input_frame, text="Donut Type:").grid(row=1, column=0, sticky="w")
        self.entry_donut = ttk.Entry(input_frame)
        self.entry_donut.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(input_frame, text="Flavor Score 1 (Int):").grid(row=2, column=0, sticky="w")
        self.entry_score1 = ttk.Entry(input_frame)
        self.entry_score1.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(input_frame, text="Flavor Score 2 (Int):").grid(row=3, column=0, sticky="w")
        self.entry_score2 = ttk.Entry(input_frame)
        self.entry_score2.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        input_frame.columnconfigure(1, weight=1)

        # 2. Controls Section
        control_frame = ttk.LabelFrame(root, text="Controls", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.btn_area = ttk.Button(control_frame, text="Define Capture Area", command=self.open_selector)
        self.btn_area.pack(fill="x", pady=2)

        self.btn_monitor = ttk.Button(control_frame, text="Start Monitoring (SPACE to Capture)", command=self.toggle_monitoring)
        self.btn_monitor.pack(fill="x", pady=2)
        
        # State Label
        self.lbl_status = ttk.Label(control_frame, text="Status: IDLE", foreground="red", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=5)

        # 3. Preview Section
        preview_frame = ttk.LabelFrame(root, text="Last Capture Preview", padding=10)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.lbl_preview = ttk.Label(preview_frame, text="No capture yet.")
        self.lbl_preview.pack(fill="both", expand=True)

        # 4. Quit
        ttk.Button(root, text="Close Program", command=self.on_close).pack(pady=10)

    def open_selector(self):
        self.root.iconify() # Minimize main window
        AreaSelector(self.set_bbox)

    def set_bbox(self, bbox):
        self.bbox = bbox
        self.root.deiconify() # Restore main window
        self.lbl_status.config(text=f"Area Defined: {bbox}", foreground="orange")

    def toggle_monitoring(self):
        if not self.bbox:
            messagebox.showwarning("Warning", "Please define a capture area first.")
            return

        if self.is_monitoring:
            # Stop Monitoring
            self.is_monitoring = False
            self.btn_monitor.config(text="Start Monitoring (SPACE to Capture)")
            self.lbl_status.config(text="Status: PAUSED", foreground="red")
            if self.listener:
                self.listener.stop()
        else:
            # Start Monitoring
            self.is_monitoring = True
            self.btn_monitor.config(text="STOP Monitoring")
            self.lbl_status.config(text="Status: MONITORING (Press Spacebar)", foreground="green")
            
            # Start global keyboard listener in a separate thread
            self.listener = keyboard.Listener(on_release=self.on_key_release)
            self.listener.start()

    def on_key_release(self, key):
        if key == keyboard.Key.space and self.is_monitoring:
            # We must schedule the capture on the Main Thread (Tkinter isn't thread safe)
            self.root.after(0, self.perform_capture)

    def perform_capture(self):
        if not self.bbox: return
        
        try:
            # 1. Capture
            img = ImageGrab.grab(self.bbox)
            
            # 2. Update Preview (Resize for GUI)
            display_img = img.copy()
            display_img.thumbnail((400, 200)) # Fit to window
            self.tk_image = ImageTk.PhotoImage(display_img) # Keep reference!
            self.lbl_preview.config(image=self.tk_image, text="")

            # 3. OCR
            text = pytesseract.image_to_string(img, config='--psm 6')
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Pad/Truncate to 3 lines
            ocr_data = lines[:3]
            while len(ocr_data) < 3:
                ocr_data.append("")

            # 4. Get User Inputs
            recipe = self.entry_recipe.get()
            donut = self.entry_donut.get()
            s1 = self.entry_score1.get()
            s2 = self.entry_score2.get()

            # 5. Save
            self.save_to_csv(recipe, donut, s1, s2, ocr_data)
            
            # Flash success
            self.lbl_status.config(text="CAPTURED & SAVED!", foreground="blue")
            self.root.after(1000, lambda: self.lbl_status.config(text="Status: MONITORING (Press Spacebar)", foreground="green"))

        except Exception as e:
            print(e)
            self.lbl_status.config(text=f"Error: {str(e)}", foreground="red")

    def save_to_csv(self, recipe, donut, s1, s2, ocr_lines):
        file_exists = os.path.isfile(OUTPUT_FILE)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [timestamp, recipe, donut, s1, s2] + ocr_lines
        
        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                headers = ['Timestamp', 'Recipe', 'Donut Type', 'Score 1', 'Score 2', 'OCR Line 1', 'OCR Line 2', 'OCR Line 3']
                writer.writerow(headers)
            writer.writerow(row)

    def on_close(self):
        if self.listener:
            self.listener.stop()
        self.root.destroy()
        os._exit(0) # Force kill threads

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()