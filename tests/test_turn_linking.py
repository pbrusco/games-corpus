"""Which IPUs belong to a turn, and which interlocutor turn a transition comes from."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from games_corpus import IPU, EnglishGamesCorpus, SlovakGamesCorpus, SpanishGamesCorpus, Turn, TurnTransition, Word
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


def test_tiny_neighbour_ipu_close_to_the_edge_is_excluded():
    # An IPU that does not intersect the turn at all must never be assigned to it, however
    # short and close it is (a padded-overlap criterion would let [1.09, 1.10] through).
    own, tiny = ipu(0.00, 1.00), ipu(1.09, 1.10)
    assert find_turn_ipus([own, tiny], 0.00, 1.00) == [own]


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


def test_simultaneous_start_at_the_edge_of_the_threshold_is_skipped():
    # A cluster of real cases sits at exactly 0.20-0.21 s, hence the 0.25 s threshold.
    assert find_interlocutor_previous_turn_id(TURNS, "A", 20.21, frozenset({"A2"})) == "A1"


def test_x3_turn_that_started_well_before_is_kept():
    # B genuinely overlaps A2 if A had been talking for a while (1.5 s here).
    assert find_interlocutor_previous_turn_id(TURNS, "A", 21.5, frozenset({"A2"})) == "A2"


def test_non_x3_turn_is_kept_even_if_it_started_just_before():
    assert find_interlocutor_previous_turn_id(TURNS, "A", 20.01) == "A2"


def test_first_turn_simultaneous_start_has_no_earlier_turn_to_fall_back_to():
    assert find_interlocutor_previous_turn_id(TURNS[1:], "A", 20.01, frozenset({"A2"})) == "A2"


# --- transition_duration clips IPU times to their turn's bounds -------------------------


@pytest.fixture
def registries():
    IPU.clear_registry()
    Turn.clear_registry()
    yield
    IPU.clear_registry()
    Turn.clear_registry()


def make_turn(speaker, turn_start, turn_end, ipu_start, ipu_end):
    ipu = IPU(words=[Word(start=ipu_start, end=ipu_end, text="x", speaker=speaker)])
    return Turn(session_id=1, task_id=1, speaker=speaker, start=turn_start, end=turn_end, ipu_ids=[ipu.ipu_id])


def transition(label, turn_from, turn_to):
    return TurnTransition(label=label, turn_id_from=turn_from.turn_id, turn_id_to=turn_to.turn_id)


def test_ipu_running_past_the_end_of_its_turn_is_clipped(registries):
    # Like the Spanish batch 2 IPU "está <missing> ah okay" [84.89, 89.07] of a turn [84.89, 85.27]
    s1 = make_turn("A", 0.0, 1.0, 0.0, 4.0)
    s2 = make_turn("B", 1.5, 2.0, 1.5, 2.0)
    tt = transition("S", s1, s2)
    assert tt.transition_duration == pytest.approx(0.5)  # unclipped: 1.5 - 4.0 = -2.5
    assert not tt.overlapped_transition


def test_ipu_starting_before_its_turn_is_clipped(registries):
    s1 = make_turn("A", 0.0, 1.0, 0.0, 1.0)
    s2 = make_turn("B", 2.0, 3.0, 0.5, 3.0)
    tt = transition("S", s1, s2)
    assert tt.transition_duration == pytest.approx(1.0)  # unclipped: 0.5 - 1.0 = -0.5
    assert not tt.overlapped_transition


def test_real_overlap_inside_the_turn_bounds_is_unchanged(registries):
    s1 = make_turn("A", 0.0, 2.0, 0.0, 2.0)
    s2 = make_turn("B", 1.5, 2.5, 1.5, 2.5)
    tt = transition("O", s1, s2)
    assert tt.transition_duration == pytest.approx(-0.5)
    assert tt.overlapped_transition


# --- real corpora ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "corpus_cls, dirname, marker, min_agreement",
    [
        (SpanishGamesCorpus, "games-spanish", "sessions-info.csv", 0.99),  # 95.6% before the fix
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
