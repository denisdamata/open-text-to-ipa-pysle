<h1 align="center">
  <img src="icon.png" alt="" width="42" align="left"> Open Text to IPA
  <img src="https://img.shields.io/badge/OS-Linux%20only-FCC624?logo=linux&logoColor=black" alt="Linux only" align="right">
</h1>

<p align="center"><strong>English text and IPA transcription, together in one readable view.</strong></p>

<div align="center">
  <img src="main.png" alt="Open Text to IPA application window" width="900">
</div>

## Project intent and sources

This project is a practical, free-to-use tool. It was developed with AI assistance. Its contribution is a simple side-by-side interface for transcribing long passages while merging with original text. The english content is provided by PySLE using the ISLEdict data.

The goal is to offer a free, local alternative for the combined text-and-transcription workflow found on [toIPA.org](https://toipa.org/text-to-ipa/en-US/). This project is independent and is not affiliated with toIPA.org.

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

### Resources

**PySLE** is the Python library used to look up pronunciations and syllable/stress information [Mahrt, T. (2016). *Pysle*.](https://github.com/timmahrt/pysle). The pronunciation data comes from **ISLEdict**, bundled with PySLE. PySLE's [ISLEdict attribution and license note](https://github.com/timmahrt/pysle#isle-dictionary) identifies it as copyright Mark Hasegawa-Johnson and licensed under the MIT license. The direct [English ISLEdict source file](https://raw.githubusercontent.com/uiuc-sst/g2ps/master/English/ISLEdict.txt) is maintained in the [ISLEX/G2P project](https://github.com/uiuc-sst/g2ps).

The application uses [Klembord](https://github.com/OzymandiasTheGreat/klembord/tree/b09e7953c6b5411325f03fc24feb11bec95d8517) for rich clipboard access on Linux.

The `lingose` Python package was also considered, but it does not provide the syllable boundaries and stress marks required for this app. PySLE was selected because syllabic separation and lexical stress are essential to the intended output.

## License

This application is free to use, provided that it is duly cited.
