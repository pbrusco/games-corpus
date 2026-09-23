"""TurnTransitionKind: overlap-free transition types, shared by all three corpora."""

from pathlib import Path

import pytest

from games_corpus import (
    EnglishGamesCorpus,
    SlovakGamesCorpus,
    SpanishGamesCorpus,
    TurnTransitionKind,
    TurnTransitionType,
)

K, T = TurnTransitionKind, TurnTransitionType
CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"


def test_every_label_has_a_kind():
    for t in T:
        assert isinstance(t.kind, K)


def test_expected_mapping():
    expected = {
        "S": (K.YIELD, False), "O": (K.YIELD, True),
        "PI": (K.TAKE, False), "I": (K.TAKE, True),
        "BI": (K.FAILED_TAKE, True),
        "BC": (K.BACKCHANNEL, False), "BC_O": (K.BACKCHANNEL, True),
        "X2": (K.RESUME, False), "X2_O": (K.RESUME, True),
        "X1": (K.FIRST_TURN, None), "X3": (K.SIMULTANEOUS_START, None), "A": (K.AMBIGUOUS, None),
    }  # fmt: skip
    assert {t.value: (t.kind, t.annotated_overlap) for t in T} == expected


def test_round_trip_rebuilds_original_label():
    for t in T:
        assert T.from_kind(t.kind, t.annotated_overlap) is t


def test_every_kind_is_reachable():
    assert {t.kind for t in T} == set(K)


def test_butt_in_only_exists_with_overlap():
    with pytest.raises(ValueError):
        T.from_kind(K.FAILED_TAKE, False)


def test_kind_values_never_reuse_an_original_label_code():
    # e.g. a "take" is PI or I; reusing "I" for it would silently change its meaning
    assert not {k.value.upper() for k in K} & {t.value for t in T}


@pytest.mark.parametrize(
    "corpus_cls, dirname, marker",
    [
        (SpanishGamesCorpus, "games-spanish", "sessions-info.csv"),
        (EnglishGamesCorpus, "games-english", "README.sessions-info"),
        (SlovakGamesCorpus, "games-slovak", "documents/sessions_info.txt"),
    ],
)
def test_real_transitions_round_trip(corpus_cls, dirname, marker):
    path = CORPUS_DIR / dirname
    if not (path / marker).exists():
        pytest.skip(f"{dirname} not available locally")
    corpus = corpus_cls()
    corpus.load(local_path=str(path), load_audio=False)
    transitions = [tt for s in corpus.sessions.values() for task in s.tasks for tt in task.turn_transitions]
    assert transitions
    for tt in transitions:
        assert tt.kind is tt.label_type.kind
        assert tt.annotated_overlap is tt.label_type.annotated_overlap
        assert T.from_kind(tt.kind, tt.annotated_overlap) is tt.label_type
