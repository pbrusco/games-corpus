"""UBA Spanish Games Corpus loader."""

import logging
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Set

import pandas as pd

from games_corpus.types import Task, Session, BatchConfig
from games_corpus.downloader import CorpusDownloader
from games_corpus.features import load_task_features
from games_corpus import parsers


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

    files: Dict[str, str] = field(
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
    BANNED_SESSIONS: Set[int] = {28}


SPEAKER_SUFFIXES = {
    1: [("A", "A"), ("B", "B")],
    2: [("A", "channel1"), ("B", "channel2")],
}


class SpanishGamesCorpus:
    """
    A class for loading and processing the UBA Games Corpus.
    This corpus includes Spanish dialogues of task-oriented, collaborative interactions.
    """

    def __init__(self):
        self.corpus_raw = None
        self.sessions = None
        self.config = CorpusConfig()
        self.corpus_url = self.config.DEFAULT_URL
        self.corpus_local_path = None
        self.corpus_files = self.config.CORPUS_FILES.files.copy()
        self.batch_configs = {
            1: BatchConfig.create_batch1_config(),
            2: BatchConfig.create_batch2_config(),
        }
        self.downloader = None
        self.features_paths = None

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

    def load(self, url=None, load_audio=False, local_path=None, features_path=None):
        """Load the corpus from a URL or local path.

        Args:
            features_path: Dict mapping batch number to features directory path,
                e.g. {1: "features/games-spanish-batch1", 2: "features/games-spanish-batch2"}.
                Also accepts a single string/Path if features are in one directory.
        """
        self._setup_paths(url, local_path)
        self._filter_audio_files(load_audio)
        if features_path is None:
            self.features_paths = None
        elif isinstance(features_path, dict):
            self.features_paths = {k: Path(v) for k, v in features_path.items()}
        else:
            # Single path — assume it covers all batches
            self.features_paths = {1: Path(features_path), 2: Path(features_path)}
        self.downloader = CorpusDownloader(self.corpus_url, self.corpus_local_path)
        self.downloader.download_corpus(self.corpus_files)
        self._prepare_corpus_data()

    def get_features(self, task):
        """Get pre-extracted acoustic features for a task as a DataFrame.

        Args:
            task: A Task object from this corpus

        Returns:
            pandas DataFrame with time series of acoustic features
        """
        if self.features_paths is None:
            raise ValueError(
                "No features path configured. Pass features_path to load(), "
                "e.g. features_path={1: 'features/games-spanish-batch1', 2: 'features/games-spanish-batch2'}"
            )
        # Determine batch from session ID
        session = self.sessions[task.session_id]
        batch = session.batch
        if batch not in self.features_paths:
            raise ValueError(f"No features path configured for batch {batch}.")
        return load_task_features(self.features_paths[batch], task.session_id, task.task_id)

    def _setup_paths(self, url=None, local_path=None):
        self.corpus_url = url or self.config.DEFAULT_URL
        self.corpus_local_path = Path(local_path) if local_path else Path("./corpus/games-spanish/")
        self.corpus_local_path.mkdir(parents=True, exist_ok=True)

    def _filter_audio_files(self, load_audio):
        if not load_audio:
            self.corpus_files = {k: v for k, v in self.corpus_files.items() if not k.endswith("-wavs")}

    def _prepare_corpus_data(self):
        try:
            self._load_raw_corpus()
            self._parse_corpus()
        except Exception as e:
            raise RuntimeError(f"Failed to prepare corpus data: {e}")

    def get_sessions_by_batch(self, batch):
        return {sid: session for sid, session in self.sessions.items() if session.batch == batch}

    def dev_tasks(self, batch: int):
        batch_sessions = self.get_sessions_by_batch(batch)
        config = self.get_batch_config(batch)
        for sess_id, sess in batch_sessions.items():
            if config.is_heldout_session(sess_id):
                continue
            for task in sess.tasks:
                if config.is_heldout_task(task.session_id, task.task_id):
                    continue
                yield task

    def held_out_tasks(self, batch: int):
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

    def _resolve_files(self, session_id, batch, extension, task_id=None):
        """Resolve per-speaker file paths for a given extension."""
        # Map extension to folder key: turns -> b1-dialogue-turns, words -> b1-dialogue-words, etc.
        folder_map = {
            "turns": f"b{batch}-dialogue-turns",
            "words": f"b{batch}-dialogue-words",
            "phrases": f"b{batch}-dialogue-phrases",
            "wav": f"b{batch}-dialogue-wavs",
        }
        prefix = folder_map[extension]
        folder = self.corpus_raw.get(prefix, {})

        result = {}
        for speaker, suffix in SPEAKER_SUFFIXES[batch]:
            if batch == 1:
                file_id = f"s{session_id:02d}.objects.1.{suffix}.{extension}"
            else:
                file_id = f"s{session_id:02d}.objects.{task_id:02d}.{suffix}.{extension}"
            file_path = folder.get(file_id)
            if file_path:
                result[speaker] = file_path
        return result

    def _resolve_turn_files(self, session_id, batch, task_id=None):
        return self._resolve_files(session_id, batch, "turns", task_id)

    def _resolve_word_files(self, session_id, batch):
        return self._resolve_files(session_id, batch, "words")

    def _resolve_phrase_files(self, session_id, batch, task_id=None):
        return self._resolve_files(session_id, batch, "phrases", task_id)

    def _resolve_wav_files(self, session_id, batch, task_id=None):
        return self._resolve_files(session_id, batch, "wav", task_id)

    # ----- Loading -----

    def _load_raw_corpus(self):
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
                for sub_file in os.listdir(folder_path):
                    sub_file_path = folder_path / sub_file
                    self.corpus_raw[file_id][sub_file] = sub_file_path

    def _parse_corpus(self):
        self.sessions = {}
        for session in self.corpus_raw["sessions-info"].itertuples():
            session_id = session.session_id
            if session_id in self.config.BANNED_SESSIONS:
                logging.warning(f"Skipping banned session: {session_id}")
                continue
            batch = session.batch
            subject_a = session.subject_id_A
            subject_b = session.subject_id_B
            tasks = self._load_tasks_for_session(session_id, batch)
            session_obj = Session(session_id, batch, subject_a, subject_b, tasks)
            self.sessions[session_id] = session_obj

    def _load_tasks_for_session(self, session_id, batch):
        tasks = []

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
            task_id = info["Task ID"]
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
