from pathlib import Path

import pytest

from games_corpus import SpanishGamesCorpus
from games_corpus.punctuation import (
    PunctuatedPhrase,
    available_sessions,
    load_session_punctuated_phrases,
)

SPANISH_CORPUS_PATH = Path(__file__).resolve().parent.parent / "corpus" / "games-spanish"
requires_spanish_corpus = pytest.mark.skipif(
    not (SPANISH_CORPUS_PATH / "sessions-info.csv").exists(),
    reason="Spanish corpus not available locally",
)


def test_available_sessions_spanish():
    assert available_sessions("SpanishGamesCorpus") == frozenset({2})


def test_available_sessions_unprocessed_corpus_is_empty():
    assert available_sessions("EnglishGamesCorpus") == frozenset()
    assert available_sessions("SlovakGamesCorpus") == frozenset()


def test_available_sessions_unknown_key_is_empty():
    assert available_sessions("NotACorpus") == frozenset()


def test_load_covered_session():
    phrases = load_session_punctuated_phrases("SpanishGamesCorpus", 2, "A")
    assert phrases
    assert all(isinstance(p, PunctuatedPhrase) for p in phrases)
    assert all(p.speaker == "A" for p in phrases)
    # phrases carry restored punctuation/capitalization, not just raw ASR text
    assert any(p.text != p.text.lower() for p in phrases)


def test_load_uncovered_session_raises():
    with pytest.raises(FileNotFoundError, match="session 99"):
        load_session_punctuated_phrases("SpanishGamesCorpus", 99, "A")


def test_load_uncovered_session_within_partially_covered_corpus_raises():
    # session 3 isn't shipped yet even though SpanishGamesCorpus has some coverage
    with pytest.raises(FileNotFoundError):
        load_session_punctuated_phrases("SpanishGamesCorpus", 3, "A")


def test_load_from_corpus_with_no_coverage_raises():
    with pytest.raises(FileNotFoundError):
        load_session_punctuated_phrases("EnglishGamesCorpus", 1, "A")


@requires_spanish_corpus
class TestBaseGamesCorpusIntegration:
    """The shared BaseGamesCorpus methods, exercised through a real corpus."""

    @pytest.fixture(scope="class")
    def corpus(self):
        c = SpanishGamesCorpus()
        c.load(load_audio=False, local_path=str(SPANISH_CORPUS_PATH))
        return c

    def test_available_punctuated_sessions(self, corpus):
        assert corpus.available_punctuated_sessions() == frozenset({2})

    def test_get_punctuated_phrases_for_covered_task(self, corpus):
        task = next(t for t in corpus.dev_tasks(batch=1) if t.session_id == 2 and t.task_id == 1)
        phrases = corpus.get_punctuated_phrases(task)
        assert phrases
        assert {p.speaker for p in phrases} <= {"A", "B"}
        assert all(task.start <= p.start <= task.start + task.duration for p in phrases)

    def test_get_punctuated_phrases_for_uncovered_task_raises(self, corpus):
        task = next(t for t in corpus.dev_tasks(batch=1) if t.session_id == 4 and t.task_id == 1)
        with pytest.raises(FileNotFoundError):
            corpus.get_punctuated_phrases(task)

    def test_get_punctuated_phrases_before_load_raises(self):
        fresh = SpanishGamesCorpus()
        # any Task will do -- it should fail on the "not loaded" check first
        with pytest.raises(ValueError, match="not loaded"):
            fresh.get_punctuated_phrases(None)  # type: ignore[arg-type]
