from pynput import keyboard
import subprocess
import time
import threading
from AppKit import NSPasteboard, NSStringPboardType
from openai import OpenAI
from dotenv import load_dotenv
import os

# Define the hotkey combo (Ctrl+Shift+A)
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
    #api_key=os.getenv("OPENROUTER_API_KEY"),
)
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
    # Simulate Cmd+C
    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "c" using command down'])
    time.sleep(0.1)  # Allow clipboard to update
    return get_clipboard_text()

def move_cursor_to_end_of_selection():
    # Move cursor to end of selection using right arrow
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 124'])

def paste_clipboard():
    subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'])


def send_api_request_with_selected_text():
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
        print(f"⏱ API responded in {round(time.time() - start_time, 2)}s")
        set_clipboard_text(result)
        time.sleep(0.05)
        move_cursor_to_end_of_selection()
        time.sleep(0.05)
        paste_clipboard()
    except Exception as e:
        print(f"⚠️ API Error: {e}")

def on_press(key):
    current_keys.add(key)
    if all(k in current_keys for k in COMBINATION):
        threading.Thread(target=send_api_request_with_selected_text).start()

def on_release(key):
    current_keys.discard(key)

def main():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()



