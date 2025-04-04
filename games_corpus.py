"""
Games corpus library. See https://www.utdt.edu/ia/integrantes/agravano/UBA-Games-Corpus/ 
"""

import logging
from pathlib import Path
import os
import zipfile
import requests
import pandas as pd
import time
from typing import Dict, List, Union, Any
from enum import Enum

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SpanishGamesCorpusDialogues:
    def __init__(self):
        self.corpus_raw = None
        self.sessions = None
        self.corpus_url = (
            "https://ri.conicet.gov.ar/bitstream/handle/11336/191235/{filename}?sequence=29&isAllowed=y"
        ) 
        # "https://www.utdt.edu/ia/integrantes/agravano/UBA-Games-Corpus/{filename}"

        self.corpus_local_path = None

        # Corpus files:
        self.corpus_files = {
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
        self.info = {
            "name": "UBA Games Corpus",
            "short_name": "uba-games",
            "description": "The UBA Games Corpus includes the files listed in Table 2. There is an important difference in the organization of files in batches 1 and 2. For the dialogues in batch 1, there is one file per session (and speaker). In this way, the file sNN.objects.1.{A,B}.wav (with NN=01..14) corresponds to the audio for the entire session NN (and speaker A/B); this file includes all 14 game tasks in that session. The file sNN.objects.1.{A,B}.tasks specifies the start and end times of each game task, as explained below.",
            "language": "Spanish",
            "participants": "Native speakers of Argentine Spanish",
            "age_range": "19-59 years",
        }

        self.banned_sessions = set([28])
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def load(self, url=None, load_audio=False, local_path=None):
        # Load the corpus from the specified URL and parse it into a dictionary
        # If the corpus has been downloaded already, it only loads it.
        # If local path is provided, it saves/load the corpus to/from that path.
        if url:
            self.corpus_url = url

        if local_path:
            self.corpus_local_path = Path(local_path)
        else:
            self.corpus_local_path = Path(f"./.{self.info['short_name']}/")

        self.corpus_local_path.mkdir(parents=True, exist_ok=True)

        if not load_audio:
            self.corpus_files = {
                k: v for k, v in self.corpus_files.items() if not k.endswith("-wavs")
            }

        # Download the corpus files
        self._download()
        # Load the corpus from the downloaded files

        self._load_raw_corpus()
        self._parse_corpus()

    def get_sessions_by_batch(self, batch):
        """Get all sessions for a specific batch"""
        return {
            sid: session
            for sid, session in self.sessions.items()
            if session.batch == batch
        }

    def _download(self):
        for file_id, file_name in self.corpus_files.items():
            if ".zip" in file_name:
                self._download_and_extract_zip(file_id, file_name)
            else:
                self._download_file(file_name)

    def _download_and_extract_zip(self, file_id, file_name):
        zip_file_path = self.corpus_local_path / file_name
        extracted_folder_path = self.corpus_local_path / file_id

        if extracted_folder_path.exists():
            logging.info(f"{file_name} already downloaded.")
            return

        if not zip_file_path.exists():
            self._download_file(file_name, zip_file_path)

        logging.info(f"Extracting {file_name}...")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(self.corpus_local_path)

    def _download_file(self, file_name, save_path=None):
        save_path = save_path or self.corpus_local_path / file_name
        if save_path.exists():
            logging.info(f"{file_name} already exists.")
            return

        for attempt in range(self.max_retries):
            try:
                logging.info(f"Downloading {file_name} (attempt {attempt + 1})...")
                response = requests.get(self.corpus_url.format(filename=file_name), timeout=30)
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return
            except (requests.RequestException, IOError) as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to download {file_name}: {e}")
                time.sleep(self.retry_delay)

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
            if session_id in self.banned_sessions:
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
        sess_idx = f"s{str(session_id).zfill(2)}"  # Ensure session ID is zero-padded to 2 digits
        task_file_id = (
            f"{sess_idx}.objects.1.tasks" if batch == 1 else f"{sess_idx}.objects.tasks"
        )
        tasks_file = tasks_folder.get(task_file_id)

        if not tasks_file:
            raise ValueError(f"Tasks file {task_file_id} not found in {tasks_folder}.")
        tasks_info = load_tasks_info(tasks_file, batch)

        for info in tasks_info:
            task_id = info["Task ID"]
            task_boundaries = (info["Start"], info["End"], task_id, session_id)

            wavs = load_wavs_for_task(session_id, task_id, wav_folder, batch)
            ipus = load_ipus_for_task(
                session_id,
                task_id,
                task_boundaries,
                phrases_folder,
                words_folder,
                batch,
            )

            turn_transitions = load_turn_transitions_for_task(
                session_id, task_id, turns_folder, phrases_folder, batch, ipus
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
            )
            tasks.append(task_obj)

        return tasks


class Task:
    def __init__(
        self,
        task_id: str,
        session_id: int,
        images: List[str],
        describer: str,
        target: str,
        score: Union[float, str],
        time_used: float,
        turn_transitions: List["TurnTransition"],
        ipus: List["IPU"],
        wavs: Dict[str, str],
    ) -> None:
        self.task_id = task_id
        self.session_id = session_id
        self.images = images
        self.describer = describer
        self.target = target
        self.score = float(score)
        self.start = ipus[0].start
        self.duration = float(time_used)
        self.turn_transitions = turn_transitions
        self.ipus = sorted(ipus, key=lambda x: x.start) if ipus else []
        self.wavs = wavs
        self.text = self._build_text()

    def _build_text(self) -> str:
        """Build readable text from IPUs"""
        if not self.ipus:
            return ""
        return "\n\t" + "\n\t".join([str(ipu) for ipu in self.ipus])

    def __repr__(self) -> str:
        return f"Task({self.task_id}, {self.session_id}, {self.describer}, {self.target}, {self.score}, {self.duration}, {len(self.ipus)} IPUs, {len(self.wavs)} wavs)"

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class Session:
    def __init__(
        self,
        session_id: int,
        batch: int,
        subject_a: str,
        subject_b: str,
        tasks: List[Task],
    ) -> None:
        self.session_id = session_id
        self.batch = batch
        self.subject_a = subject_a
        self.subject_b = subject_b
        self.tasks = tasks

    def __repr__(self) -> str:
        return f"Session({self.session_id}, {self.batch}, {self.subject_a}, {self.subject_b}, {len(self.tasks)} tasks)"

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class Word:
    def __init__(self, start: float, end: float, text: str, speaker: str) -> None:
        self.start = start
        self.end = end
        self.text = text
        self.speaker = speaker
        self.duration = end - start

    def __repr__(self) -> str:
        return f"Word({self.start}, {self.end}, {self.text})"

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class IPU:
    def __init__(self, words: List[Word]):
        self.words = words
        self.start = words[0].start
        self.end = words[-1].end
        self.speaker = words[0].speaker
        self.duration = self.end - self.start
        self.text = " ".join([word.text for word in words])
        self.num_words = len(words)

    def __repr__(self):
        return f"[{self.start}:{self.end}] {self.speaker}: {self.text}"

    def __getitem__(self, key):
        return getattr(self, key)


class TurnTransitionType(Enum):
    # Regular transitions
    HOLD_TURN = "H"
    SMOOTH_SWITCH = "S"
    BACKCHANNEL = "BC"
    PAUSED_INTERRUPTION = "PI"

    # Overlapped transitions
    OVERLAPPED_SWITCH = "O"
    OVERLAPPED_BACKCHANNEL = "BC_O"
    OVERLAPPED_INTERRUPTION = "I"
    OVERLAPPED_BUTT_IN = "BI"

    # Special transitions
    FIRST_TURN = "X1"
    BACKCHANNEL_CONTINUATION = "X2"
    OVERLAPPED_BACKCHANNEL_CONTINUATION = "X2_O"
    SIMULTANEOUS_START = "X3"

    AMBIGUOUS = "A"

    @classmethod
    def from_string(cls, label: str) -> "TurnTransitionType":
        """Convert string label to TurnTransitionType enum member"""
        label = label.upper()
        for member in cls:
            if member.value == label:
                return member
        raise ValueError(f"Unknown transition label: {label}")

    def __str__(self) -> str:
        return self.value


class TurnTransition:
    def __init__(self, label: str, ipu_from: IPU, ipu_to: IPU):
        self.label = TurnTransitionType.from_string(label)
        self.ipu_from = ipu_from
        self.ipu_to = ipu_to
        self.duration = ipu_to.start - ipu_from.end
        self.overlapped_transition = self.duration < 0

    def __repr__(self):
        return f"TurnTransition({self.label}, {self.ipu_from}, {self.ipu_to})"


def load_tasks_info(tasks_file, batch):
    tasks_info = []

    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if batch == 1:
                task_info = line.split(";")
                if len(task_info) < 3:
                    continue

                start_end_images, describer, target, score, time_used = task_info
                start, end, images = start_end_images.split(" ")
                start = float(start)
                end = float(end)
                images = images.split("Images:")[-1]
                task_id = f"{len(tasks_info) + 1:02d}"
                time_used = float(time_used.split(":")[-1].strip())

            elif batch == 2:
                task_id, task_info = line.split(" ", 1)
                images, describer, target, score, time_used = task_info.split(";")
                start = 0
                time_used = float(time_used.split(":")[-1].strip())
                end = time_used

            images = images.split(",")
            describer = describer.split(":")[-1].strip()
            target = target.split(":")[-1].strip()
            score = score.split(":")[-1].strip()
            tasks_info.append(
                {
                    "Task ID": task_id,
                    "Start": start,
                    "End": end,
                    "Images": images,
                    "Describer": describer,
                    "Target": target,
                    "Score": score,
                    "Time-used": time_used,
                }
            )

    return tasks_info


def find_nearest_ipu(ipus, start_time, end_time, max_diff=0.1):
    """Find IPU that best matches the given timestamps"""
    best_ipu = None
    min_diff = float("inf")

    for ipu in ipus:
        start_diff = abs(ipu.start - start_time)
        end_diff = abs(ipu.end - end_time)
        total_diff = start_diff + end_diff

        if total_diff < min_diff and total_diff < max_diff:
            min_diff = total_diff
            best_ipu = ipu

    return best_ipu


def load_turn_transitions_for_task(
    session_id: int,
    task_id: str,
    turns_folder: Dict[str, Path],
    phrases_folder: Dict[str, Path],
    batch: int,
    ipus: List[IPU],
) -> List[TurnTransition]:
    """Load turn transitions for the given task and match them to IPUs"""
    transitions = []
    # Sort IPUs by start time for efficient lookup
    ipus = sorted(ipus, key=lambda x: x.start) if ipus else []
    if not ipus:
        return transitions

    # Create lookup dictionary for IPUs by speaker
    ipus_by_speaker = {}
    for ipu in ipus:
        if ipu.speaker not in ipus_by_speaker:
            ipus_by_speaker[ipu.speaker] = []
        ipus_by_speaker[ipu.speaker].append(ipu)

    # Process each speaker's turns file
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        turns_file_id = (
            f"s{session_id:02d}.objects.1.{speaker_suffix}.turns"
            if batch == 1
            else f"s{session_id:02d}.objects.{task_id}.turns.{speaker_suffix}.turns"
        )
        turns_file = turns_folder.get(turns_file_id)
        if not turns_file:
            logging.warning(f"Turn transitions file {turns_file_id} not found.")
            continue

        try:
            with open(turns_file, "r", encoding="utf-8") as f:
                prev_turn_ipu = None
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 3:
                        continue

                    start, end, label = parts
                    start, end = float(start), float(end)

                    # Skip silence markers
                    if label == "#":
                        continue

                    current_turn_ipu = find_nearest_ipu(
                        ipus_by_speaker.get(speaker, []), start, end
                    )

                    if current_turn_ipu:
                        if prev_turn_ipu:

                            transition = TurnTransition(
                                label=label,
                                ipu_from=prev_turn_ipu,
                                ipu_to=current_turn_ipu,
                            )
                            transitions.append(transition)
                        prev_turn_ipu = current_turn_ipu

        except Exception as e:
            logging.error(f"Error processing turns file {turns_file_id}: {e}")
            continue

    return sorted(transitions, key=lambda x: x.ipu_to.start)


def load_wavs_for_task(session_id, task_id, wav_folder, batch):
    wavs = {}
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        if batch == 1:
            wav_file_id = f"s{session_id:02d}.objects.1.{speaker_suffix}.wav"
        elif batch == 2:
            wav_file_id = f"s{session_id:02d}.objects.{task_id}.{speaker_suffix}.wav"

        if wav_folder:
            wav_file = wav_folder.get(wav_file_id)
            if not wav_file:
                logging.warning(f"WAV file {wav_file_id} not found.")
                continue
            wavs[speaker] = wav_file

    return wavs


def load_ipus_for_task(
    session_id, task_id, task_boundaries, phrases_folder, words_folder, batch
):
    if batch == 2:
        ipus = load_ipus_from_phrases(session_id, task_id, phrases_folder, batch)
    elif batch == 1:
        ipus = load_ipus_from_words(session_id, task_boundaries, words_folder)

    return ipus


def load_ipus_from_words(session_id, task_boundaries, words_folder):
    task_start = task_boundaries[0]
    task_end = task_boundaries[1]
    all_ipus = []

    for speaker in ["A", "B"]:
        words_file_id = f"s{session_id:02d}.objects.1.{speaker}.words"
        words_file = words_folder[words_file_id]

        words = []
        with open(words_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                parts = line.split(" ")
                if len(parts) == 2:
                    parts = [parts[0], parts[1], "#"]
                else:
                    parts = [x for x in parts if x.strip() != ""]

                t0, tf, text = parts
                t0 = float(t0)
                tf = float(tf)
                text = text.strip()

                if t0 > task_end:
                    break

                if tf < task_start:
                    continue

                if text.strip() == "#":
                    if words:
                        all_ipus.append(IPU(words=words))
                        words = []
                else:
                    words.append(
                        Word(
                            start=float(t0),
                            end=float(tf),
                            text=text.strip(),
                            speaker=speaker,
                        )
                    )
            if words:
                all_ipus.append(IPU(words=words))

    return all_ipus


def elipsis(text, max_length=10):
    """Truncate text to a maximum length and add ellipsis if necessary."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def get_speaker_and_suffixes(batch):
    if batch == 1:
        return [("A", "A"), ("B", "B")]
    elif batch == 2:
        return [("A", "channel1"), ("B", "channel2")]
    else:
        raise ValueError("Unknown batch number: {}".format(batch))


def load_ipus_from_phrases(session_id, task_id, phrases_folder, batch):
    all_ipus = []
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        ipus_file_id = (
            f"s{session_id:02d}.objects.1.{speaker_suffix}.phrases"
            if batch == 1
            else f"s{session_id:02d}.objects.{task_id}.{speaker_suffix}.phrases"
        )
        ipus_file = phrases_folder.get(ipus_file_id)
        if not ipus_file:
            logging.warning(f"IPUs file {ipus_file_id} not found.")
            continue

        try:
            words_by_ipu = []
            current_words = []

            with open(ipus_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    try:
                        t0, tf, text = line.split("\t")
                        if text.strip() == "#":
                            if current_words:
                                words_by_ipu.append(current_words)
                                current_words = []
                            continue

                        # Create all words for this IPU at once
                        t0, tf = float(t0), float(tf)
                        words = text.split()
                        if not words:
                            continue

                        # Distribute time evenly among words
                        word_duration = (tf - t0) / len(words)
                        current_words.extend(
                            [
                                Word(
                                    start=t0 + i * word_duration,
                                    end=t0 + (i + 1) * word_duration,
                                    text=word.strip(),
                                    speaker=speaker,
                                )
                                for i, word in enumerate(words)
                            ]
                        )

                    except ValueError as e:
                        logging.error(f"Error parsing line in {ipus_file_id}: {line}")
                        logging.error(str(e))
                        continue

            # Add any remaining words
            if current_words:
                words_by_ipu.append(current_words)

            # Create IPUs from word groups
            all_ipus.extend([IPU(words=words) for words in words_by_ipu])

        except Exception as e:
            logging.error(f"Error processing file {ipus_file_id}: {e}")
            continue

    return sorted(all_ipus, key=lambda x: x.start)
