"""Parsing functions for the Games Corpus.

All parsers accept resolved file paths — the corpus classes are responsible
for mapping (session, task, speaker) to file paths.
"""

import logging
from pathlib import Path
from typing import List, Dict

from games_corpus.types import TurnTransition, Turn, IPU, Word, TurnTransitionType


# ---------------------------------------------------------------------------
# Task info parsers
# ---------------------------------------------------------------------------


def load_objects_tasks(tasks_file) -> list:
    """Parse tasks file in the objects format: START END LABEL (semicolon fields).

    Works for Spanish B1, English, and Slovak objects games.
    Fields are parsed by name (key:value), not by position.
    """
    tasks_info = []

    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            task_info = line.split(";")
            if len(task_info) < 3:
                continue

            start_end_images = task_info[0]
            parts = start_end_images.split()
            if len(parts) < 3:
                continue

            start = float(parts[0])
            end = float(parts[1])
            rest = " ".join(parts[2:])

            # Skip non-task lines (comments, talking-to-confederate, practice, etc.)
            if not rest.startswith("Images:"):
                continue

            # Parse all key:value fields by name
            fields = {}
            fields["Images"] = rest.split("Images:")[-1]
            for field in task_info[1:]:
                if ":" in field:
                    key, value = field.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Handle duplicate keys (e.g. Slovak has Describer twice) — keep first
                    if key not in fields:
                        fields[key] = value

            task_id = len(tasks_info) + 1
            images = fields["Images"].split(",")
            tasks_info.append(
                {
                    "Task ID": task_id,
                    "Start": start,
                    "End": end,
                    "Images": images,
                    "Describer": fields.get("Describer", ""),
                    "Target": fields.get("Target", ""),
                    "Score": fields.get("Score", "0"),
                    "Time-used": float(fields.get("Time-used", "0")),
                }
            )

    return tasks_info


def load_objects_tasks_b2(tasks_file) -> list:
    """Parse tasks file in the Spanish B2 format: TASK_ID LABEL (semicolon fields)."""
    tasks_info = []

    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            task_id, task_info_str = line.split(" ", 1)
            task_id = int(task_id)
            images, describer, target, score, time_used = task_info_str.split(";")
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


# ---------------------------------------------------------------------------
# IPU helpers
# ---------------------------------------------------------------------------


def find_turn_ipus(speaker_ipus, turn_start, turn_end, max_diff=0.1):
    """Find IPUs that fall within the given turn boundaries."""
    return [
        ipu
        for ipu in speaker_ipus
        if (turn_start - max_diff) <= ipu.start <= (turn_end + max_diff)
        or (turn_start - max_diff) <= ipu.end <= (turn_end + max_diff)
    ]


def find_interlocutor_previous_turn_id(turns, speaker, starting_before=None):
    """Find the most recent turn before the given timestamp."""
    if not turns:
        return None
    for turn in reversed(turns):
        if turn.start <= starting_before and turn.speaker == speaker:
            return turn.turn_id
    return None


# ---------------------------------------------------------------------------
# Turns loader
# ---------------------------------------------------------------------------


def load_turns_for_task(
    session_id: int,
    task_id: int,
    turn_files: Dict[str, Path],
    ipus: List[IPU],
    task_boundaries: tuple,
) -> List[Turn]:
    """Load turns from per-speaker turn files.

    Args:
        turn_files: mapping of speaker ("A"/"B") -> resolved file path
    """
    turns = []

    ipus = sorted(ipus, key=lambda x: x.start) if ipus else []
    if not ipus:
        return turns

    task_start = task_boundaries[0]
    task_end = task_boundaries[1]

    ipus_by_speaker = {}
    for ipu in ipus:
        if ipu.speaker not in ipus_by_speaker:
            ipus_by_speaker[ipu.speaker] = []
        ipus_by_speaker[ipu.speaker].append(ipu)

    for speaker, turns_file in turn_files.items():
        if not Path(turns_file).exists():
            logging.warning(f"Turn file {turns_file} not found.")
            continue

        with open(turns_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue

                turn_start, turn_end, label = parts
                turn_start, turn_end = float(turn_start), float(turn_end)

                if turn_start > task_end:
                    break
                if turn_end < task_start:
                    continue
                if label == "#":
                    continue

                speaker_ipus = ipus_by_speaker.get(speaker, [])
                turn_ipus = find_turn_ipus(speaker_ipus, turn_start, turn_end, max_diff=0.1)
                turn_id = Turn.id_builder(session_id, task_id, speaker, turn_start, turn_end)
                if len(turn_ipus) == 0:
                    logging.warning(f"Cannot find IPUs for turn {turn_id}. Skipping turn")
                    continue

                turn = Turn(
                    ipu_ids=[ipu.ipu_id for ipu in turn_ipus],
                    speaker=speaker,
                    session_id=session_id,
                    task_id=task_id,
                    start=turn_start,
                    end=turn_end,
                )
                turns.append(turn)

    return sorted(turns, key=lambda x: x.start)


# ---------------------------------------------------------------------------
# Turn transitions loader
# ---------------------------------------------------------------------------


def load_turn_transitions_for_task(
    session_id: int,
    task_id: int,
    turn_files: Dict[str, Path],
    turns: List[Turn],
    task_boundaries: tuple,
) -> List[TurnTransition]:
    """Load turn transitions from per-speaker turn files.

    Args:
        turn_files: mapping of speaker ("A"/"B") -> resolved file path
    """
    transitions = []
    if not turns:
        return transitions

    task_start = task_boundaries[0]
    task_end = task_boundaries[1]

    for speaker, turns_file in turn_files.items():
        if not Path(turns_file).exists():
            logging.warning(f"Turn transitions file {turns_file} not found.")
            continue

        with open(turns_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue

                turn_start, turn_end, label = parts
                turn_start, turn_end = float(turn_start), float(turn_end)

                if turn_start > task_end:
                    break
                if turn_end < task_start:
                    continue

                assert speaker in ["A", "B"]
                interlocutor = "B" if speaker == "A" else "A"

                if label == "#":
                    continue
                if label in ["L", "L-SIM", "N", "N-SIM", "A", "?"]:
                    logging.debug("Skipping undefined turn transitions")
                    continue

                if label == TurnTransitionType.SIMULTANEOUS_START.value or label == TurnTransitionType.FIRST_TURN.value:
                    prev_turn_id = None
                else:
                    prev_turn_id = find_interlocutor_previous_turn_id(
                        turns,
                        speaker=interlocutor,
                        starting_before=turn_start,
                    )
                    if not prev_turn_id:
                        logging.warning(
                            f"Could not find matching previous turn for: {line.strip()=}. Skipping Transition"
                        )
                        continue

                turn_id = Turn.id_builder(session_id, task_id, speaker, turn_start, turn_end)

                if turn_id not in Turn._all_turns:
                    logging.warning(f"Turn ID {turn_id} not found in loaded turns. Skipping transition.")
                    continue

                transition = TurnTransition(
                    label=label,
                    turn_id_from=prev_turn_id,
                    turn_id_to=turn_id,
                )
                transitions.append(transition)

    return sorted(transitions, key=lambda x: x.ipu_to.start)


# ---------------------------------------------------------------------------
# IPU loaders
# ---------------------------------------------------------------------------


def load_ipus_from_words(
    word_files: Dict[str, Path],
    task_boundaries: tuple,
) -> List[IPU]:
    """Load IPUs by parsing word-level files.

    Args:
        word_files: mapping of speaker ("A"/"B") -> resolved .words file path
        task_boundaries: (task_start, task_end, ...)
    """
    task_start = task_boundaries[0]
    task_end = task_boundaries[1]
    all_ipus = []

    for speaker, words_file in word_files.items():
        words = []
        with open(words_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Auto-detect delimiter: tab or space
                if "\t" in line:
                    parts = line.split("\t")
                else:
                    parts = line.split(" ")
                    if len(parts) == 2:
                        parts = [parts[0], parts[1], "#"]
                    else:
                        parts = [x for x in parts if x.strip() != ""]

                if len(parts) < 2:
                    continue

                t0 = float(parts[0])
                tf = float(parts[1])
                text = parts[2].strip() if len(parts) > 2 else "#"

                if t0 > task_end:
                    break
                if tf < task_start:
                    continue

                if text == "#":
                    if words:
                        all_ipus.append(IPU(words=words))
                        words = []
                else:
                    words.append(
                        Word(
                            start=t0,
                            end=tf,
                            text=text,
                            speaker=speaker,
                        )
                    )
            if words:
                all_ipus.append(IPU(words=words))

    return all_ipus


def load_ipus_from_phrases(
    phrase_files: Dict[str, Path],
    task_boundaries: tuple = None,
) -> List[IPU]:
    """Load IPUs by parsing phrase-level files.

    Handles both tab-delimited (Spanish B2) and space-delimited (Slovak .Phrases) formats.
    Recognizes both '#' and 'xxx' as silence markers.

    Args:
        phrase_files: mapping of speaker ("A"/"B") -> resolved .phrases file path
        task_boundaries: optional (task_start, task_end, ...) to filter by time range
    """
    task_start = task_boundaries[0] if task_boundaries else None
    task_end = task_boundaries[1] if task_boundaries else None
    all_ipus = []

    for speaker, ipus_file in phrase_files.items():
        if not Path(ipus_file).exists():
            logging.warning(f"Phrases file {ipus_file} not found.")
            continue

        try:
            words_by_ipu = []
            current_words = []

            with open(ipus_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        # Auto-detect delimiter: tab or space
                        if "\t" in line:
                            parts = line.split("\t", 2)
                        else:
                            parts = line.split(None, 2)

                        if len(parts) < 2:
                            continue

                        t0, tf = float(parts[0]), float(parts[1])
                        text = parts[2].strip() if len(parts) > 2 else ""

                        if task_end is not None and t0 > task_end:
                            break
                        if task_start is not None and tf < task_start:
                            continue

                        # Silence markers: '#' or 'xxx' or empty
                        if text in ("#", "xxx", ""):
                            if current_words:
                                words_by_ipu.append(current_words)
                                current_words = []
                            continue

                        words = text.replace("#", "").split()
                        if not words:
                            continue

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
                        logging.error(f"Error parsing line in {ipus_file}: {line}")
                        logging.error(str(e))
                        continue

            if current_words:
                words_by_ipu.append(current_words)

            all_ipus.extend([IPU(words=words) for words in words_by_ipu])

        except Exception as e:
            logging.error(f"Error processing file {ipus_file}: {e}")
            continue

    return sorted(all_ipus, key=lambda x: x.start)


# ---------------------------------------------------------------------------
# WAV loader
# ---------------------------------------------------------------------------


def load_wavs_for_task(wav_files: Dict[str, Path]) -> Dict[str, Path]:
    """Return validated wav file paths.

    Args:
        wav_files: mapping of speaker ("A"/"B") -> resolved .wav file path
    """
    result = {}
    for speaker, wav_file in wav_files.items():
        if Path(wav_file).exists():
            result[speaker] = wav_file
        else:
            logging.warning(f"WAV file {wav_file} not found.")
    return result
