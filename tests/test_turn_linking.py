"""Which IPUs belong to a turn, and which interlocutor turn a transition comes from."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from games_corpus import EnglishGamesCorpus, SlovakGamesCorpus, SpanishGamesCorpus
from games_corpus.parsers import find_interlocutor_previous_turn_id, find_turn_ipus

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"


def ipu(start, end):
    return SimpleNamespace(start=start, end=end)


def turn(turn_id, speaker, start):
    return SimpleNamespace(turn_id=turn_id, speaker=speaker, start=start)


# --- find_turn_ipus ------------------------------------------------------------------


def test_neighbour_ipu_starting_just_after_the_turn_is_excluded():
    # Real case (Spanish s1/t12): turn [664.37-665.40]; the speaker's next IPU starts at
    # 665.49, 90 ms after the turn ends. It used to be counted as this turn's last IPU.
    own, neighbour = ipu(664.37, 665.40), ipu(665.49, 665.94)
    assert find_turn_ipus([own, neighbour], 664.37, 665.40) == [own]


def test_neighbour_ipu_ending_just_before_the_turn_is_excluded():
    previous, own = ipu(578.18, 579.82), ipu(579.88, 581.44)
    assert find_turn_ipus([previous, own], 579.88, 581.44) == [own]


def test_ipu_spilling_slightly_over_the_turn_edge_is_kept():
    spill = ipu(10.00, 12.25)  # rounding mismatch between the turn and IPU files
    assert find_turn_ipus([spill], 10.05, 12.00) == [spill]


def test_turn_shorter_than_its_single_ipu_keeps_it():
    # Some turns are shorter than their only IPU (file mismatch); they must not lose it.
    long_ipu = ipu(84.89, 89.07)
    assert find_turn_ipus([long_ipu], 84.89, 85.27) == [long_ipu]


# --- find_interlocutor_previous_turn_id ------------------------------------------------


TURNS = [turn("A1", "A", 10.0), turn("A2", "A", 20.00)]


def test_simultaneous_start_is_skipped_for_the_previous_turn():
    # A started A2 (annotated X3) 10 ms before B's turn: B responds to A1.
    assert find_interlocutor_previous_turn_id(TURNS, "A", 20.01, frozenset({"A2"})) == "A1"


def test_x3_turn_that_started_well_before_is_kept():
    # B genuinely overlaps A2 if A had been talking for a while (1.5 s here).
    assert find_interlocutor_previous_turn_id(TURNS, "A", 21.5, frozenset({"A2"})) == "A2"


def test_non_x3_turn_is_kept_even_if_it_started_just_before():
    assert find_interlocutor_previous_turn_id(TURNS, "A", 20.01) == "A2"


def test_first_turn_simultaneous_start_has_no_earlier_turn_to_fall_back_to():
    assert find_interlocutor_previous_turn_id(TURNS[1:], "A", 20.01, frozenset({"A2"})) == "A2"


# --- real corpora ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "corpus_cls, dirname, marker, min_agreement",
    [
        (SpanishGamesCorpus, "games-spanish", "sessions-info.csv", 0.985),  # 95.6% before the fix
        (EnglishGamesCorpus, "games-english", "README.sessions-info", 0.995),  # 95.1% before
        (SlovakGamesCorpus, "games-slovak", "documents/sessions_info.txt", 0.995),  # 96.5% before
    ],
)
def test_timestamp_overlap_agrees_with_annotation(corpus_cls, dirname, marker, min_agreement):
    path = CORPUS_DIR / dirname
    if not (path / marker).exists():
        pytest.skip(f"{dirname} not available locally")
    corpus = corpus_cls()
    corpus.load(local_path=str(path), load_audio=False)
    transitions = [
        tt
        for s in corpus.sessions.values()
        for task in s.tasks
        for tt in task.turn_transitions
        if tt.turn_from is not None and tt.annotated_overlap is not None
    ]
    agreement = sum(tt.overlapped_transition == tt.annotated_overlap for tt in transitions) / len(transitions)
    assert agreement >= min_agreement
