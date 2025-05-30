import time
import subprocess
import os
from pynput import keyboard
from AppKit import NSPasteboard, NSStringPboardType
from openai import OpenAI
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, 
                            QLineEdit, QPushButton, QVBoxLayout,
                            QWidget, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QIcon
import json
import os.path
import sys
from Foundation import NSBundle

CONFIG_FILE = os.path.expanduser("~/.wradAI_config.json")
class FocusManager:
    def __init__(self):
        self.original_app_info = None
    
    def capture_focus(self):
        """Capture current focused application and window"""
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontAppID to bundle identifier of first application process whose frontmost is true
                set frontWindow to name of first window of process frontApp
                return frontApp & "|||" & frontAppID & "|||" & frontWindow
            end tell
            '''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            if "|||" in result:
                parts = result.split("|||")
                self.original_app_info = {
                    'name': parts[0],
                    'bundle_id': parts[1],
                    'window': parts[2]
                }
        except Exception as e:
            print(f"⚠️ Error capturing focus: {e}")
    
    def restore_focus(self):
        """Restore focus to original application and window"""
        if not self.original_app_info:
            return
            
        try:
            # First try to activate by bundle ID (more reliable)
            if self.original_app_info.get('bundle_id'):
                subprocess.run([
                    'osascript', '-e',
                    f'tell application id "{self.original_app_info["bundle_id"]}" to activate'
                ], check=True)
                time.sleep(0.3)
            
            # Then try to raise the specific window
            if self.original_app_info.get('window'):
                script = f'''
                tell application "System Events"
                    tell process "{self.original_app_info["name"]}"
                        set frontmost to true
                        try
                            set targetWindow to first window whose name contains "{self.original_app_info["window"]}"
                            perform action "AXRaise" of targetWindow
                        end try
                    end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=True)
                time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Error restoring focus: {e}")

def load_api_key():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('api_key', '')
    except Exception:
        return ""
    return ""

def save_api_key(api_key):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'api_key': api_key}, f)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=load_api_key()
)

class LoadingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Processing...")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.center()
        
        self.progress = QProgressBar(self)
        self.progress.setGeometry(25, 25, 250, 25)
        self.progress.setMaximum(100)
        self.progress.setTextVisible(False)
        
        self.animation = QPropertyAnimation(self.progress, b"value")
        self.animation.setDuration(2000)
        self.animation.setLoopCount(-1)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.start()
    
    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

class ApiKeyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenRouter API Key Configuration")
        self.setFixedSize(400, 150)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        label = QLabel("Enter your OpenRouter API Key:")
        layout.addWidget(label)
        
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setPlaceholderText("Paste your API key here")
        self.api_key_entry.setEchoMode(QLineEdit.Password)
        self.api_key_entry.setText(load_api_key())
        layout.addWidget(self.api_key_entry)
        
        save_button = QPushButton("Save & Start")
        save_button.clicked.connect(self.save_and_start)
        layout.addWidget(save_button)
        
        self.center()
    
    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
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

class APIWorker(QThread):
    finished = pyqtSignal(str, bool)
    error = pyqtSignal(str)
    
    def __init__(self, selected_text):
        super().__init__()
        self.selected_text = selected_text
        self.mutex = QMutex()
    
    def run(self):
        self.mutex.lock()
        try:
            prompt = (
                "You are an attending in a Emergency medicine clinic. "
                "Help me write a SOAP note. I am going to give the subjective and objective findings "
                "of a patient. You will provide the Assessment and Plan for the patient.\n\n"
                "Output the format in plain text, with each section on a new line\n"
                f"Subjective and Objective: {self.selected_text}"
            )
            
            print("🌐 Sending API request...")
            start_time = time.time()
            completion = client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[{"role": "user", "content": prompt}],
            )
            result = completion.choices[0].message.content.strip()
            print(f"✅ API responded in {round(time.time() - start_time, 2)}s")
            self.finished.emit(result, True)
        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            print(f"⚠️ {error_msg}")
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class KeyboardListener(QThread):
    hotkey_pressed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.combination = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('a')}
        self.current_keys = set()
        self.last_press_time = 0
        self.debounce_interval = 0.5  # 500ms debounce
    
    def on_press(self, key):
        try:
            current_time = time.time()
            if current_time - self.last_press_time < self.debounce_interval:
                return
                
            self.current_keys.add(key)
            if all(k in self.current_keys for k in self.combination):
                self.last_press_time = current_time
                self.hotkey_pressed.emit()
        except Exception as e:
            print(f"⚠️ Key press error: {e}")
    
    def on_release(self, key):
        try:
            if key in self.current_keys:
                self.current_keys.remove(key)
        except Exception as e:
            print(f"⚠️ Key release error: {e}")
    
    def run(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

class ClipboardManager:
    @staticmethod
    def get_clipboard_text():
        try:
            pb = NSPasteboard.generalPasteboard()
            content = pb.stringForType_(NSStringPboardType)
            return content.strip() if content else ""
        except Exception as e:
            print(f"⚠️ Clipboard read error: {e}")
            return ""
    
    @staticmethod
    def set_clipboard_text(text):
        try:
            pb = NSPasteboard.generalPasteboard()
            pb.clearContents()
            pb.setString_forType_(text, NSStringPboardType)
            time.sleep(0.3)  # Important delay for clipboard stability
        except Exception as e:
            print(f"⚠️ Clipboard write error: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WradAI")
        self.setFixedSize(1, 1)
        self.move(-100, -100)
        
        self.focus_manager = FocusManager()
        self.clipboard_manager = ClipboardManager()
        self.is_processing = False
        self.loading_window = None
        self.worker = None
        
        # Initialize keyboard listener
        self.keyboard_listener = KeyboardListener()
        self.keyboard_listener.hotkey_pressed.connect(self.handle_hotkey)
        self.keyboard_listener.start()
    
    def copy_selection(self):
        """More reliable copy implementation with verification"""
        try:
            # Clear clipboard first
            self.clipboard_manager.set_clipboard_text("")
            time.sleep(0.2)
            
            # Perform the copy command
            subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to keystroke "c" using command down'],
                check=True
            )
            time.sleep(0.5)  # Increased delay for reliability
            
            # Verify we got something
            text = self.clipboard_manager.get_clipboard_text()
            if not text:
                raise Exception("Clipboard is empty after copy")
            return text
        except Exception as e:
            print(f"⚠️ Copy failed: {e}")
            return ""
    
    def paste_response(self, text):
        """Reliable paste with focus management"""
        try:
            # Set the clipboard content
            self.clipboard_manager.set_clipboard_text(text)
            time.sleep(0.4)
            
            # Restore original focus
            self.focus_manager.restore_focus()
            time.sleep(0.4)  # Critical delay for focus change
            
            # Move cursor to end of selection
            subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to key code 124'],  # Right arrow
                check=True
            )
            time.sleep(0.2)
            
            # Perform the paste with retry logic
            for attempt in range(3):
                try:
                    subprocess.run(
                        ['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'],
                        check=True
                    )
                    time.sleep(0.2)
                    return True
                except Exception as e:
                    if attempt == 2:
                        raise
                    print(f"⚠️ Paste attempt {attempt + 1} failed, retrying...")
                    time.sleep(0.3)
                    continue
        except Exception as e:
            print(f"⚠️ Paste failed: {e}")
            return False
    
    def handle_hotkey(self):
        if self.is_processing:
            print("⚠️ Already processing a request")
            return
            
        print("🔍 Hotkey detected (Ctrl+Shift+A)")
        self.send_api_request_with_selected_text()

    def send_api_request_with_selected_text(self):
        if self.is_processing:
            return
            
        self.is_processing = True
        self.focus_manager.capture_focus()  # Remember current focus
        
        try:
            # Copy the selected text
            selected_text = self.copy_selection()
            if not selected_text:
                print("No text selected.")
                self.is_processing = False
                return
            
            print(f"🔍 Selected text: {selected_text[:50]}...")
            self.show_loading_window()
            
            # Process the API request
            self.worker = APIWorker(selected_text)
            self.worker.finished.connect(self.handle_api_result)
            self.worker.error.connect(self.handle_api_error)
            self.worker.start()
            
            QTimer.singleShot(30000, self.cleanup)
        except Exception as e:
            print(f"⚠️ Error in request processing: {e}")
            self.cleanup()
    
    def handle_api_result(self, result, success):
        try:
            if not success:
                print("⚠️ API request failed")
                self.cleanup()
                return
            
            print("📋 Processing API response...")
            if not self.paste_response(result):
                print("⚠️ Failed to paste response")
            
            print("📤 Operation completed")
        except Exception as e:
            print(f"⚠️ Error handling result: {e}")
        finally:
            self.cleanup()
    
    def show_loading_window(self):
        self.loading_window = LoadingWindow()
        self.loading_window.show()
        QApplication.processEvents()

    def handle_api_error(self, error_msg):
        print(f"⚠️ {error_msg}")
        self.cleanup()

    def cleanup(self):
        if self.loading_window:
            self.loading_window.close()
            self.loading_window = None
            
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
            
        self.is_processing = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configure application identity for macOS
    try:
        bundle = NSBundle.mainBundle()
        if bundle:
            info = bundle.infoDictionary()
            if info:
                info["LSUIElement"] = False
                info["CFBundleName"] = "WradAI"
    except Exception as e:
        print(f"⚠️ macOS configuration error: {e}")

    app.setApplicationName("WradAI")
    app.setApplicationDisplayName("WradAI")

    if not load_api_key():
        window = ApiKeyWindow()
    else:
        window = MainWindow()
    
    window.show()
    sys.exit(app.exec_())