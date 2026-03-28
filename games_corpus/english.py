"""Columbia English Games Corpus loader."""

import logging
from pathlib import Path

from games_corpus.types import Task, Session
from games_corpus import parsers


class EnglishGamesCorpus:
    """
    A class for loading and processing the Columbia Games Corpus (English).
    This corpus includes English dialogues of task-oriented, collaborative interactions.

    The corpus must be downloaded manually and placed in a local directory.
    """

    DEFAULT_PATH = "./corpus/games-english/"

    def __init__(self):
        self.sessions = None
        self.corpus_local_path = None

    @property
    def name(self) -> str:
        return "Columbia Games Corpus"

    def load(self, local_path=None, load_audio=False):
        """Load the English Games Corpus from a local directory.

        Args:
            local_path: Path to the corpus directory (default: ./corpus/games-english/)
            load_audio: Whether to load audio file references
        """
        self.corpus_local_path = Path(local_path) if local_path else Path(self.DEFAULT_PATH)
        if not self.corpus_local_path.exists():
            raise FileNotFoundError(
                f"English corpus not found at {self.corpus_local_path}. "
                "Please download the Columbia Games Corpus manually and place it there."
            )

        sessions_info = self._parse_sessions_info()
        self._parse_corpus(sessions_info, load_audio)

    def _parse_sessions_info(self):
        """Parse the README.sessions-info plain text table."""
        readme_path = self.corpus_local_path / "README.sessions-info"
        if not readme_path.exists():
            raise FileNotFoundError(f"Sessions info file not found at {readme_path}")

        sessions = []
        with open(readme_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                parts = line.split()
                # Lines like: 01  101  m  102  m
                if len(parts) == 5 and parts[0].isdigit():
                    sessions.append(
                        {
                            "session_id": int(parts[0]),
                            "subject_a": parts[1],
                            "subject_b": parts[3],
                        }
                    )
        return sessions

    def _parse_corpus(self, sessions_info, load_audio):
        self.sessions = {}
        for info in sessions_info:
            session_id = info["session_id"]
            tasks = self._load_tasks_for_session(session_id, load_audio)
            session_obj = Session(
                session_id=session_id,
                batch=1,
                subject_a=info["subject_a"],
                subject_b=info["subject_b"],
                tasks=tasks,
            )
            self.sessions[session_id] = session_obj

    # ----- File path resolution -----

    def _session_dir(self, session_id):
        return self.corpus_local_path / f"session_{session_id:02d}"

    def _file_path(self, session_id, game, part, speaker_suffix, extension):
        return self._session_dir(session_id) / f"s{session_id:02d}.{game}.{part}.{speaker_suffix}.{extension}"

    def _resolve_speaker_files(self, session_id, extension):
        """Resolve per-speaker file paths for objects game (part 1)."""
        result = {}
        for speaker in ["A", "B"]:
            path = self._file_path(session_id, "objects", 1, speaker, extension)
            if path.exists():
                result[speaker] = path
        return result

    # ----- Task loading -----

    def _load_tasks_for_session(self, session_id, load_audio):
        tasks = []
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            logging.warning(f"Session directory {session_dir} not found. Skipping.")
            return tasks

        tasks_file = session_dir / f"s{session_id:02d}.objects.1.tasks"
        if not tasks_file.exists():
            logging.warning(f"Tasks file {tasks_file} not found. Skipping session {session_id}.")
            return tasks

        tasks_info = parsers.load_objects_tasks(tasks_file)

        word_files = self._resolve_speaker_files(session_id, "words")
        turn_files = self._resolve_speaker_files(session_id, "turns")
        phrase_files = self._resolve_speaker_files(session_id, "phrases")

        for info in tasks_info:
            task_id = info["Task ID"]
            task_boundaries = (info["Start"], info["End"], task_id, session_id)

            # Load IPUs: prefer words if available, fall back to phrases
            if word_files:
                ipus = parsers.load_ipus_from_words(word_files, task_boundaries)
            elif phrase_files:
                ipus = parsers.load_ipus_from_phrases(phrase_files)
            else:
                ipus = []

            turns = parsers.load_turns_for_task(session_id, task_id, turn_files, ipus, task_boundaries)
            turn_transitions = parsers.load_turn_transitions_for_task(
                session_id, task_id, turn_files, turns, task_boundaries
            )

            wav_files = {}
            if load_audio:
                wav_files = parsers.load_wavs_for_task(self._resolve_speaker_files(session_id, "wav"))

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
                wavs=wav_files,
                turns=turns,
            )
            tasks.append(task_obj)

        return tasks
