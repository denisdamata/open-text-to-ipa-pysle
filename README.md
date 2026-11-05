# Open Text to IPA — PySLE

A free, offline desktop application for transcribing English text into IPA alongside the original text. It uses **PySLE** as its pronunciation and phonetic transcription engine.

## Project intent and attribution

This project was developed with AI assistance throughout. Its distinctive contribution is the simple side-by-side interface and support for transcribing long passages into readable English scripts; the pronunciation data and phonetic engine come from PySLE, not from a new AI model.

The goal is to offer a free, local alternative for the combined text-and-transcription workflow found on [toIPA.org](https://toipa.org/). This project is independent and is not affiliated with toIPA.org.

## Installation

1. **Create a virtual environment** (Python 3.11+):
   ```bash
   python3 -m venv ~/venv
   source ~/venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

1. Paste English text into the left text area.
2. Choose a transcription mode (the default is **Word by word**):
   - **Word by word**: Each word and its IPA transcription appear together on the same line
   - **Transcription only**: A single continuous IPA line for the whole text
3. "Syllable division" is enabled by default; uncheck it to remove dot separators between syllables.
4. Click "Transcribe" to convert the text to IPA.
5. Right-click the output to copy selected text or select all. Right-click the input for cut, copy, paste, and select-all actions.

## Features

- **Long text support**: Scrollable input and transcription panels for longer passages
- **Preserved formatting**: Existing spaces and line breaks are kept in the transcription
- **Stress marking**: Stressed syllables are always marked with `ˈ` or `ˌ`
- **Error handling**: Unknown words are shown in brackets `[word]`
- **Offline**: Uses PySLE locally; no AI service or network connection is used at runtime
- **Cache**: In-memory cache prevents repeated lookups in the same session

## Requirements

- Python 3.11+
- Tkinter (part of Python standard library on Linux)
- PySLE engine (installed via `requirements.txt`)

## Troubleshooting

If the application doesn't start:
1. Ensure you're using Python 3.11+
2. Verify the virtual environment is activated
3. Check that all dependencies are installed correctly

If the Transcribe button reports an error, make sure PySLE is installed in the same virtual environment used to launch the application.

## License

This project is a simple educational application for IPA transcription using pysle.

---

**Project Structure:**
```
open_text_to_ipa_pysle/
├── main.py          # GUI with two-panel layout
├── transcriber.py   # IPA transcription logic
└── README.md        # Installation and usage
```