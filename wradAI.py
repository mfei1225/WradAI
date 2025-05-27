import threading
import time
import subprocess
import os
from pynput import keyboard
from AppKit import NSPasteboard, NSStringPboardType
from openai import OpenAI
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                            QLineEdit, QPushButton, QVBoxLayout,
                            QWidget, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import json
import os.path
import sys

# Configuration file path
CONFIG_FILE = os.path.expanduser("~/.wradAI_config.json")

def load_api_key():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('api_key', '')
        except json.JSONDecodeError:
            return ""
    return ""

def save_api_key(api_key):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'api_key': api_key}, f)

# Initialize client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=load_api_key()
)

class ApiKeyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenRouter API Key Configuration")
        self.setFixedSize(400, 150)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Label
        label = QLabel("Enter your OpenRouter API Key:")
        layout.addWidget(label)
        
        # API Key Entry
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setPlaceholderText("Paste your API key here")
        self.api_key_entry.setEchoMode(QLineEdit.Password)
        self.api_key_entry.setText(load_api_key())
        layout.addWidget(self.api_key_entry)
        
        # Save Button
        save_button = QPushButton("Save & Start")
        save_button.clicked.connect(self.save_and_start)
        layout.addWidget(save_button)
        
        # Center the window
        self.center()
    
    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.desktop().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())
    
    def save_and_start(self):
        api_key = self.api_key_entry.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Warning", "API key cannot be empty!")
            return
        
        save_api_key(api_key)
        client.api_key = api_key
        self.close()
        QMessageBox.information(self, "Success", "API key saved successfully!")
        
        # Start the keyboard listener in a separate thread
        threading.Thread(target=start_keyboard_listener, daemon=True).start()

# Key combination: Ctrl+Shift+A
COMBINATION = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('a')}
current_keys = set()

def get_clipboard_text():
    pb = NSPasteboard.generalPasteboard()
    content = pb.stringForType_(NSStringPboardType)
    return content.strip() if content else ""

def set_clipboard_text(text):
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(text, NSStringPboardType)

def copy_selection():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "c" using command down'])
    time.sleep(0.1)
    return get_clipboard_text()

def move_cursor_to_end_of_selection():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 124'])

def paste_clipboard():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'])

def send_api_request_with_selected_text():
    if not client.api_key:
        print("❗ API key not set.")
        return

    selected_text = copy_selection()
    if not selected_text:
        print("No text selected.")
        return

    prompt = (
        "You are an attending in a Emergency medicine clinic. "
        "Help me write a SOAP note. I am going to give the subjective and objective findings "
        "of a patient. You will provide the Assessment and Plan for the patient.\n\n"
        "Output the format in plain text, with each section on a new line\n"
        f"Subjective and Objective: {selected_text}"
    )

    try:
        start_time = time.time()
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
        )
        result = completion.choices[0].message.content.strip()
        print(f"✅ API responded in {round(time.time() - start_time, 2)}s")
        set_clipboard_text(result)
        time.sleep(0.05)
        move_cursor_to_end_of_selection()
        time.sleep(0.05)
        paste_clipboard()
    except Exception as e:
        set_clipboard_text("Error: API request failed. Please try again.")
        time.sleep(0.05)
        move_cursor_to_end_of_selection()
        time.sleep(0.05)
        paste_clipboard()
        print(f"⚠️ API Error: {e}")

def on_press(key):
    current_keys.add(key)
    if all(k in current_keys for k in COMBINATION):
        threading.Thread(target=send_api_request_with_selected_text, daemon=True).start()

def on_release(key):
    current_keys.discard(key)

def start_keyboard_listener():
    print("🔁 Starting keyboard listener...")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        if not load_api_key():
            self.window = ApiKeyWindow()
            self.window.show()
        else:
            # Start keyboard listener in background
            threading.Thread(target=start_keyboard_listener, daemon=True).start()
            
            # Create a hidden window to keep the app running
            self.window = QMainWindow()
            self.window.setWindowFlags(Qt.WindowDoesNotAcceptFocus | Qt.WindowStaysOnTopHint)
            self.window.resize(1, 1)
            self.window.move(-100, -100)
            self.window.show()
        
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    Application()