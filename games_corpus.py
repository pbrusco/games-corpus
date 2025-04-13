"""Games corpus library."""

import logging
from pathlib import Path
import os
import zipfile
import requests
import pandas as pd
import time
from dataclasses import dataclass, field
from typing import Dict, Set
import games_corpus_parsers
from games_corpus_types import Task, Session, BatchConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
    files: Dict[str, str] = field(default_factory=lambda: {
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
    })


class CorpusConfig:
    """Configuration for the UBA Games Corpus"""

    CORPUS_INFO: CorpusInfo = CorpusInfo()
    CORPUS_FILES: CorpusFiles = CorpusFiles()
    DEFAULT_URL: str = "https://ri.conicet.gov.ar/bitstream/handle/11336/191235/{filename}?sequence=29&isAllowed=y"
    BANNED_SESSIONS: Set[int] = {28}


class CorpusDownloader:
    """Handles downloading and extracting corpus files"""

    def __init__(
        self, url: str, local_path: Path, max_retries: int = 3, retry_delay: int = 5
    ):
        self.url = url
        self.local_path = local_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def download_corpus(self, files_to_download: dict):
        """Download all corpus files"""
        for file_id, file_name in files_to_download.items():
            if ".zip" in file_name:
                self._download_and_extract_zip(file_id, file_name)
            else:
                self._download_file(file_name)

    def _download_and_extract_zip(self, file_id: str, file_name: str):
        zip_file_path = self.local_path / file_name
        extracted_folder_path = self.local_path / file_id

        if extracted_folder_path.exists():
            logging.info(f"{file_name} already downloaded.")
            return

        if not zip_file_path.exists():
            self._download_file(file_name, zip_file_path)

        logging.info(f"Extracting {file_name}...")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(self.local_path)

    def _download_file(self, file_name: str, save_path: Path = None):
        save_path = save_path or self.local_path / file_name
        if save_path.exists():
            logging.info(f"{file_name} already exists.")
            return

        for attempt in range(self.max_retries):
            try:
                logging.info(f"Downloading {file_name} (attempt {attempt + 1})...")
                response = requests.get(self.url.format(filename=file_name), timeout=30)
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return
            except (requests.RequestException, IOError) as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to download {file_name}: {e}")
                time.sleep(self.retry_delay)


class SpanishGamesCorpusDialogues:
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

    @property
    def name(self) -> str:
        return self.config.CORPUS_INFO.name

    @property
    def description(self) -> str:
        return self.config.CORPUS_INFO.description

    def get_batch_config(self, batch: int) -> BatchConfig:
        """Get configuration for a specific batch.
        
        Args:
            batch: Batch number to get configuration for
            
        Returns:
            BatchConfig for the specified batch
            
        Raises:
            ValueError: If batch number is not available
        """
        if batch not in self.batch_configs:
            raise ValueError(
                f"Invalid batch number: {batch}. Available batches are: {list(self.batch_configs.keys())}"
            )
        return self.batch_configs[batch]

    def load(self, url=None, load_audio=False, local_path=None):
        """Load the corpus from a URL or local path."""
        self._setup_paths(url, local_path)
        self._filter_audio_files(load_audio)
        self.downloader = CorpusDownloader(self.corpus_url, self.corpus_local_path)
        self.downloader.download_corpus(self.corpus_files)
        self._prepare_corpus_data()

    def _setup_paths(self, url=None, local_path=None):
        """Configure corpus URLs and paths."""
        self.corpus_url = url or self.config.DEFAULT_URL
        self.corpus_local_path = (
            Path(local_path)
            if local_path
            else Path(f"./.{self.config.CORPUS_INFO.short_name}/")
        )
        self.corpus_local_path.mkdir(parents=True, exist_ok=True)

    def _filter_audio_files(self, load_audio):
        """Remove audio files from corpus_files if not loading audio."""
        if not load_audio:
            self.corpus_files = {
                k: v for k, v in self.corpus_files.items() if not k.endswith("-wavs")
            }

    def _prepare_corpus_data(self):
        """Load and parse corpus data."""
        try:
            self._load_raw_corpus()
            self._parse_corpus()
        except Exception as e:
            raise RuntimeError(f"Failed to prepare corpus data: {e}")

    def get_sessions_by_batch(self, batch):
        """Get all sessions for a specific batch"""
        return {
            sid: session
            for sid, session in self.sessions.items()
            if session.batch == batch
        }

    def dev_tasks(self, batch: int):
        """Get development tasks for a specific batch"""
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
        """Get held out tasks for a specific batch"""
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

    def _load_raw_corpus(self):
        # Loads the raw corpus data from the downloaded files into a structured format
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
        # Parse the raw corpus files into a structured format
        self.sessions = {}
        for session in self.corpus_raw["sessions-info"].itertuples():
            session_id = session.session_id
            if (
                session_id in self.config.BANNED_SESSIONS
            ):  # Changed from self.banned_sessions
                logging.warning(f"Skipping banned session: {session_id}")
                continue
            batch = session.batch
            subject_a = session.subject_id_A
            subject_b = session.subject_id_B
            tasks = self._load_tasks_for_session(
                session_id,
                batch,
            )
            session_obj = Session(session_id, batch, subject_a, subject_b, tasks)
            self.sessions[session_id] = session_obj

    def _load_tasks_for_session(self, session_id, batch):
        tasks = []
        if batch == 1:
            tasks_folder = self.corpus_raw["b1-dialogue-tasks"]
            wav_folder = self.corpus_raw.get("b1-dialogue-wavs")
            phrases_folder = self.corpus_raw["b1-dialogue-phrases"]
            turns_folder = self.corpus_raw["b1-dialogue-turns"]
            words_folder = self.corpus_raw["b1-dialogue-words"]
        elif batch == 2:
            tasks_folder = self.corpus_raw["b2-dialogue-tasks"]
            wav_folder = self.corpus_raw.get("b2-dialogue-wavs")
            phrases_folder = self.corpus_raw["b2-dialogue-phrases"]
            turns_folder = self.corpus_raw["b2-dialogue-turns"]
            words_folder = None
        else:
            logging.error(f"Unknown batch number: {batch}")
            return tasks

        # Load tasks from the tasks file
        sess_idx = f"s{str(session_id).zfill(2)}"
        task_file_id = (
            f"{sess_idx}.objects.1.tasks" if batch == 1 else f"{sess_idx}.objects.tasks"
        )
        tasks_file = tasks_folder.get(task_file_id)

        if not tasks_file:
            raise ValueError(f"Tasks file {task_file_id} not found in {tasks_folder}.")
        tasks_info = games_corpus_parsers.load_tasks_info(tasks_file, batch)

        for info in tasks_info:
            task_id = info["Task ID"]
            task_boundaries = (info["Start"], info["End"], task_id, session_id)

            wavs = games_corpus_parsers.load_wavs_for_task(
                session_id, task_id, wav_folder, batch
            )
            ipus = games_corpus_parsers.load_ipus_for_task(
                session_id,
                task_id,
                task_boundaries,
                phrases_folder,
                words_folder,
                batch,
            )

            turns = games_corpus_parsers.load_turns_for_task(
                session_id, task_id, turns_folder, batch, ipus, task_boundaries
            )

            turn_transitions = games_corpus_parsers.load_turn_transitions_for_task(
                session_id,
                task_id,
                turns_folder,
                batch,
                turns,
                task_boundaries,
            )

            task_obj = Task(
                task_id=task_id,
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
