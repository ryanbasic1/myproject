import os
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import ImageGrab, Image
import pytesseract
from openai import OpenAI
import pyperclip
import keyboard
import pystray
from pystray import MenuItem as item
import datetime

# ---------- SETTINGS ----------
SETTINGS_FILE = "settings.txt"
LOG_FILE = "ocr_mistral_log.txt"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {
            "base_url": "http://127.0.0.1:1234/v1",
            "model_name": "mistralai/mistral-7b-instruct-v0.3"
        }
    with open(SETTINGS_FILE, "r") as f:
        lines = f.readlines()
        settings = {}
        for line in lines:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                settings[k] = v
        return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        for k, v in settings.items():
            f.write(f"{k}={v}\n")

settings = load_settings()

# ---------- LM STUDIO CLIENT ----------
client = OpenAI(
    base_url=settings["base_url"],
    api_key="lm-studio"
)
LOCAL_MODEL_NAME = settings["model_name"]

# ---------- CONNECTION TEST ----------
def test_connection():
    try:
        response = client.models.list()
        print("✅ Connected to LM Studio. Models available:")
        for m in response.data:
            print("   -", m.id)
        return True
    except Exception as e:
        print(f"❌ Could not connect to LM Studio: {e}")
        return False

# ---------- SETTINGS WINDOW ----------
def show_settings_window():
    root = tk.Tk()
    root.withdraw()
    base_url = simpledialog.askstring("Settings", "LM Studio Server URL:", initialvalue=settings["base_url"])
    model_name = simpledialog.askstring("Settings", "Model Name:", initialvalue=settings["model_name"])
    if base_url and model_name:
        settings["base_url"] = base_url
        settings["model_name"] = model_name
        save_settings(settings)
        messagebox.showinfo("Settings", "Settings saved. Please restart the app.")
    root.destroy()

# ---------- REGION SELECTOR ----------
class ScreenRegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.configure(background='black')
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="gray", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.start_x = self.start_y = 0
        self.rect = None
        self.bbox = None
    def on_click(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="yellow", width=2
        )
    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    def on_release(self, event):
        self.bbox = (
            min(self.start_x, event.x),
            min(self.start_y, event.y),
            max(self.start_x, event.x),
            max(self.start_y, event.y)
        )
        self.root.destroy()
    def get_bbox(self):
        self.root.mainloop()
        return self.bbox

# ---------- OCR & MISTRAL ----------
def log_interaction(ocr_text, mistral_response):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] OCR: {ocr_text}\n")
        f.write(f"[{datetime.datetime.now()}] Mistral: {mistral_response}\n\n")

def capture_text_from_selected_area():
    selector = ScreenRegionSelector()
    bbox = selector.get_bbox()
    if not bbox:
        return None
    try:
        screenshot = ImageGrab.grab(bbox)
        return pytesseract.image_to_string(screenshot).strip()
    except Exception as e:
        return f"OCR Error: {e}"

def ask_mistral(prompt):
    try:
        response = client.chat.completions.create(
            model=settings["model_name"],
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Mistral Error: {e}"

def show_popup(title, content):
    popup = tk.Tk()
    popup.withdraw()
    messagebox.showinfo(title, content)
    popup.destroy()

def handle_hotkey():
    print("🔹 Select a region on screen...")
    text = capture_text_from_selected_area()
    if not text or "Error" in text:
        show_popup("❌ Error", text or "No text detected.")
        return
    print(f"📝 OCR Text: {text[:100]}...")
    response = ask_mistral(text)
    pyperclip.copy(response)
    show_popup("🤖 Mistral Response", response)
    log_interaction(text, response)
    print("✅ Mistral response copied to clipboard.")

# ---------- TRAY APP ----------
def run_tray_app():
    icon_image = Image.new("RGB", (64, 64), "black")
    icon = pystray.Icon("Mistral Assistant", icon_image, "Mistral Assistant", menu=pystray.Menu(
        item('Activate (Ctrl+Shift+G)', lambda: handle_hotkey()),
        item('Settings', lambda: show_settings_window()),
        item('Quit', lambda icon, item: quit_app(icon))
    ))
    icon.run()

def quit_app(icon):
    icon.stop()
    os._exit(0)

# ---------- HOTKEY ----------
def start_hotkey_listener():
    keyboard.add_hotkey('ctrl+shift+g', handle_hotkey)
    print("🟢 Press Ctrl+Shift+G to activate OCR + Mistral.")
    while True:
        pass  # Keep the listener running

# ---------- MAIN MENU ----------
def main():
    if not test_connection():
        show_popup("Connection Error", "Could not connect to LM Studio. Please check your settings.")
        return
    root = tk.Tk()
    root.withdraw()
    choice = simpledialog.askstring("Startup", "Type 'tray' for tray app, 'hotkey' for hotkey only, 'settings' for settings:")
    root.destroy()
    if choice == "tray":
        threading.Thread(target=run_tray_app).start()
    elif choice == "hotkey":
        start_hotkey_listener()
    elif choice == "settings":
        show_settings_window()
    else:
        print("No valid choice. Exiting.")

if __name__ == "__main__":
    main()
