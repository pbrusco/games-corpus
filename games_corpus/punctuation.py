"""Machine-restored punctuation for games-corpus transcripts.

WARNING -- NOT HUMAN ANNOTATION. Everything this module loads is punctuation
and capitalization *predicted by an LLM* (Gemini, given the session audio plus
the original unpunctuated transcript), not produced or checked by any
corpus's human annotators. It exists because the source transcripts are
ASR-style (no punctuation, no capitalization at all), which hides real
information for text-only tasks -- e.g. a bare "sí" can be either a genuine
answer to a question or just a backchannel, and only a restored "¿...?"
tells them apart. Treat every `PunctuatedPhrase.text` as a noisy pseudo-label:
a word-level fidelity check rejects phrases where the model appears to have
changed the wording (falling back to the original unpunctuated text in that
case), but false negatives are possible, and even accepted phrases are
unverified by a human. Do not use this as ground truth.

Known failure mode, quantified by this package's own tests
(test_stripping_punctuation_recovers_the_human_transcript): the fidelity
check is a similarity threshold, not exact match, so it lets through a small
rate (~2-7% of phrases per file in batch 1) of disfluency cleanup -- Gemini
tends to drop stutters, false starts, and filler words in an otherwise-long,
mostly-matching phrase (e.g. "está es hacia" -> "hacia"). Two sessions that
originally hit ~20% from this were re-generated with a stricter threshold;
the remaining baseline is accepted as documented noise, not silently hidden.

Generic across all three corpora (Spanish, English, Slovak) by design, even
though only Spanish has any sessions processed so far -- see `_COVERAGE`.
Prefer `BaseGamesCorpus.get_punctuated_phrases(task)` /
`.available_punctuated_sessions()` over calling this module directly; they
resolve the corpus key for you.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data" / "punctuated_phrases"

#: Corpus class name (`type(corpus).__name__`) -> on-disk directory slug.
#: Add an entry here once a corpus has any processed sessions.
_CORPUS_SLUGS: dict[str, str] = {
    "SpanishGamesCorpus": "games-spanish",
    "EnglishGamesCorpus": "games-english",
    "SlovakGamesCorpus": "games-slovak",
}

#: Corpus class name -> session ids that have machine-restored punctuation
#: available. A session is only listed once BOTH speakers' files are shipped
#: -- keep this in sync with games_corpus/data/punctuated_phrases/.
_COVERAGE: dict[str, frozenset[int]] = {
    "SpanishGamesCorpus": frozenset(range(1, 15)),  # batch 1, sessions 1-14
}


@dataclass(frozen=True)
class PunctuatedPhrase:
    """One phrase with LLM-predicted punctuation/capitalization.

    NOT human-verified -- see this module's docstring. `text` is meant to
    have the same words as the source transcript's phrase (enforced at
    generation time by a word-level fidelity check, with a small known
    false-negative rate -- see the module docstring); punctuation, casing,
    AND diacritics/accents may all differ (e.g. "buho" -> "búho" is an
    intentional orthography fix, not a wording change).
    """

    speaker: str
    start: float
    end: float
    text: str


def _phrases_file(corpus_key: str, session_id: int, speaker: str) -> Path:
    # Same s{session:02d}.objects.1.{speaker}.* naming every corpus already
    # uses for its own raw .phrases files (see e.g. EnglishGamesCorpus._file_path),
    # with an .autopunct. infix so these are never mistaken for the human ones.
    slug = _CORPUS_SLUGS.get(corpus_key, corpus_key)
    return _DATA_DIR / slug / f"s{session_id:02d}.objects.1.{speaker}.autopunct.phrases"


def available_sessions(corpus_key: str) -> frozenset[int]:
    """Session ids for `corpus_key` (e.g. `"SpanishGamesCorpus"`, or
    `type(corpus).__name__`) that have machine-restored punctuation."""
    return _COVERAGE.get(corpus_key, frozenset())


def load_session_punctuated_phrases(corpus_key: str, session_id: int, speaker: str) -> list[PunctuatedPhrase]:
    """Load one session-speaker's machine-restored phrases.

    NOT human annotation -- see this module's docstring before using `text`
    for anything where correctness matters.

    Args:
        corpus_key: `type(corpus).__name__`, e.g. `"SpanishGamesCorpus"`.

    Raises:
        FileNotFoundError: `session_id` isn't in `available_sessions(corpus_key)`.
    """
    if session_id not in available_sessions(corpus_key):
        covered = sorted(available_sessions(corpus_key))
        raise FileNotFoundError(
            f"No machine-restored punctuation for {corpus_key} session {session_id} "
            f"(speaker {speaker!r}). Only sessions {covered} have been processed so far."
        )
    path = _phrases_file(corpus_key, session_id, speaker)

    phrases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue  # a handful of source phrases are zero-duration/empty; not real content
        start, end, text = parts
        if text == "#" or not text:
            continue
        phrases.append(PunctuatedPhrase(speaker=speaker, start=float(start), end=float(end), text=text))
    return phrases
