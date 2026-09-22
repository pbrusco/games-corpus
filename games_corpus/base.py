"""Abstract base class for dialogue game corpora."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from games_corpus.types import Session, Task


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
