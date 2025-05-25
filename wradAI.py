import sys
import threading
import time
import subprocess
import os
from pathlib import Path
from pynput import keyboard
from dotenv import load_dotenv

from AppKit import (
    NSApplication, NSWindow, NSTextField, NSButton, NSMakeRect,
    NSTitledWindowMask, NSClosableWindowMask, NSResizableWindowMask,
    NSBackingStoreBuffered, NSPasteboard, NSStringPboardType
)
from Foundation import NSObject
from PyObjCTools import AppHelper
from openai import OpenAI

# Load env if needed
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# Global OpenAI client placeholder
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=""  # Leave blank initially; will be set from GUI
)

# Key combination: Ctrl+Shift+A
COMBINATION = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('a')}
current_keys = set()

# Clipboard utils
def get_clipboard_text():
    pb = NSPasteboard.generalPasteboard()
    content = pb.stringForType_(NSStringPboardType)
    return content.strip() if content else ""

def set_clipboard_text(text):
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(text, NSStringPboardType)

# MacOS keyboard simulation via AppleScript
def copy_selection():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "c" using command down'])
    time.sleep(0.1)
    return get_clipboard_text()

def move_cursor_to_end_of_selection():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 124'])

def paste_clipboard():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'])

# API logic
def send_api_request_with_selected_text():
    if not client.api_key:
        print("❗ API key not set. Please enter it in the window.")
        return

    selected_text = copy_selection()
    if not selected_text:
        print("No text selected.")
        return

    prompt = (
        "You are an attending in a family medicine clinic. "
        "Help me write a SOAP note. I am going to give the subjective and objective findings "
        "of a patient. You will provide the Assessment and Plan for the patient.\n\n"
        f"Subjective and Objective: {selected_text}"
    )

    try:
        start_time = time.time()
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
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
        print(f"⚠️ API Error: {e}")

# Hotkey handling
def on_press(key):
    current_keys.add(key)
    if all(k in current_keys for k in COMBINATION):
        threading.Thread(target=send_api_request_with_selected_text).start()

def on_release(key):
    current_keys.discard(key)

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# macOS AppDelegate
class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100.0, 100.0, 400.0, 150.0),
            NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("Enter API Key")

        # Label
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 90, 360, 24))
        label.setStringValue_("Enter your API key:")
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        self.window.contentView().addSubview_(label)

        # Text field
        self.api_key_field = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 60, 360, 24))
        self.window.contentView().addSubview_(self.api_key_field)

        # Button
        button = NSButton.alloc().initWithFrame_(NSMakeRect(150, 20, 100, 30))
        button.setTitle_("Submit")
        button.setBezelStyle_(4)
        button.setTarget_(self)
        button.setAction_("submitClicked:")
        self.window.contentView().addSubview_(button)

        self.window.makeKeyAndOrderFront_(None)

    def submitClicked_(self, sender):
        api_key = self.api_key_field.stringValue()
        client.api_key = api_key
        print("✅ API key set.")
        self.window.orderOut_(None)

# Main launcher
def main():
    # Start keyboard listener in background
    threading.Thread(target=start_keyboard_listener, daemon=True).start()

    # Start macOS GUI app
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()

if __name__ == "__main__":
    main()
