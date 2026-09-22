import pytest

from games_corpus.punctuation import (
    PunctuatedPhrase,
    available_sessions,
    load_session_punctuated_phrases,
)


def test_available_sessions_batch1():
    assert available_sessions(1) == frozenset({2})


def test_available_sessions_unknown_batch_is_empty():
    assert available_sessions(999) == frozenset()


def test_load_covered_session():
    phrases = load_session_punctuated_phrases(1, 2, "A")
    assert phrases
    assert all(isinstance(p, PunctuatedPhrase) for p in phrases)
    assert all(p.speaker == "A" for p in phrases)
    # phrases carry restored punctuation/capitalization, not just raw ASR text
    assert any(p.text != p.text.lower() for p in phrases)


def test_load_uncovered_session_raises():
    with pytest.raises(FileNotFoundError, match="session 99"):
        load_session_punctuated_phrases(1, 99, "A")


def test_load_uncovered_session_within_available_batch_raises():
    # session 3 isn't shipped yet even though batch 1 has some coverage
    with pytest.raises(FileNotFoundError):
        load_session_punctuated_phrases(1, 3, "A")
