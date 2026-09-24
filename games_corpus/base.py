"""Abstract base class for dialogue game corpora."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from games_corpus.phonetics import count_phones, load_phonetic_dictionary
from games_corpus.punctuation import PunctuatedPhrase, available_sessions, load_session_punctuated_phrases

if TYPE_CHECKING:
    from games_corpus.types import IPU, Session, Task


class BaseGamesCorpus(ABC):
    """Abstract base class defining the common interface for all games corpora."""

    sessions: dict[int, "Session"] | None

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the corpus."""

    @abstractmethod
    def load(
        self,
        *,
        local_path: str | Path | None = None,
        load_audio: bool = False,
        features_path: str | Path | dict[int, str | Path] | None = None,
    ) -> None:
        """Load corpus sessions and tasks.

        Args:
            local_path: Path to local corpus directory.
            load_audio: Whether to load audio file references.
            features_path: Path to pre-extracted acoustic features directory or mapping.
        """

    @abstractmethod
    def download_features(self, features_dir: str = "features") -> None:
        """Download pre-extracted acoustic features from remote storage."""

    @abstractmethod
    def get_features(self, task: "Task") -> pd.DataFrame:
        """Get pre-extracted acoustic features for a task as a DataFrame."""

    def phonetic_dictionary(self) -> dict[str, tuple[str, ...]]:
        """Word -> phones for this corpus (automatic transcription, see `games_corpus.phonetics`)."""
        return load_phonetic_dictionary(type(self).__name__)

    def num_phones(self, ipu: "IPU") -> int | None:
        """Number of phones in an IPU, or None if one of its words is not in the dictionary
        (e.g. unintelligible-speech marks like "?")."""
        return count_phones((w.text for w in ipu.words), self.phonetic_dictionary())

    def phones_per_second(self, ipu: "IPU") -> float | None:
        """Speech rate of an IPU in phones per second (None if `num_phones` is None)."""
        n = self.num_phones(ipu)
        return None if n is None or ipu.duration <= 0 else n / ipu.duration

    def available_punctuated_sessions(self) -> frozenset[int]:
        """Session ids that have machine-restored punctuation available.

        NOT HUMAN ANNOTATION -- see `games_corpus.punctuation`'s module
        docstring. Empty for corpora/sessions not processed yet.
        """
        return available_sessions(type(self).__name__)

    def get_punctuated_phrases(self, task: "Task") -> list[PunctuatedPhrase]:
        """Get machine-restored punctuation/capitalization for a task, if available.

        NOT HUMAN ANNOTATION -- see `games_corpus.punctuation`'s module
        docstring before relying on the returned text for anything where
        correctness matters. Coverage is currently a small pilot; check
        `available_punctuated_sessions()` first if you want to avoid the
        exception.

        Args:
            task: A Task object from this corpus.

        Returns:
            Both speakers' phrases overlapping the task's time span, in
            chronological order.

        Raises:
            FileNotFoundError: this task's session hasn't been processed.
            ValueError: the corpus hasn't been loaded yet.
        """
        if self.sessions is None:
            raise ValueError("Corpus not loaded. Call load() first.")
        corpus_key = type(self).__name__
        task_end = task.start + task.duration
        phrases = [
            p
            for speaker in ("A", "B")
            for p in load_session_punctuated_phrases(corpus_key, task.session_id, speaker)
            if p.start < task_end and p.end > task.start
        ]
        return sorted(phrases, key=lambda p: p.start)
