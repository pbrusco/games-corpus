"""Phonetic dictionaries shipped with the package, and phone counts / speech rate per IPU."""

from pathlib import Path

import pytest

from games_corpus import IPU, EnglishGamesCorpus, SlovakGamesCorpus, SpanishGamesCorpus, Word
from games_corpus.phonetics import count_phones, load_phonetic_dictionary

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
CORPORA = [
    (SpanishGamesCorpus, "games-spanish"),
    (EnglishGamesCorpus, "games-english"),
    (SlovakGamesCorpus, "games-slovak"),
]


@pytest.mark.parametrize(
    "key, word, phones",
    [
        ("SpanishGamesCorpus", "sí", ("s", "i")),
        ("SpanishGamesCorpus", "izquierda", ("i", "s", "k", "j", "e", "ɾ", "ð", "a")),
        ("SpanishGamesCorpus", "<risa>", ()),
        ("EnglishGamesCorpus", "okay", ("oʊ", "k", "eɪ")),
        ("SlovakGamesCorpus", "je", ("j", "e")),
    ],
)
def test_known_entries(key, word, phones):
    assert load_phonetic_dictionary(key)[word] == phones


def test_count_phones_is_none_when_a_word_is_missing():
    d = {"la": ("l", "a"), "<risa>": ()}
    assert count_phones(["la", "<risa>", "la"], d) == 4
    assert count_phones(["la", "xyz"], d) is None


def test_phones_per_second():
    corpus = SpanishGamesCorpus()
    ipu = IPU(words=[Word(0.0, 0.25, "sí", "A"), Word(0.25, 0.5, "claro", "A")])
    assert corpus.num_phones(ipu) == 2 + 5
    assert corpus.phones_per_second(ipu) == pytest.approx(7 / 0.5)


@pytest.mark.parametrize("cls, slug", CORPORA)
def test_dictionary_covers_the_corpus_vocabulary(cls, slug):
    """Every word token in the corpus is in the dictionary, except unintelligible-speech marks
    ("?") and, in Slovak, "mm" (missing from the original dictionary)."""
    if not (CORPUS_DIR / slug).exists():
        pytest.skip(f"corpus data not available at {CORPUS_DIR / slug}")
    corpus = cls()
    corpus.load(local_path=CORPUS_DIR / slug)
    assert corpus.sessions is not None
    d = corpus.phonetic_dictionary()
    words = [w.text for s in corpus.sessions.values() for t in s.tasks for i in t.ipus for w in i.words]
    missing = {w for w in words if w not in d}
    assert missing <= {"?", "?-", "-?", "mm"}
    assert sum(w in missing for w in words) / len(words) < 0.01
