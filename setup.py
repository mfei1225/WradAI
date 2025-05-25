from setuptools import setup

APP = ['wradAI.py']
DATA_FILES = [('', ['.env'])]
OPTIONS = {
    'packages': ['openai', 'dotenv',],
    'includes': [
        'pynput',
        'pynput.keyboard._darwin', 
        'pynput.mouse._darwin',
        'AppKit',
    ],
    'plist': {
        'CFBundleName': 'wradAI',
        'CFBundleDisplayName': 'wradAI',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
    },
}

setup(
    app=APP,
    name='wradAI',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)
