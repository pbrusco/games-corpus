"""Parsing functions for the Games Corpus.

All parsers accept resolved file paths — the corpus classes are responsible
for mapping (session, task, speaker) to file paths.
"""

import logging
from pathlib import Path
from typing import Any

from games_corpus.types import Task, TurnTransition, Turn, IPU, Word, TurnTransitionType


# ---------------------------------------------------------------------------
# Task info parsers
# ---------------------------------------------------------------------------


def load_objects_tasks(tasks_file: str | Path) -> list[dict[str, Any]]:
    """Parse tasks file in the objects format: START END LABEL (semicolon fields).

    Works for Spanish B1, English, and Slovak objects games.
    Fields are parsed by name (key:value), not by position.
    """
    tasks_info: list[dict[str, Any]] = []

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


def load_objects_tasks_b2(tasks_file: str | Path) -> list[dict[str, Any]]:
    """Parse tasks file in the Spanish B2 format: TASK_ID LABEL (semicolon fields)."""
    tasks_info: list[dict[str, Any]] = []

    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            raw_task_id, task_info_str = line.split(" ", 1)
            task_id = int(raw_task_id)
            raw_images, raw_describer, raw_target, raw_score, raw_time_used = task_info_str.split(";")
            start = 0.0
            time_used = float(raw_time_used.split(":")[-1].strip())
            end = time_used

            images = raw_images.split(",")
            describer = raw_describer.split(":")[-1].strip()
            target = raw_target.split(":")[-1].strip()
            score = raw_score.split(":")[-1].strip()
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


def find_turn_ipus(speaker_ipus: list[IPU], turn_start: float, turn_end: float, max_diff: float = 0.1) -> list[IPU]:
    """IPUs that substantially overlap the turn: the shared time covers at least half of the
    IPU or half of the turn. max_diff widens the turn to absorb rounding differences between
    the turn and IPU files.

    Earlier versions took any IPU whose start OR end fell within max_diff of the turn, so an
    IPU of the speaker's next turn starting a few ms after this turn ended was counted in
    both turns (shifting ipu_from/ipu_to and the overlap computed from them). Requiring real
    overlap drops those, while keeping IPUs that spill over the turn's edge and the few turns
    that are shorter than their single IPU (a mismatch between the two files)."""
    lo, hi = turn_start - max_diff, turn_end + max_diff
    turn_dur = hi - lo
    selected = []
    for ipu in speaker_ipus:
        shared = min(hi, ipu.end) - max(lo, ipu.start)
        if shared > 0 and (shared >= 0.5 * (ipu.end - ipu.start) or shared >= 0.5 * turn_dur):
            selected.append(ipu)
    return selected


# A turn annotated as a simultaneous start (X3) that began less than this many seconds
# before the interlocutor's turn is not what the interlocutor is responding to: both
# speakers started at (almost) the same time, and the annotators label the interlocutor's
# transition against the speaker's *previous* turn. Across the three corpora, 98% of such
# cases are annotated without overlap, while X3 turns the interlocutor genuinely overlaps
# started ~1-2s earlier (median).
SIMULTANEOUS_START_MAX_LEAD = 0.2


def find_interlocutor_previous_turn_id(
    turns: list[Turn],
    speaker: str,
    starting_before: float | None = None,
    simultaneous_start_ids: frozenset[str] = frozenset(),
) -> str | None:
    """The interlocutor turn a transition comes from: the most recent turn of `speaker`
    starting at or before `starting_before`, skipping a simultaneous start (a turn in
    `simultaneous_start_ids`, i.e. annotated X3, that began less than
    SIMULTANEOUS_START_MAX_LEAD earlier) in favour of the turn before it."""
    if not turns or starting_before is None:
        return None
    candidates = [turn for turn in turns if turn.start <= starting_before and turn.speaker == speaker]
    if not candidates:
        return None
    last = candidates[-1]
    if (
        last.turn_id in simultaneous_start_ids
        and starting_before - last.start < SIMULTANEOUS_START_MAX_LEAD
        and len(candidates) > 1
    ):
        return candidates[-2].turn_id
    return last.turn_id


# ---------------------------------------------------------------------------
# Turns loader
# ---------------------------------------------------------------------------


def load_turns_for_task(
    session_id: int,
    task_id: int,
    turn_files: dict[str, Path],
    ipus: list[IPU],
    task_boundaries: tuple[Any, ...],
) -> list[Turn]:
    """Load turns from per-speaker turn files.

    Args:
        session_id: Session identifier
        task_id: Task identifier
        turn_files: mapping of speaker ("A"/"B") -> resolved file path
        ipus: Loaded IPUs for this task
        task_boundaries: tuple containing (start, end, ...)
    """
    turns: list[Turn] = []

    ipus = sorted(ipus, key=lambda x: x.start) if ipus else []
    if not ipus:
        return turns

    task_start = task_boundaries[0]
    task_end = task_boundaries[1]

    ipus_by_speaker: dict[str, list[IPU]] = {}
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

                raw_start, raw_end, label = parts
                turn_start, turn_end = float(raw_start), float(raw_end)

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
    turn_files: dict[str, Path],
    turns: list[Turn],
    task_boundaries: tuple[Any, ...],
) -> list[TurnTransition]:
    """Load turn transitions from per-speaker turn files.

    Args:
        session_id: Session identifier
        task_id: Task identifier
        turn_files: mapping of speaker ("A"/"B") -> resolved file path
        turns: Loaded Turn objects for this task
        task_boundaries: tuple containing (start, end, ...)
    """
    transitions: list[TurnTransition] = []
    if not turns:
        return transitions

    task_start = task_boundaries[0]
    task_end = task_boundaries[1]

    entries: list[tuple[str, str, float, float, str]] = []  # (speaker, line, start, end, label)
    for speaker, turns_file in turn_files.items():
        if not Path(turns_file).exists():
            logging.warning(f"Turn transitions file {turns_file} not found.")
            continue

        with open(turns_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue

                raw_start, raw_end, label = parts
                turn_start, turn_end = float(raw_start), float(raw_end)

                if turn_start > task_end:
                    break
                if turn_end < task_start:
                    continue
                entries.append((speaker, line, turn_start, turn_end, label))

    # Turns annotated as simultaneous starts, needed before linking either speaker's transitions
    simultaneous_start_ids = frozenset(
        Turn.id_builder(session_id, task_id, speaker, start, end)
        for speaker, _, start, end, label in entries
        if label == TurnTransitionType.SIMULTANEOUS_START.value
    )

    for speaker, line, turn_start, turn_end, label in entries:
        if speaker not in ("A", "B"):
            logging.warning(f"Unexpected speaker '{speaker}', skipping transition")
            continue
        interlocutor = "B" if speaker == "A" else "A"

        if label == "#":
            continue
        if label in ["L", "L-SIM", "N", "N-SIM", "A", "?"]:
            logging.debug("Skipping undefined turn transitions")
            continue

        if label in (TurnTransitionType.SIMULTANEOUS_START.value, TurnTransitionType.FIRST_TURN.value):
            prev_turn_id = None
        else:
            prev_turn_id = find_interlocutor_previous_turn_id(
                turns,
                speaker=interlocutor,
                starting_before=turn_start,
                simultaneous_start_ids=simultaneous_start_ids,
            )
            if not prev_turn_id:
                logging.warning(f"Could not find matching previous turn for: {line.strip()=}. Skipping Transition")
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
    word_files: dict[str, Path],
    task_boundaries: tuple[Any, ...],
) -> list[IPU]:
    """Load IPUs by parsing word-level files.

    Args:
        word_files: mapping of speaker ("A"/"B") -> resolved .words file path
        task_boundaries: (task_start, task_end, ...)
    """
    task_start = task_boundaries[0]
    task_end = task_boundaries[1]
    all_ipus: list[IPU] = []

    for speaker, words_file in word_files.items():
        words: list[Word] = []
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
    phrase_files: dict[str, Path],
    task_boundaries: tuple[Any, ...] | None = None,
) -> list[IPU]:
    """Load IPUs by parsing phrase-level files.

    Handles both tab-delimited (Spanish B2) and space-delimited (Slovak .Phrases) formats.
    Recognizes both '#' and 'xxx' as silence markers.

    Args:
        phrase_files: mapping of speaker ("A"/"B") -> resolved .phrases file path
        task_boundaries: optional (task_start, task_end, ...) to filter by time range
    """
    task_start = task_boundaries[0] if task_boundaries else None
    task_end = task_boundaries[1] if task_boundaries else None
    all_ipus: list[IPU] = []

    for speaker, ipus_file in phrase_files.items():
        if not Path(ipus_file).exists():
            logging.warning(f"Phrases file {ipus_file} not found.")
            continue

        try:
            words_by_ipu: list[list[Word]] = []
            current_words: list[Word] = []

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


def load_wavs_for_task(wav_files: dict[str, Path]) -> dict[str, Path]:
    """Return validated wav file paths.

    Args:
        wav_files: mapping of speaker ("A"/"B") -> resolved .wav file path
    """
    result: dict[str, Path] = {}
    for speaker, wav_file in wav_files.items():
        if Path(wav_file).exists():
            result[speaker] = Path(wav_file)
        else:
            logging.warning(f"WAV file {wav_file} not found.")
    return result


# ---------------------------------------------------------------------------
# Shared task builder
# ---------------------------------------------------------------------------


def build_tasks_from_files(
    session_id: int,
    tasks_info: list[dict[str, Any]],
    word_files: dict[str, Path],
    turn_files: dict[str, Path],
    phrase_files: dict[str, Path],
    wav_files: dict[str, Path],
    load_audio: bool,
) -> list[Task]:
    """Build Task objects from parsed task info and resolved file paths.

    Shared logic used by English and Slovak corpus classes.
    """
    tasks: list[Task] = []
    task_wavs = load_wavs_for_task(wav_files) if load_audio else {}

    for info in tasks_info:
        task_id = int(info["Task ID"])
        task_boundaries = (info["Start"], info["End"], task_id, session_id)

        if word_files:
            ipus = load_ipus_from_words(word_files, task_boundaries)
        elif phrase_files:
            ipus = load_ipus_from_phrases(phrase_files, task_boundaries)
        else:
            ipus = []

        turns = load_turns_for_task(session_id, task_id, turn_files, ipus, task_boundaries)
        turn_transitions = load_turn_transitions_for_task(session_id, task_id, turn_files, turns, task_boundaries)

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
            wavs=task_wavs,
            turns=turns,
        )
        tasks.append(task_obj)

    return tasks
