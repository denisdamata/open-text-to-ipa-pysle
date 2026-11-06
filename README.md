<h1 align="center">
  <img src="icon.png" alt="" width="42" align="left"> Open Text to IPA
  <img src="https://img.shields.io/badge/OS-Linux%20only-FCC624?logo=linux&logoColor=black" alt="Linux only" align="right">
</h1>

<p align="center"><strong>English text and IPA transcription, together in one readable view.</strong></p>

<div align="center">
  <img src="main.png" alt="Open Text to IPA application window" width="900">
</div>

## Project intent and sources

This project is a practical, free-to-use tool, not an educational product. It was developed with AI assistance. Its contribution is a simple side-by-side interface for transcribing long passages while preserving their formatting; pronunciation lookup is provided by PySLE using the ISLEdict pronunciation data.

The goal is to offer a free, local alternative for the combined text-and-transcription workflow found on [toIPA.org](https://toipa.org/text-to-ipa/en-US/). This project is independent and is not affiliated with toIPA.org.

The `lingose` Python package was also considered, but it does not provide the syllable boundaries and stress marks required for this app. PySLE was selected because syllabic separation and lexical stress are essential to the intended output.

### Pronunciation engine and dictionary

**PySLE** is the Python library used to look up pronunciations and syllable/stress information:

> Mahrt, T. (2016). *Pysle*. [Source repository](https://github.com/timmahrt/pysle).

The pronunciation data comes from **ISLEdict**, bundled with PySLE. PySLE's [ISLEdict attribution and license note](https://github.com/timmahrt/pysle#isle-dictionary) identifies it as copyright Mark Hasegawa-Johnson and licensed under the MIT license. The direct [English ISLEdict source file](https://raw.githubusercontent.com/uiuc-sst/g2ps/master/English/ISLEdict.txt) is maintained in the [ISLEX/G2P project](https://github.com/uiuc-sst/g2ps).

### Clipboard library

The application uses [Klembord](https://github.com/OzymandiasTheGreat/klembord/tree/b09e7953c6b5411325f03fc24feb11bec95d8517) for rich clipboard access on Linux.

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
   - **Word by word**: Each original word is followed by its IPA transcription in `/slashes/`; punctuation is omitted, while syllable dots follow the checkbox setting
   - **Transcription only**: A single continuous IPA line for the whole text
3. "Syllable division" is enabled by default; uncheck it to remove dot separators between syllables.
4. Click "Transcribe" to convert the text to IPA.
5. Use standard shortcuts in the input:
   - **Ctrl+A**: Select all
   - **Ctrl+C / Ctrl+X / Ctrl+V**: Copy / cut / paste
   - **Ctrl+Z / Ctrl+Y**: Undo / redo
6. In the output, **Ctrl+A** selects all and **Ctrl+C** copies the selection. Bold formatting is included when pasting into rich-text apps; plain-text apps receive unformatted text. Right-click either text area for its available editing actions.

## Features

- **Long text support**: Scrollable input and transcription panels for longer passages
- **Preserved formatting**: Existing spaces and line breaks are kept in the transcription
- **Readable output**: Original text is bolded to distinguish it from IPA
- **Rich clipboard**: Uses [Klembord](https://github.com/OzymandiasTheGreat/klembord)'s X11 clipboard support to copy long selections as plain text, HTML, and RTF
- **Stress marking**: Stressed syllables are always marked with `ˈ` or `ˌ`
- **Unknown words**: Original words are kept without bracketed IPA placeholders
- **Offline**: Uses PySLE locally; no AI service or network connection is used at runtime
- **Cache**: In-memory cache prevents repeated lookups in the same session

## Requirements

- Python 3.11+
- Tkinter (part of Python standard library on Linux)
- PySLE engine (installed via `requirements.txt`)
- Klembord (X11 clipboard access; installed via `requirements.txt`)

## Troubleshooting

If the application doesn't start:
1. Ensure you're using Python 3.11+
2. Verify the virtual environment is activated
3. Check that all dependencies are installed correctly

If the Transcribe button reports an error, make sure PySLE is installed in the same virtual environment used to launch the application.

## License

This application is free to use. PySLE, ISLEdict, and Klembord are separate upstream projects; refer to the sources above for their respective licenses and attribution.
