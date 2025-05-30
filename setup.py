from setuptools import setup
import os

APP = ['wradAI.py']
DATA_FILES = []
OPTIONS = {
    'packages': ['openai', 'pynput', 'PyQt5'],
    'includes': [
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pynput._util',
        'pynput._util.darwin',
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'AppKit',
        'Foundation',
        'objc',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'ssl',  # Needed for OpenSSL usage
        'ctypes.macholib.dyld',  # Needed for _ctypes import error
    ],
    'excludes': ['tkinter'],
    'frameworks': [
        '/opt/homebrew/opt/libffi/lib/libffi.dylib',
        '/opt/homebrew/opt/openssl@3/lib/libssl.3.dylib',
        '/opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib'
    ],
    'plist': {
        'CFBundleName': 'wradAI',
        'CFBundleDisplayName': 'wradAI',
        'CFBundleIdentifier': 'com.yourdomain.wradAI',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSAppleEventsUsageDescription': 'wradAI uses AppleScript to copy and paste selected text.',
        'NSAccessibilityUsageDescription': 'wradAI needs keyboard access to detect your hotkey.',
        'LSUIElement': False,  # Changed to False to show in Dock
        'NSHighResolutionCapable': True,
        'CFBundleIconFile': 'AppIcon.icns',  # Add if you have an icon
        'NSUIElement': False,  # Alternative to LSUIElement
    },
    'argv_emulation': False,
}

setup(
    app=APP,
    name='wradAI',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)