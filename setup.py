from setuptools import setup

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
        'PyQt5.QtGui'
    ],
    'excludes': [
        'tkinter'  # Remove if you're not using Tkinter
    ],
    'plist': {
        'CFBundleName': 'wradAI',
        'CFBundleDisplayName': 'wradAI',
        'CFBundleIdentifier': 'com.yourdomain.wradAI',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSAppleEventsUsageDescription': 'wradAI uses AppleScript to copy and paste selected text.',
        'NSAccessibilityUsageDescription': 'wradAI needs keyboard access to detect your hotkey.',
        'LSUIElement': True,  # Changed to True for background app without dock icon
        'NSAppleMusicUsageDescription': 'Required for keyboard access',
        'NSSystemAdministrationUsageDescription': 'Required for keyboard access',
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