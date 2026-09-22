"""UBA Spanish Games Corpus loader."""

import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from games_corpus import parsers
from games_corpus.base import BaseGamesCorpus
from games_corpus.downloader import CorpusDownloader
from games_corpus.features import download_features, load_task_features
from games_corpus.types import BatchConfig, Session, Task


@dataclass(frozen=True)
class CorpusInfo:
    """Metadata about the corpus."""

    name: str = "UBA Games Corpus"
    short_name: str = "uba-games"
    description: str = "The UBA Games Corpus includes Spanish dialogues..."
    language: str = "Spanish"
    participants: str = "Native speakers of Argentine Spanish"
    age_range: str = "19-59 years"


@dataclass(frozen=True)
class CorpusFiles:
    """Mapping of corpus file identifiers to their filenames."""

    files: dict[str, str] = field(
        default_factory=lambda: {
            "b1-dialogue-phrases": "b1-dialogue-phrases.zip",
            "b1-dialogue-tasks": "b1-dialogue-tasks.zip",
            "b1-dialogue-turns": "b1-dialogue-turns.zip",
            "b1-dialogue-wavs": "b1-dialogue-wavs.zip",
            "b1-dialogue-words": "b1-dialogue-words.zip",
            "b2-dialogue-phrases": "b2-dialogue-phrases.zip",
            "b2-dialogue-tasks": "b2-dialogue-tasks.zip",
            "b2-dialogue-turns": "b2-dialogue-turns.zip",
            "b2-dialogue-wavs": "b2-dialogue-wavs.zip",
            "sessions-info": "sessions-info.csv",
            "subjects-info": "subjects-info.csv",
        }
    )


class CorpusConfig:
    """Configuration for the UBA Games Corpus"""

    CORPUS_INFO: CorpusInfo = CorpusInfo()
    CORPUS_FILES: CorpusFiles = CorpusFiles()
    DEFAULT_URL: str = "https://ri.conicet.gov.ar/bitstream/handle/11336/191235/{filename}?sequence=29&isAllowed=y"
    BANNED_SESSIONS: set[int] = {28}


SPEAKER_SUFFIXES = {
    1: [("A", "A"), ("B", "B")],
    2: [("A", "channel1"), ("B", "channel2")],
}


class SpanishGamesCorpus(BaseGamesCorpus):
    """A class for loading and processing the UBA Games Corpus.

    This corpus includes Spanish dialogues of task-oriented, collaborative interactions.
    """

    def __init__(self):
        self.corpus_raw: dict[str, Any] | None = None
        self.sessions: dict[int, Session] | None = None
        self.config = CorpusConfig()
        self.corpus_url = self.config.DEFAULT_URL
        self.corpus_local_path: Path | None = None
        self.corpus_files = self.config.CORPUS_FILES.files.copy()
        self.batch_configs = {
            1: BatchConfig.create_batch1_config(),
            2: BatchConfig.create_batch2_config(),
        }
        self.downloader: CorpusDownloader | None = None
        self.features_paths: dict[int, Path] | None = None

    @property
    def name(self) -> str:
        return self.config.CORPUS_INFO.name

    @property
    def description(self) -> str:
        return self.config.CORPUS_INFO.description

    def get_batch_config(self, batch: int) -> BatchConfig:
        if batch not in self.batch_configs:
            raise ValueError(f"Invalid batch number: {batch}. Available batches are: {list(self.batch_configs.keys())}")
        return self.batch_configs[batch]

    def load(
        self,
        local_path: str | Path | None = None,
        load_audio: bool = False,
        features_path: str | Path | dict[int, str | Path] | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Load the corpus from a URL or local path.

        Args:
            local_path: Path to directory where corpus is stored
            load_audio: Whether to include wav audio file paths
            features_path: Dict mapping batch number to features directory path,
                e.g. {1: "features/games-spanish-batch1", 2: "features/games-spanish-batch2"}.
                Also accepts a single string/Path if features are in one directory.
            url: Optional URL template for downloading
            **kwargs: Additional options
        """
        if url is None and isinstance(local_path, str) and local_path.startswith(("http://", "https://")):
            url = local_path
            local_path = None

        self._setup_paths(url, local_path)
        self._filter_audio_files(load_audio)
        if features_path is None:
            self.features_paths = None
        elif isinstance(features_path, dict):
            self.features_paths = {k: Path(v) for k, v in features_path.items()}
        else:
            # Single path — assume it covers all batches
            self.features_paths = {1: Path(features_path), 2: Path(features_path)}
        assert self.corpus_local_path is not None
        self.downloader = CorpusDownloader(self.corpus_url, self.corpus_local_path)
        self.downloader.download_corpus(self.corpus_files)
        self._prepare_corpus_data()

    def download_features(self, features_dir: str = "features") -> None:
        """Download pre-extracted acoustic features from GitHub Releases.

        Args:
            features_dir: Base directory to store features (default: "features")
        """
        download_features(features_dir, ["games-spanish-batch1", "games-spanish-batch2"])
        self.features_paths = {
            1: Path(features_dir) / "games-spanish-batch1",
            2: Path(features_dir) / "games-spanish-batch2",
        }

    def get_features(self, task: Task) -> pd.DataFrame:
        """Get pre-extracted acoustic features for a task as a DataFrame.

        Args:
            task: A Task object from this corpus

        Returns:
            pandas DataFrame with time series of acoustic features
        """
        if self.features_paths is None:
            raise ValueError("No features path configured. Call download_features() or pass features_path to load().")
        if self.sessions is None:
            raise ValueError("Corpus not loaded. Call load() first.")
        # Determine batch from session ID
        session = self.sessions[task.session_id]
        batch = session.batch
        if batch is None or batch not in self.features_paths:
            raise ValueError(f"No features path configured for batch {batch}.")
        return load_task_features(self.features_paths[batch], task.session_id, task.task_id)

    def _setup_paths(self, url: str | None = None, local_path: str | Path | None = None) -> None:
        self.corpus_url = url or self.config.DEFAULT_URL
        self.corpus_local_path = Path(local_path) if local_path else Path("./corpus/games-spanish/")
        self.corpus_local_path.mkdir(parents=True, exist_ok=True)

    def _filter_audio_files(self, load_audio: bool) -> None:
        if not load_audio:
            self.corpus_files = {k: v for k, v in self.corpus_files.items() if not k.endswith("-wavs")}

    def _prepare_corpus_data(self) -> None:
        try:
            self._load_raw_corpus()
            self._parse_corpus()
        except Exception as e:
            raise RuntimeError(f"Failed to prepare corpus data: {e}") from e

    def get_sessions_by_batch(self, batch: int) -> dict[int, Session]:
        if self.sessions is None:
            return {}
        return {sid: session for sid, session in self.sessions.items() if session.batch == batch}

    def dev_tasks(self, batch: int) -> Iterator[Task]:
        batch_sessions = self.get_sessions_by_batch(batch)
        config = self.get_batch_config(batch)
        for sess_id, sess in batch_sessions.items():
            if config.is_heldout_session(sess_id):
                continue
            for task in sess.tasks:
                if config.is_heldout_task(task.session_id, task.task_id):
                    continue
                yield task

    def held_out_tasks(self, batch: int) -> Iterator[Task]:
        batch_sessions = self.get_sessions_by_batch(batch)
        config = self.get_batch_config(batch)
        for sess_id, sess in batch_sessions.items():
            if config.is_heldout_session(sess_id):
                for task in sess.tasks:
                    yield task
            else:
                for task in sess.tasks:
                    if config.is_heldout_task(sess_id, task.task_id):
                        yield task

    # ----- File path resolution -----

    def _resolve_files(
        self, session_id: int, batch: int, extension: str, task_id: int | None = None
    ) -> dict[str, Path]:
        """Resolve per-speaker file paths for a given extension."""
        if self.corpus_raw is None:
            return {}
        # Map extension to folder key: turns -> b1-dialogue-turns, words -> b1-dialogue-words, etc.
        folder_map = {
            "turns": f"b{batch}-dialogue-turns",
            "words": f"b{batch}-dialogue-words",
            "phrases": f"b{batch}-dialogue-phrases",
            "wav": f"b{batch}-dialogue-wavs",
        }
        prefix = folder_map[extension]
        folder = self.corpus_raw.get(prefix, {})

        result: dict[str, Path] = {}
        for speaker, suffix in SPEAKER_SUFFIXES[batch]:
            if batch == 1:
                file_id = f"s{session_id:02d}.objects.1.{suffix}.{extension}"
            else:
                file_id = f"s{session_id:02d}.objects.{task_id:02d}.{suffix}.{extension}"
            file_path = folder.get(file_id)
            if file_path:
                result[speaker] = file_path
        return result

    def _resolve_turn_files(self, session_id: int, batch: int, task_id: int | None = None) -> dict[str, Path]:
        return self._resolve_files(session_id, batch, "turns", task_id)

    def _resolve_word_files(self, session_id: int, batch: int) -> dict[str, Path]:
        return self._resolve_files(session_id, batch, "words")

    def _resolve_phrase_files(self, session_id: int, batch: int, task_id: int | None = None) -> dict[str, Path]:
        return self._resolve_files(session_id, batch, "phrases", task_id)

    def _resolve_wav_files(self, session_id: int, batch: int, task_id: int | None = None) -> dict[str, Path]:
        return self._resolve_files(session_id, batch, "wav", task_id)

    # ----- Loading -----

    def _load_raw_corpus(self) -> None:
        assert self.corpus_local_path is not None
        self.corpus_raw = {}
        for file_id, file_name in self.corpus_files.items():
            file_path = self.corpus_local_path / file_name
            if file_name.endswith(".csv"):
                logging.info(f"Loading CSV file: {file_name}")
                self.corpus_raw[file_id] = pd.read_csv(file_path)
            elif file_name.endswith(".zip"):
                folder_path = self.corpus_local_path / file_id
                logging.info(f"Loading extracted ZIP folder: {file_id}")
                self.corpus_raw[file_id] = {}
                if folder_path.exists():
                    for sub_file in os.listdir(folder_path):
                        sub_file_path = folder_path / sub_file
                        self.corpus_raw[file_id][sub_file] = sub_file_path

    def _parse_corpus(self) -> None:
        assert self.corpus_raw is not None
        self.sessions = {}
        for session in self.corpus_raw["sessions-info"].itertuples():
            session_id = int(session.session_id)
            if session_id in self.config.BANNED_SESSIONS:
                logging.warning(f"Skipping banned session: {session_id}")
                continue
            batch = int(session.batch)
            subject_a = str(session.subject_id_A)
            subject_b = str(session.subject_id_B)
            tasks = self._load_tasks_for_session(session_id, batch)
            session_obj = Session(session_id, batch, subject_a, subject_b, tasks)
            self.sessions[session_id] = session_obj

    def _load_tasks_for_session(self, session_id: int, batch: int) -> list[Task]:
        assert self.corpus_raw is not None
        tasks: list[Task] = []

        # Resolve tasks file
        if batch == 1:
            tasks_folder = self.corpus_raw["b1-dialogue-tasks"]
            task_file_id = f"s{session_id:02d}.objects.1.tasks"
        elif batch == 2:
            tasks_folder = self.corpus_raw["b2-dialogue-tasks"]
            task_file_id = f"s{session_id:02d}.objects.tasks"
        else:
            logging.error(f"Unknown batch number: {batch}")
            return tasks

        tasks_file = tasks_folder.get(task_file_id)
        if not tasks_file:
            raise ValueError(f"Tasks file {task_file_id} not found.")

        if batch == 1:
            tasks_info = parsers.load_objects_tasks(tasks_file)
        else:
            tasks_info = parsers.load_objects_tasks_b2(tasks_file)

        for info in tasks_info:
            task_id = int(info["Task ID"])
            task_boundaries = (info["Start"], info["End"], task_id, session_id)

            # Resolve per-speaker file paths
            turn_files = self._resolve_turn_files(session_id, batch, task_id)
            wav_files = self._resolve_wav_files(session_id, batch, task_id)

            # Load IPUs (words for B1, phrases for B2)
            if batch == 1:
                word_files = self._resolve_word_files(session_id, batch)
                ipus = parsers.load_ipus_from_words(word_files, task_boundaries)
            else:
                phrase_files = self._resolve_phrase_files(session_id, batch, task_id)
                ipus = parsers.load_ipus_from_phrases(phrase_files)

            turns = parsers.load_turns_for_task(session_id, task_id, turn_files, ipus, task_boundaries)
            turn_transitions = parsers.load_turn_transitions_for_task(
                session_id, task_id, turn_files, turns, task_boundaries
            )
            wavs = parsers.load_wavs_for_task(wav_files)

            task_obj = Task(
                task_id=task_id,
                start=info["Start"],
                duration=info["End"] - info["Start"],
                session_id=session_id,
                images=info["Images"],
                describer=info["Describer"],
                target=info["Target"],
                score=info["Score"],
                time_used=info["Time-used"],
                turn_transitions=turn_transitions,
                ipus=ipus,
                wavs=wavs,
                turns=turns,
            )
            tasks.append(task_obj)

        return tasks
