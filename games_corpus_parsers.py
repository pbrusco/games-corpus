"""Backward compatibility shim. Import from games_corpus.parsers instead."""

from games_corpus.parsers import (  # noqa: F401
    load_objects_tasks,
    load_objects_tasks_b2,
    find_turn_ipus,
    find_interlocutor_previous_turn_id,
    load_ipus_from_phrases,
    load_wavs_for_task,
)
from games_corpus.parsers import load_ipus_from_words as _new_load_ipus_from_words
from games_corpus.parsers import load_turns_for_task as _new_load_turns_for_task
from games_corpus.parsers import load_turn_transitions_for_task  # noqa: F401


def load_tasks_info(tasks_file, batch):
    """Backward-compatible wrapper for the renamed task parsers."""
    if batch == 1:
        return load_objects_tasks(tasks_file)
    elif batch == 2:
        return load_objects_tasks_b2(tasks_file)
    else:
        raise ValueError(f"Unknown batch number: {batch}")


def _resolve_speaker_files(session_id, folder, batch, extension):
    """Helper to resolve old-style folder+batch to new-style {speaker: Path} dict."""
    suffixes = [("A", "A"), ("B", "B")] if batch == 1 else [("A", "channel1"), ("B", "channel2")]
    result = {}
    for speaker, suffix in suffixes:
        if batch == 1:
            file_id = f"s{session_id:02d}.objects.1.{suffix}.{extension}"
        else:
            file_id = f"s{session_id:02d}.objects.{session_id:02d}.{suffix}.{extension}"
        file_path = folder.get(file_id)
        if file_path:
            result[speaker] = file_path
    return result


def load_ipus_from_words(session_id, task_boundaries, words_folder):
    """Backward-compatible wrapper — resolves old-style args to new API."""
    word_files = _resolve_speaker_files(session_id, words_folder, 1, "words")
    return _new_load_ipus_from_words(word_files, task_boundaries)


def load_turns_for_task(session_id, task_id, turns_folder, batch, ipus, task_boundaries):
    """Backward-compatible wrapper — resolves old-style args to new API."""
    turn_files = _resolve_speaker_files(session_id, turns_folder, batch, "turns")
    return _new_load_turns_for_task(session_id, task_id, turn_files, ipus, task_boundaries)
