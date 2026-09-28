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

Control tasks of batch 2, English and Slovak (task-level files): the fidelity check rejected (and kept
the original text of) ~2% of the phrases in batch 2, ~1% in Slovak and ~9% in English, whose transcripts
mark many cut-off words ("o-", "ther-") that the model tends to clean up. The check compares letters of
any alphabet (Slovak diacritics included).

Generic across all three corpora (Spanish, English, Slovak). Coverage comes in
two granularities: whole sessions (batch 1 of the Spanish corpus, `_COVERAGE`)
and single tasks (the control tasks of batch 2, English and Slovak, processed
task by task to restore only what an evaluation needs; `available_tasks`).
Prefer `BaseGamesCorpus.get_punctuated_phrases(task)` /
`.available_punctuated_sessions()` over calling this module directly; they
resolve the corpus key for you.
"""

from __future__ import annotations

import re
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


def _task_file(corpus_key: str, session_id: int, task_id: int, speaker: str) -> Path:
    # task-level files: s{session:02d}.objects.{task:02d}.{speaker}.autopunct.phrases, in the corpus's own
    # times (session-relative for English/Slovak, task-relative for Spanish batch 2), so they match its IPUs
    slug = _CORPUS_SLUGS.get(corpus_key, corpus_key)
    return _DATA_DIR / slug / f"s{session_id:02d}.objects.{task_id:02d}.{speaker}.autopunct.phrases"


_TASK_FILE_RE = re.compile(r"s(\d+)\.objects\.(\d{2})\.([AB])\.autopunct\.phrases")


def available_tasks(corpus_key: str) -> frozenset[tuple[int, int]]:
    """(session_id, task_id) pairs with task-level machine-restored punctuation for both speakers."""
    d = _DATA_DIR / _CORPUS_SLUGS.get(corpus_key, corpus_key)
    speakers: dict[tuple[int, int], set[str]] = {}
    for f in d.glob("*.autopunct.phrases") if d.exists() else []:
        m = _TASK_FILE_RE.fullmatch(f.name)
        if m:
            speakers.setdefault((int(m[1]), int(m[2])), set()).add(m[3])
    return frozenset(k for k, v in speakers.items() if v == {"A", "B"})


def _read_phrases(path: Path, speaker: str) -> list[PunctuatedPhrase]:
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


def load_task_punctuated_phrases(
    corpus_key: str, session_id: int, task_id: int, speaker: str
) -> list[PunctuatedPhrase]:
    """Load one task-speaker's machine-restored phrases (NOT human annotation, see the module docstring).

    Raises:
        FileNotFoundError: the task isn't in `available_tasks(corpus_key)`.
    """
    if (session_id, task_id) not in available_tasks(corpus_key):
        raise FileNotFoundError(
            f"No machine-restored punctuation for {corpus_key} session {session_id} task {task_id}."
        )
    return _read_phrases(_task_file(corpus_key, session_id, task_id, speaker), speaker)


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
    return _read_phrases(_phrases_file(corpus_key, session_id, speaker), speaker)
