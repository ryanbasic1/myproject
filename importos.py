import os
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, Image
import pytesseract
from openai import OpenAI
import pyperclip
import keyboard
import pystray
from pystray import MenuItem as item

# ---------- LM STUDIO CLIENT ----------
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",  # LM Studio API endpoint
    api_key="lm-studio"                   # Placeholder only (ignored by LM Studio)
)

# Change this to match your LM Studio model name exactly
LOCAL_MODEL_NAME = "mistralai/mistral-7b-instruct-v0.3"

# ---------- CONNECTION TEST ----------
def test_connection():
    try:
        response = client.models.list()
        print("✅ Connected to LM Studio. Models available:")
        for m in response.data:
            print("   -", m.id)
    except Exception as e:
        print(f"❌ Could not connect to LM Studio: {e}")
        print("Make sure the server is running in LM Studio (Server tab → Start Server).")
        os._exit(1)

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

# ---------- OCR ----------
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

# ---------- STREAMING MISTRAL ----------
def ask_mistral_stream(prompt):
    try:
        streamed_text = ""
        # Streaming request using stream=True
        for chunk in client.chat.completions.create(
            model=LOCAL_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            delta = chunk.choices[0].delta.content or ""
            if delta:
                print(delta, end="", flush=True)
                streamed_text += delta

        print("\n✅ Finished streaming.")
        return streamed_text.strip()

    except Exception as e:
        return f"Mistral Error: {e}"

# ---------- POPUP ----------
def show_popup(title, content):
    popup = tk.Tk()
    popup.withdraw()
    messagebox.showinfo(title, content)
    popup.destroy()

# ---------- HOTKEY HANDLER ----------
def handle_hotkey():
    print("🔹 Select a region on screen...")
    text = capture_text_from_selected_area()
    if not text or "Error" in text:
        show_popup("❌ Error", text or "No text detected.")
        return
    print(f"📝 OCR Text: {text[:100]}...")
    response = ask_mistral_stream(text)
    pyperclip.copy(response)
    show_popup("🤖 Mistral Response", response)
    print("✅ Mistral response copied to clipboard.")

# ---------- TRAY APP ----------
def run_tray_app():
    icon_image = Image.new("RGB", (64, 64), "black")  # Simple icon
    icon = pystray.Icon("Mistral Assistant", icon_image, "Mistral Assistant", menu=pystray.Menu(
        item('Activate (Ctrl+Shift+G)', lambda: handle_hotkey()),
        item('Quit', lambda icon, item: quit_app(icon))
    ))
    icon.run()

def quit_app(icon):
    icon.stop()
    os._exit(0)

# ---------- HOTKEY LISTENER ----------
def start_hotkey_listener():
    keyboard.add_hotkey('ctrl+shift+g', handle_hotkey)
    keyboard.add_hotkey('ctrl+shift+q', handle_exit_hotkey)
    print("🟢 Press Ctrl+Shift+G to activate OCR + Mistral.")
    print("🟢 Press Ctrl+Shift+Q to exit the program.")
    keyboard.wait()

# ---------- EXIT BUTTON WINDOW ----------
def show_exit_window():
    def exit_app():
        root.destroy()
        os._exit(0)
    root = tk.Tk()
    root.title("Exit Program")
    root.geometry("250x100")
    btn = tk.Button(root, text="Exit Program", command=exit_app, font=("Arial", 14), bg="red", fg="white")
    btn.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    root.mainloop()

def handle_exit_hotkey():
    show_exit_window()

# ---------- MAIN ----------
if __name__ == "__main__":
    test_connection()
    hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
    hotkey_thread.start()
    run_tray_app()
    show_exit_window()
