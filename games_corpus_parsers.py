"""Parsing functions for the Games Corpus."""

import logging
from pathlib import Path
from typing import List, Dict
from games_corpus_types import TurnTransition, Turn, IPU, Word, TurnTransitionType


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
                task_id = len(tasks_info) + 1
                time_used = float(time_used.split(":")[-1].strip())

            elif batch == 2:
                task_id, task_info = line.split(" ", 1)
                task_id = int(task_id)
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


def find_interlocutor_previous_turn_id(turns, speaker, starting_before=None):
    """Find the most recent turn before the given timestamp"""
    if not turns:
        return None

    for turn in reversed(turns):
        if turn.start <= starting_before and turn.speaker == speaker:
            return turn.turn_id

    return None


def find_turn_ipus(speaker_ipus, turn_start, turn_end, max_diff=0.1):
    """
    Find IPUs that fall within the given turn boundaries.

    An IPU is considered to fall within the boundaries if its start time is
    greater than or equal to (turn_start - max_diff) and its end time is
    less than or equal to (turn_end + max_diff). IPUs that partially overlap
    with the boundaries but do not meet these conditions are excluded.
    """
    turn_ipus = [
        ipu
        for ipu in speaker_ipus
        if (turn_start - max_diff) <= ipu.start <= (turn_end + max_diff)
        or (turn_start - max_diff) <= ipu.end <= (turn_end + max_diff)
    ]
    return turn_ipus


def get_speaker_and_suffixes(batch):
    if batch == 1:
        return [("A", "A"), ("B", "B")]
    elif batch == 2:
        return [("A", "channel1"), ("B", "channel2")]
    else:
        raise ValueError("Unknown batch number: {}".format(batch))


def load_turns_for_task(
    session_id: int,
    task_id: int,
    turns_folder: Dict[str, Path],
    batch: int,
    ipus: List[IPU],
    task_boundaries: tuple[int, int, int, int],
) -> List[TurnTransition]:
    turns = []

    # Sort IPUs by start time for efficient lookup
    ipus = sorted(ipus, key=lambda x: x.start) if ipus else []
    if not ipus:
        return turns

    task_start = task_boundaries[0]
    task_end = task_boundaries[1]

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
            else f"s{session_id:02d}.objects.{task_id:02d}.{speaker_suffix}.turns"
        )
        turns_file = turns_folder.get(turns_file_id)
        if not turns_file:
            logging.warning(f"Turn file {turns_file_id} not found.")
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

                # Skip silence markers
                if label == "#":
                    continue

                turn_ipus = find_turn_ipus(
                    ipus_by_speaker[speaker], turn_start, turn_end, max_diff=0.1
                )
                turn_id = Turn.id_builder(
                    session_id, task_id, speaker, turn_start, turn_end
                )
                if len(turn_ipus) == 0:
                    logging.warning(
                        f"Cannot find IPUs for turn {turn_id}. Skipping turn"
                    )
                    continue

                turn = Turn(
                    ipu_ids=[
                        ipu.ipu_id for ipu in turn_ipus
                    ],  # Changed from ipus to ipu_ids
                    speaker=speaker,
                    session_id=session_id,
                    task_id=task_id,
                    start=turn_start,
                    end=turn_end,
                )
                turns.append(turn)

    return sorted(turns, key=lambda x: x.start)


def load_turn_transitions_for_task(
    session_id: int,
    task_id: int,
    turns_folder: Dict[str, Path],
    batch: int,
    turns: List[IPU],
    task_boundaries: tuple[int, int, int, int],
) -> List[TurnTransition]:
    transitions = []

    # Sort IPUs by start time for efficient lookup
    if not turns:
        return transitions

    task_start = task_boundaries[0]
    task_end = task_boundaries[1]

    # Process each speaker's turns file
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        turns_file_id = (
            f"s{session_id:02d}.objects.1.{speaker_suffix}.turns"
            if batch == 1
            else f"s{session_id:02d}.objects.{task_id:02d}.{speaker_suffix}.turns"
        )
        turns_file = turns_folder.get(turns_file_id)
        if not turns_file:
            logging.warning(f"Turn transitions file {turns_file_id} not found.")
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

                # Skip silence markers
                if label == "#":
                    continue

                if label in ["L", "L-SIM", "N", "N-SIM", "A"]:
                    logging.debug("Skipping undefined turn transitions")
                    continue

                if (
                    label == TurnTransitionType.SIMULTANEOUS_START.value
                    or label == TurnTransitionType.FIRST_TURN.value
                ):
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

                turn_id = Turn.id_builder(
                    session_id, task_id, speaker, turn_start, turn_end
                )

                if turn_id not in Turn._all_turns:
                    logging.warning(
                        f"Turn ID {turn_id} not found in loaded turns. Skipping transition."
                    )
                    continue

                transition = TurnTransition(
                    label=label,
                    turn_id_from=prev_turn_id,
                    turn_id_to=turn_id,
                )
                transitions.append(transition)

    return sorted(transitions, key=lambda x: x.ipu_to.start)


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


def load_ipus_from_phrases(session_id, task_id, phrases_folder, batch):
    all_ipus = []
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        ipus_file_id = (
            f"s{session_id:02d}.objects.1.{speaker_suffix}.phrases"
            if batch == 1
            else f"s{session_id:02d}.objects.{task_id:02d}.{speaker_suffix}.phrases"
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
                        words = text.replace("#", "").split()
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


def load_wavs_for_task(session_id, task_id, wav_folder, batch):
    wavs = {}
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        if batch == 1:
            wav_file_id = f"s{session_id:02d}.objects.1.{speaker_suffix}.wav"
        elif batch == 2:
            wav_file_id = (
                f"s{session_id:02d}.objects.{task_id:02d}.{speaker_suffix}.wav"
            )

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
