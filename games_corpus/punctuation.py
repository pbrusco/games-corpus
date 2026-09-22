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
    "SpanishGamesCorpus": frozenset({2}),
}


@dataclass(frozen=True)
class PunctuatedPhrase:
    """One phrase with LLM-predicted punctuation/capitalization.

    NOT human-verified -- see this module's docstring. `text` has the same
    words as the source transcript's phrase (enforced at generation time by a
    word-level fidelity check), only punctuation and casing may differ.
    """

    speaker: str
    start: float
    end: float
    text: str


def _phrases_file(corpus_key: str, session_id: int, speaker: str) -> Path:
    slug = _CORPUS_SLUGS.get(corpus_key, corpus_key)
    return _DATA_DIR / slug / f"session_{session_id:02d}_{speaker}.phrases"


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
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        start, end, text = line.split("\t")
        if text == "#":
            continue
        phrases.append(PunctuatedPhrase(speaker=speaker, start=float(start), end=float(end), text=text))
    return phrases
