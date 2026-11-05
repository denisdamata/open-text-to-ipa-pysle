"""ISLE dictionary lookup and pronunciation-entry selection."""

from pysle.isletool import Isle
from pysle.utilities.errors import WordNotInIsleError


_isle = Isle()
_IPA_VOWELS = frozenset("aeiouɪɛæɑɒɔʊʌəɚɝɐɵɨʉɘɜɞɤɯøœy")
_INITIAL_SOUNDS = {
    "b": ("b",),
    "c": ("k", "s"),
    "d": ("d",),
    "f": ("f",),
    "g": ("g", "dʒ"),
    "h": ("h",),
    "j": ("dʒ",),
    "k": ("k",),
    "l": ("l",),
    "m": ("m",),
    "n": ("n",),
    "p": ("p",),
    "q": ("k",),
    "r": ("ɹ", "r"),
    "s": ("s",),
    "t": ("t", "θ", "ð"),
    "v": ("v",),
    "w": ("w",),
    "x": ("z",),
    "y": ("j",),
    "z": ("z",),
}
_FINAL_SOUNDS = {
    "b": ("b",),
    "c": ("k", "s"),
    "d": ("d", "t"),
    "f": ("f", "v"),
    "g": ("g", "dʒ"),
    "j": ("dʒ",),
    "k": ("k",),
    "l": ("l",),
    "m": ("m",),
    "n": ("n",),
    "p": ("p",),
    "r": ("ɹ", "r"),
    "s": ("s", "z"),
    "t": ("t", "d"),
    "v": ("v",),
    "x": ("s", "z"),
    "z": ("z", "s"),
}


def _entry_matches_spelling_boundary(word, phonemes, initial):
    word = word.lower()
    if initial:
        if word.startswith("wh"):
            expected_sounds = ("w",)
        elif word.startswith("th"):
            expected_sounds = ("θ", "ð")
        else:
            expected_sounds = _INITIAL_SOUNDS.get(word[:1], ())
        boundary_phonemes = phonemes[:1]
    else:
        if word.endswith("ng"):
            expected_sounds = ("ŋ",)
        elif word.endswith("ck"):
            expected_sounds = ("k",)
        elif word.endswith("ch"):
            expected_sounds = ("tʃ", "dʒ", "ʃ", "k")
        elif word.endswith("sh"):
            expected_sounds = ("ʃ",)
        elif word.endswith("th"):
            expected_sounds = ("θ", "ð")
        elif word.endswith("ph"):
            expected_sounds = ("f",)
        else:
            expected_sounds = _FINAL_SOUNDS.get(word[-1:], ())
        boundary_phonemes = phonemes[-1:]

    return any(
        phoneme.startswith(sound)
        for phoneme in boundary_phonemes
        for sound in expected_sounds
    )


def _select_best_entry(entries):
    analyzed_entries = []

    for index, entry in enumerate(entries):
        try:
            syllabifications = entry.syllabificationList
            if not syllabifications:
                continue
            syllables = syllabifications[0].syllables
            num_primary = sum(
                str(phoneme).count("ˈ")
                for syllable in syllables
                for phoneme in syllable.phonemes
            )
            num_secondary = sum(
                str(phoneme).count("ˌ")
                for syllable in syllables
                for phoneme in syllable.phonemes
            )
            syllables_without_nucleus = sum(
                not any(
                    "\u0329" in str(phoneme)
                    or any(vowel in str(phoneme) for vowel in _IPA_VOWELS)
                    for phoneme in syllable.phonemes
                )
                for syllable in syllables
            )
            num_syllables = len(syllables)
            word = entry.word
            phonemes = [
                str(phoneme).replace("ˈ", "").replace("ˌ", "")
                for syllable in syllables
                for phoneme in syllable.phonemes
            ]
        except Exception:
            continue

        analyzed_entries.append((
            index,
            entry,
            num_primary,
            num_secondary,
            num_syllables,
            syllables_without_nucleus,
            word,
            phonemes,
        ))

    initial_matches = {
        index
        for index, _, _, _, _, _, word, phonemes in analyzed_entries
        if _entry_matches_spelling_boundary(word, phonemes, initial=True)
    }
    final_matches = {
        index
        for index, _, _, _, _, _, word, phonemes in analyzed_entries
        if _entry_matches_spelling_boundary(word, phonemes, initial=False)
    }
    candidates = []

    for (
        index,
        entry,
        num_primary,
        num_secondary,
        num_syllables,
        syllables_without_nucleus,
        _word,
        _phonemes,
    ) in analyzed_entries:
        if num_primary >= 2 or syllables_without_nucleus >= 1:
            continue
        if (
            num_syllables == 1
            and num_primary == 0
            and num_secondary >= 1
        ):
            continue
        if num_syllables >= 2 and num_primary == 0:
            continue
        if initial_matches and index not in initial_matches:
            continue
        if final_matches and index not in final_matches:
            continue

        candidates.append((num_secondary, index, entry))

    if candidates:
        return min(candidates, key=lambda candidate: candidate[:2])[2]
    return entries[0]


def _normalize_syllable(phonemes: list[str]) -> str:
    merged_phonemes = []
    index = 0

    while index < len(phonemes):
        phoneme = phonemes[index]
        base_phoneme = phoneme.replace("ˈ", "").replace("ˌ", "")
        markers = "".join(marker for marker in phoneme if marker in "ˈˌ")
        if (
            base_phoneme == "ɚ"
            and index + 1 < len(phonemes)
            and phonemes[index + 1].replace("ˈ", "").replace("ˌ", "") == "ɹ"
        ):
            next_phoneme = phonemes[index + 1]
            markers += "".join(marker for marker in next_phoneme if marker in "ˈˌ")
            merged_phonemes.append(markers + "ɝ")
            index += 2
            continue

        merged_phonemes.append(phoneme)
        index += 1

    syllable = "".join(merged_phonemes)
    syllable = syllable.replace("ɵ", "θ")
    syllable = syllable.replace("əɹ", "ɚ")
    syllable = syllable.replace("hw", "w")
    return syllable.replace("ei", "eɪ")


def lookup_syllables(word: str) -> list[str] | None:
    """Return normalized syllable strings, or None if the word is absent."""
    try:
        entries = _isle.lookup(word)
    except WordNotInIsleError:
        return None

    if not entries:
        return None

    entry = _select_best_entry(entries)
    return [
        _normalize_syllable([str(phoneme) for phoneme in syllable.phonemes])
        for syllable in entry.syllabificationList[0].syllables
    ]
