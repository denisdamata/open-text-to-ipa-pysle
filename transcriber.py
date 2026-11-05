#!/usr/bin/env python3
"""
Transcriber module for the Open Text to IPA PYSLE application.
Handles text tokenization, pysle lookup, and IPA formatting.

Core functions:
- ipa_palavra(palavra, silabas: bool) -> str — returns the IPA for a word
  with `ˈ`/`ˌ` repositioned to the start of the syllable;
  inserts `.` between syllables if `silabas=True`.
- transcrever_texto(texto, modo, silabas) -> str — orchestrates the output
  in both modes.
- Handling of unknown words: keep the original word in brackets `[palavra]`.
- In-memory cache (`dict`) to avoid repeated `pysle` lookups in the same session.
"""

import re
from pysle.isletool import Isle
from pysle.utilities.errors import WordNotInIsleError


_isle = Isle()
_translation_cache: dict[tuple[str, bool], str] = {}
_WORD_PATTERN = re.compile(r"^([^\w]*)([\w]+(?:['’][\w]+|-[\w]+)*)([^\w]*)$")


def ipa_palavra(palavra: str, silabas: bool = False) -> str:
    """
    Returns the IPA for a word, with stress markers repositioned to the
    start of the syllable.
    
    Args:
        palavra: The word to transcribe.
        silabas: If True, syllables are separated by `.`;
                 if False, syllables are concatenated directly.
    
    Returns:
        The IPA transcription string. If the word is not in the lexicon,
        returns the original word in brackets `[palavra]`.
    """
    match = _WORD_PATTERN.fullmatch(palavra)
    if match is None:
        return palavra

    prefix, word, suffix = match.groups()
    cache_key = (word, silabas)
    if cache_key in _translation_cache:
        return prefix + _translation_cache[cache_key] + suffix

    try:
        entries = _isle.lookup(word)
    except WordNotInIsleError:
        result = f"[{word}]"
    except Exception:
        result = f"[erro: {word}]"
    else:
        if not entries:
            result = f"[{word}]"
        else:
            entry = entries[0]

            syllables = []
            for syllable in entry.syllabificationList[0].syllables:
                marker = ""
                phonemes = []
                for phoneme in syllable.phonemes:
                    if "ˈ" in phoneme or "ˌ" in phoneme:
                        marker = "ˈ" if "ˈ" in phoneme else "ˌ"
                        phoneme = phoneme.replace("ˈ", "").replace("ˌ", "")
                    phonemes.append(phoneme)
                syllables.append(marker + "".join(phonemes))

            result = ("." if silabas else "").join(syllables)

    _translation_cache[cache_key] = result
    return prefix + result + suffix


def transcrever_texto(texto: str, modo: str = "transcription only", silabas: bool = False) -> str:
    """
    Orchestrates the IPA transcription output in both modes.
    
    Args:
        texto: The text to transcribe.
        modo: Either "transcription only" or "word by word".
        silabas: If True, syllables are separated by `.`;
                 if False, syllables are concatenated directly.
    
    Returns:
        The formatted output string based on the selected mode.
    """
    parts = re.split(r"(\s+)", texto)
    output_parts = []

    for part in parts:
        if not part or part.isspace():
            output_parts.append(part)
            continue

        ipa = ipa_palavra(part, silabas)
        if modo == "word by word" and ipa != part:
            output_parts.append(f"{part} {ipa}")
        else:
            output_parts.append(ipa)

    return "".join(output_parts)


if __name__ == "__main__":
    # Simple test when run directly
    test_words = ["complicated", "hello", "world", "unknownword"]
    for word in test_words:
        ipa = ipa_palavra(word, silabas=False)
        print(f"{word}: {ipa}")
    print("\n--- With syllable division ---")
    for word in test_words:
        ipa = ipa_palavra(word, silabas=True)
        print(f"{word}: {ipa}")