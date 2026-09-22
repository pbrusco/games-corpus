"""Machine-restored punctuation for games-corpus transcripts.

WARNING -- NOT HUMAN ANNOTATION. Everything this module loads is punctuation
and capitalization *predicted by an LLM* (Gemini, given the session audio plus
the original unpunctuated transcript), not produced or checked by the
corpus's human annotators. It exists because the source transcripts are
ASR-style (no punctuation, no capitalization at all), which hides real
information for text-only tasks -- e.g. a bare "sí" can be either a genuine
answer to a question or just a backchannel, and only a restored "¿...?"
tells them apart. Treat every `PunctuatedPhrase.text` as a noisy pseudo-label:
a word-level fidelity check rejects phrases where the model appears to have
changed the wording (falling back to the original unpunctuated text in that
case), but false negatives are possible, and even accepted phrases are
unverified by a human. Do not use this as ground truth.

Coverage: only `PILOT_SESSIONS` has been processed so far (UBA Spanish games
corpus). Loading a session outside that set raises `FileNotFoundError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data" / "punctuated_phrases"

#: batch -> session ids that have machine-restored punctuation available.
#: A session is only listed once BOTH speakers' files are shipped -- keep
#: this in sync with games_corpus/data/punctuated_phrases/.
PILOT_SESSIONS: dict[int, frozenset[int]] = {
    1: frozenset({2}),
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


def _phrases_file(batch: int, session_id: int, speaker: str) -> Path:
    return _DATA_DIR / f"b{batch}" / f"s{session_id:02d}.objects.1.{speaker}.phrases"


def available_sessions(batch: int) -> frozenset[int]:
    """Session ids in `batch` that have machine-restored punctuation available."""
    return PILOT_SESSIONS.get(batch, frozenset())


def load_session_punctuated_phrases(batch: int, session_id: int, speaker: str) -> list[PunctuatedPhrase]:
    """Load one session-speaker's machine-restored phrases.

    NOT human annotation -- see this module's docstring before using `text`
    for anything where correctness matters.

    Raises:
        FileNotFoundError: `session_id` isn't in `available_sessions(batch)`.
    """
    if session_id not in available_sessions(batch):
        covered = sorted(available_sessions(batch))
        raise FileNotFoundError(
            f"No machine-restored punctuation for batch {batch} session {session_id} "
            f"(speaker {speaker!r}). Only sessions {covered} have been processed so far."
        )
    path = _phrases_file(batch, session_id, speaker)

    phrases = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        start, end, text = line.split("\t")
        if text == "#":
            continue
        phrases.append(PunctuatedPhrase(speaker=speaker, start=float(start), end=float(end), text=text))
    return phrases
