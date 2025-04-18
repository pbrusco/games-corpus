# tests/test_task_boundaries.py
import math
import sys
from pathlib import Path

import pytest

# ----------------------------------------------------------------------
# 1) importa la librería y los parsers de la tool
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
GAMES_CORPUS_PATH = REPO_ROOT / "games-corpus"

if str(GAMES_CORPUS_PATH) not in sys.path:
    sys.path.append(str(GAMES_CORPUS_PATH))

from games_corpus import SpanishGamesCorpusDialogues
from games_corpus_parsers import (
    load_tasks_info,
    load_ipus_from_words,
    load_turns_for_task,
)

# ----------------------------------------------------------------------
# 2) constantes de la prueba
# ----------------------------------------------------------------------
SESSION_ID = 3
TASK_ID = 2
EXPECTED_START = 34.949000
FIRST_TURN_B = (37.900195, 41.897241)  # (start, end)

CORPUS_ROOT = REPO_ROOT / "uba_games_corpus"

# ----------------------------------------------------------------------
# 3) fixture corpus
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def corpus():
    c = SpanishGamesCorpusDialogues()
    c.load(load_audio=False, local_path=str(CORPUS_ROOT))
    return c


# ----------------------------------------------------------------------
# 4) tests
# ----------------------------------------------------------------------
def test_raw_task_start_matches_expected(corpus):
    """Lee el fichero .tasks crudo y comprueba que el start es 34.949."""
    tasks_mapping = corpus.corpus_raw["b1-dialogue-tasks"]

    # El nombre puede ser s03... o s3...  ⇒ buscamos el que exista.
    key_with_zero = f"s{SESSION_ID:02d}.objects.1.tasks"
    key_no_zero = f"s{SESSION_ID}.objects.1.tasks"

    if key_with_zero in tasks_mapping:
        tasks_file = tasks_mapping[key_with_zero]
    elif key_no_zero in tasks_mapping:
        tasks_file = tasks_mapping[key_no_zero]
    else:
        pytest.skip(f"No se encontró el .tasks de la sesión {SESSION_ID}")

    tasks_info = load_tasks_info(tasks_file, batch=1)
    raw_start = next(t["Start"] for t in tasks_info if t["Task ID"] == TASK_ID)

    assert math.isclose(
        raw_start, EXPECTED_START, abs_tol=1e-6
    ), "El .tasks crudo no coincide con el valor esperado."


def test_task_object_preserves_start(corpus):
    """El Task cargado por la tool debe conservar el mismo start."""
    task = next(t for t in corpus.sessions[SESSION_ID].tasks if t.task_id == TASK_ID)

    assert math.isclose(
        task.start, EXPECTED_START, abs_tol=1e-6
    ), (
        f"Task.start se modificó ({task.start}) y ya no coincide con el "
        "valor del fichero .tasks (34.949)."
    )


def test_first_turn_of_B_is_present(corpus):
    """
    El primer turno de B (37.900‑41.897 s) debería estar incluido en los
    turnos que la tool devuelve para S3‑T2.
    """
    task = next(t for t in corpus.sessions[SESSION_ID].tasks if t.task_id == TASK_ID)
    task_end = task.start + task.duration

    words_folder = corpus.corpus_raw["b1-dialogue-words"]
    turns_folder = corpus.corpus_raw["b1-dialogue-turns"]

    # IPUs extraídas con la propia función de la tool
    ipus = load_ipus_from_words(
        SESSION_ID, (task.start, task_end), words_folder
    )

    turns_B = load_turns_for_task(
        SESSION_ID,
        TASK_ID,
        turns_folder=turns_folder,
        batch=1,
        ipus=ipus,
        task_boundaries=(task.start, task_end, None, None),
    )

    found = any(
        turn.speaker == "B"
        and math.isclose(turn.start, FIRST_TURN_B[0], abs_tol=1e-6)
        and math.isclose(turn.end, FIRST_TURN_B[1], abs_tol=1e-6)
        for turn in turns_B
    )

    assert (
        found
    ), "El primer turno de B (37.900‑41.897 s) debería estar incluido y no lo está."
