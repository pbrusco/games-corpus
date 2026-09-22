"""Slovak Games Corpus loader."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from games_corpus import parsers
from games_corpus.base import BaseGamesCorpus
from games_corpus.features import download_features, load_task_features
from games_corpus.types import Session, Task


class SlovakGamesCorpus(BaseGamesCorpus):
    """A class for loading and processing the Slovak Games Corpus.

    This corpus includes Slovak dialogues of task-oriented, collaborative interactions.

    The corpus must be downloaded manually and placed in a local directory.
    Data files are under a 'data/' subdirectory with session folders,
    and session metadata is in 'documents/sessions_info.txt'.
    """

    DEFAULT_PATH = "./corpus/games-slovak/"

    def __init__(self):
        self.sessions: dict[int, Session] | None = None
        self.corpus_local_path: Path | None = None
        self.features_path: Path | None = None

    @property
    def name(self) -> str:
        return "Slovak Games Corpus"

    def load(
        self,
        local_path: str | Path | None = None,
        load_audio: bool = False,
        features_path: str | Path | None = None,
    ) -> None:
        """Load the Slovak Games Corpus from a local directory.

        Args:
            local_path: Path to the corpus directory (default: ./corpus/games-slovak/)
            load_audio: Whether to load audio file references
            features_path: Path to pre-extracted features (e.g. features/games-slovak/)
        """
        self.corpus_local_path = Path(local_path) if local_path else Path(self.DEFAULT_PATH)
        self.features_path = Path(features_path) if features_path else None
        if not self.corpus_local_path.exists():
            raise FileNotFoundError(
                f"Slovak corpus not found at {self.corpus_local_path}. "
                "Please download the Slovak Games Corpus manually and place it there."
            )

        sessions_info = self._parse_sessions_info()
        self._parse_corpus(sessions_info, load_audio)

    def download_features(self, features_dir: str = "features") -> None:
        """Download pre-extracted acoustic features from GitHub Releases.

        Args:
            features_dir: Base directory to store features (default: "features")
        """
        download_features(features_dir, ["games-slovak"])
        self.features_path = Path(features_dir) / "games-slovak"

    def get_features(self, task: Task) -> pd.DataFrame:
        """Get pre-extracted acoustic features for a task as a DataFrame.

        Args:
            task: A Task object from this corpus

        Returns:
            pandas DataFrame with time series of acoustic features
        """
        if self.features_path is None:
            raise ValueError("No features path configured. Pass features_path to load() or call download_features().")
        return load_task_features(self.features_path, task.session_id, task.task_id)

    def _parse_sessions_info(self) -> list[dict[str, Any]]:
        """Parse the documents/sessions_info.txt tab-delimited table."""
        assert self.corpus_local_path is not None
        info_path = self.corpus_local_path / "documents" / "sessions_info.txt"
        if not info_path.exists():
            raise FileNotFoundError(f"Sessions info file not found at {info_path}")

        sessions: list[dict[str, Any]] = []
        with open(info_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                # Header: sessionID  idSpeakerA  genderSpeakerA  idSpeakerB  genderSpeakerB
                if len(parts) == 5 and parts[0].isdigit():
                    sessions.append(
                        {
                            "session_id": int(parts[0]),
                            "subject_a": parts[1],
                            "subject_b": parts[3],
                        }
                    )
        return sessions

    def _parse_corpus(self, sessions_info: list[dict[str, Any]], load_audio: bool) -> None:
        self.sessions = {}
        for info in sessions_info:
            session_id = info["session_id"]
            tasks = self._load_tasks_for_session(session_id, load_audio)
            session_obj = Session(
                session_id=session_id,
                batch=None,
                subject_a=info["subject_a"],
                subject_b=info["subject_b"],
                tasks=tasks,
            )
            self.sessions[session_id] = session_obj

    # ----- File path resolution -----

    def _session_dir(self, session_id: int) -> Path:
        assert self.corpus_local_path is not None
        return self.corpus_local_path / "data" / f"session_{session_id:02d}"

    def _file_path(self, session_id: int, speaker_suffix: str, extension: str) -> Path:
        return self._session_dir(session_id) / f"s{session_id:02d}.objects.1.{speaker_suffix}.{extension}"

    def _resolve_speaker_files(self, session_id: int, extension: str) -> dict[str, Path]:
        """Resolve per-speaker file paths for objects game (part 1)."""
        result: dict[str, Path] = {}
        for speaker in ["A", "B"]:
            path = self._file_path(session_id, speaker, extension)
            if path.exists():
                result[speaker] = path
        return result

    # ----- Task loading -----

    def _load_tasks_for_session(self, session_id: int, load_audio: bool) -> list[Task]:
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            logging.warning(f"Session directory {session_dir} not found. Skipping.")
            return []

        tasks_file = session_dir / f"s{session_id:02d}.objects.1.tasks"
        if not tasks_file.exists():
            logging.warning(f"Tasks file {tasks_file} not found. Skipping session {session_id}.")
            return []

        return parsers.build_tasks_from_files(
            session_id=session_id,
            tasks_info=parsers.load_objects_tasks(tasks_file),
            word_files=self._resolve_speaker_files(session_id, "words"),
            turn_files=self._resolve_speaker_files(session_id, "turns"),
            phrase_files=self._resolve_speaker_files(session_id, "Phrases"),  # Slovak uses capitalized extension
            wav_files=self._resolve_speaker_files(session_id, "wav"),
            load_audio=load_audio,
        )
