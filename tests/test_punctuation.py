import re
import unicodedata
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

_WORD_RE = re.compile(r"[a-záéíóúñü]+", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]*>")  # non-lexical annotations, e.g. <risa>, <tos>


def _fold_accents(text: str) -> str:
    # The ASR source transcripts carry accents inconsistently (present on
    # some phrases, dropped on others); Gemini's restoration adds/corrects
    # them (e.g. "buho" -> "búho") as part of normal orthography, not a
    # wording change. Fold both sides to compare underlying words regardless
    # of accent marks -- ñ is a distinct letter in Spanish, not an accented
    # n, so it's deliberately preserved.
    return (
        "".join(
            c
            for c in unicodedata.normalize("NFD", text.replace("ñ", "\0").replace("Ñ", "\1"))
            if unicodedata.category(c) != "Mn"
        )
        .replace("\0", "ñ")
        .replace("\1", "Ñ")
    )


def _strip_punctuation(text: str) -> str:
    """Undo restoration: drop non-lexical annotation tags, lowercase, fold
    accents, drop everything but letters, single-space words. Used to check
    the autopunct text still says the same words as the original human
    (unpunctuated) transcript -- the one invariant restoration is never
    allowed to break."""
    text = _TAG_RE.sub(" ", text)
    return " ".join(w.lower() for w in _WORD_RE.findall(_fold_accents(text)))


def _load_raw_phrases(session_id: int, speaker: str) -> dict[tuple[float, float], str]:
    """The original, human, unpunctuated .phrases file -- start/end are
    exact floats as stored, so this is keyed the same way autopunct files
    are (same source timestamps, untouched by restoration)."""
    path = SPANISH_CORPUS_PATH / "b1-dialogue-phrases" / f"s{session_id:02d}.objects.1.{speaker}.phrases"
    phrases = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        start, end, text = line.split("\t")
        if text == "#":
            continue
        phrases[(float(start), float(end))] = text
    return phrases


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
@pytest.mark.parametrize("speaker", ["A", "B"])
def test_stripping_punctuation_recovers_the_human_transcript(speaker):
    """The one invariant restoration must never violate: punctuation/casing
    may differ from the human .phrases file, but the words underneath must
    not -- this is exactly what the fidelity check enforces at generation
    time, checked here directly against the shipped data and the original
    corpus files it was derived from."""
    raw = _load_raw_phrases(2, speaker)
    autopunct = load_session_punctuated_phrases("SpanishGamesCorpus", 2, speaker)
    assert autopunct  # would pass vacuously on an empty list otherwise

    matched = 0
    for phrase in autopunct:
        original = raw.get((phrase.start, phrase.end))
        assert original is not None, f"no matching human phrase for {phrase}"
        # Normalize both sides the same way: the source transcripts carry
        # accents inconsistently (present on some phrases, absent on others),
        # so only folding the restored side would flag that inconsistency as
        # a false mismatch.
        assert _strip_punctuation(phrase.text) == _strip_punctuation(original)
        matched += 1
    assert matched == len(raw)


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
