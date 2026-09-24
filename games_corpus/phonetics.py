"""Phonetic dictionaries, for counting phones (e.g. speech rate in phones per second).

One dictionary per corpus in `data/phonetic_dicts/{corpus-slug}.txt`, one word per line:
`count<TAB>word<TAB>phones`, where `phones` is space-separated (possibly empty) and `count`
is the word's frequency in the corpus (informative only). These are the dictionaries used in
Brusco et al.'s turn-taking experiments (e.g. the phones-per-second features of the RF models):

- English and Slovak: copied unchanged from the corpus data distributions.
- Spanish (batches 1 and 2): regenerated with the original recipe (the original file was lost),
  see scripts/generate_phonetic_dict_spanish.py: phonemizer + eSpeak NG, Latin American Spanish;
  "uu" and <tags> (e.g. <risa>) have no phones; one-letter words count as one phone.

These are automatic grapheme-to-phoneme transcriptions, not human annotation. Known quirk
inherited from eSpeak: letter sequences it can't read as a word are spelled out, e.g. Spanish
"mm" -> "e m e ɛ m e" (6 phones).

Unintelligible-speech marks ("?", "?-", "-?") are not loaded as words, so an IPU containing one
has no phone count (None), as in the original experiments' treatment of out-of-dictionary words.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data" / "phonetic_dicts"

#: Transcription marks for unintelligible speech. Not words: an IPU containing one has no phone
#: count. (A "?" attached to a word, e.g. "bien?", marks a doubtful transcription of that word
#: and keeps its phones.)
UNINTELLIGIBLE = frozenset({"?", "?-", "-?"})

#: Corpus class name (`type(corpus).__name__`) -> dictionary file slug.
_CORPUS_SLUGS: dict[str, str] = {
    "SpanishGamesCorpus": "games-spanish",
    "EnglishGamesCorpus": "games-english",
    "SlovakGamesCorpus": "games-slovak",
}


@cache
def load_phonetic_dictionary(corpus_key: str) -> dict[str, tuple[str, ...]]:
    """Word -> phones for a corpus (`corpus_key` = corpus class name)."""
    path = _DATA_DIR / f"{_CORPUS_SLUGS[corpus_key]}.txt"
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] not in UNINTELLIGIBLE:
            # English marks the boundary of a truncated word's reconstructed part with "|",
            # attached to the next phone (o-(ne) -> "oʊ |n iː"); it isn't a phone itself.
            entries[fields[1]] = tuple(p for p in (f.lstrip("|") for f in fields[2:]) if p)
    return entries


def count_phones(words: Iterable[str], dictionary: dict[str, tuple[str, ...]]) -> int | None:
    """Total phones in `words`, or None if any word is missing from the dictionary."""
    total = 0
    for w in words:
        if w not in dictionary:
            return None
        total += len(dictionary[w])
    return total
