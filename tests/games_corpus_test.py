import sys
from pathlib import Path
import math

REPO_ROOT = Path(__file__).resolve().parents[2]
GAMES_CORPUS_PATH = REPO_ROOT / "games-corpus"

if str(GAMES_CORPUS_PATH) not in sys.path:
    sys.path.append(str(GAMES_CORPUS_PATH))

import pytest
from games_corpus import (
    SpanishGamesCorpusDialogues,
    Task,
    Session,
)
from games_corpus_types import (
    Word,
    IPU,
    TurnTransition,
    Turn,
    TurnTransitionType,
)

from games_corpus_parsers import load_tasks_info, load_ipus_from_words, load_turns_for_task


@pytest.fixture
def sample_task_file(tmp_path):
    task_file = tmp_path / "sample_tasks.txt"
    content = """0.0 10.0 Images:img1,img2;Describer:A;Target:img1;Score:1.0;Time-used:10.0
10.0 20.0 Images:img3,img4;Describer:B;Target:img3;Score:0.5;Time-used:10.0"""
    task_file.write_text(content)
    return task_file


@pytest.fixture
def sample_words():
    return [
        Word(start=0.0, end=1.0, text="hello", speaker="A"),
        Word(start=1.0, end=2.0, text="world", speaker="A"),
    ]


@pytest.fixture
def sample_ipu(sample_words):
    return IPU(words=sample_words)


@pytest.fixture
def sample_ipus():
    return [
        IPU(words=[Word(start=0.0, end=1.0, text="hello", speaker="A")]),
        IPU(words=[Word(start=2.0, end=3.0, text="world", speaker="B")]),
    ]


@pytest.fixture
def sample_turns(sample_ipus):
    return [
        Turn(
            session_id=1,
            task_id=1,
            ipu_ids=[sample_ipus[0].ipu_id],
            speaker="A",
            start=0.0,
            end=1.0,
        ),
        Turn(
            session_id=1,
            task_id=1,
            ipu_ids=[sample_ipus[1].ipu_id],
            speaker="B",
            start=2.0,
            end=3.0,
        ),
    ]


@pytest.fixture
def sample_task(sample_ipus, sample_turns):
    task = Task(
        task_id="01",
        session_id=1,
        start=0.0,
        duration=10.0,
        images=["img1.jpg", "img2.jpg"],
        describer="A",
        target="img1.jpg",
        score="1.0",
        time_used=10.0,
        turn_transitions=[
            TurnTransition(
                label="X1",
                turn_id_from=None,  # First turn has no previous turn
                turn_id_to=sample_turns[0].turn_id,
            ),
            TurnTransition(
                label="BC",
                turn_id_from=sample_turns[0].turn_id,
                turn_id_to=sample_turns[1].turn_id,
            ),
        ],
        turns=sample_turns,
        ipus=sample_ipus,
        wavs={"A": "/path/to/wav/A.wav", "B": "/path/to/wav/B.wav"},
    )
    return task


def intersects(a, b):
    """Check if two intervals (a and b) intersect."""
    return not (a.end <= b.start or b.end <= a.start)


class TestTurnTransitionType:
    def test_from_string_valid(self):
        assert TurnTransitionType.from_string("S") == TurnTransitionType.SMOOTH_SWITCH
        assert TurnTransitionType.from_string("BC") == TurnTransitionType.BACKCHANNEL

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            TurnTransitionType.from_string("INVALID")

    def test_str_representation(self):
        assert str(TurnTransitionType.SMOOTH_SWITCH) == "Transition S"
        assert str(TurnTransitionType.BACKCHANNEL) == "Transition BC"


class TestWord:
    def test_word_initialization(self):
        word = Word(start=0.0, end=1.0, text="hello", speaker="A")
        assert word.start == 0.0
        assert word.end == 1.0
        assert word.text == "hello"
        assert word.speaker == "A"
        assert word.duration == 1.0

    def test_word_representation(self):
        word = Word(start=0.0, end=1.0, text="hello", speaker="A")
        assert (
            repr(word)
            == "Word(start=0.0, end=1.0, text='hello', speaker='A', duration=1.0)"
        )


class TestIPU:
    def test_ipu_initialization(self, sample_words):
        ipu = IPU(words=sample_words)
        assert ipu.start == 0.0
        assert ipu.end == 2.0
        assert ipu.speaker == "A"
        assert ipu.duration == 2.0
        assert ipu.text == "hello world"
        assert ipu.num_words == 2

    def test_ipu_representation(self, sample_ipu):
        assert "IPU(words=" in repr(sample_ipu)
        assert "hello" in repr(sample_ipu)
        assert "world" in repr(sample_ipu)


class TestTurnTransition:
    def test_turn_transition_initialization(self, sample_turns):
        transition = TurnTransition(
            label="BC",
            turn_id_from=sample_turns[0].turn_id,
            turn_id_to=sample_turns[1].turn_id,
        )
        assert transition.label_type == TurnTransitionType.BACKCHANNEL
        assert transition.transition_duration == 1.0
        assert not transition.overlapped_transition

    def test_overlapped_transition(self, sample_turns):
        # Create an overlapping turn
        overlapped_turn = Turn(
            session_id=1,
            task_id=1,
            ipu_ids=[
                IPU(
                    words=[Word(start=0.5, end=1.5, text="overlap", speaker="B")]
                ).ipu_id
            ],
            speaker="B",
            start=0.5,
            end=1.5,
        )
        transition = TurnTransition(
            label="O",
            turn_id_from=sample_turns[0].turn_id,
            turn_id_to=overlapped_turn.turn_id,
        )
        assert transition.overlapped_transition

    def test_x3_transition_timing(self):
        """Verify that X3 transitions are always less than 210ms away from an interlocutor turn start."""
        MAX_X3_GAP = 0.210  # 210ms
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)

        for session in corpus.sessions.values():
            for task in session.tasks:
                # Get all X3 transitions
                x3_transitions = [t for t in task.turn_transitions if t.label == "X3"]
                for trans in x3_transitions:
                    to_turn = Turn.get_turn_by_id(trans.turn_id_to)
                    interlocutor_previous_turn = [
                        t for t in task.turns
                        if t.speaker != to_turn.speaker
                        and t.start <= to_turn.start][-1]
                    
                    gap = to_turn.start - interlocutor_previous_turn.start
                    assert gap <= MAX_X3_GAP, f"X3 transition gap exceeds 210ms ({to_turn.start} vs {interlocutor_previous_turn.start})"



class TestTurn:
    def test_turn_initialization(self, sample_turns):
        turn = sample_turns[0]
        assert turn.session_id == 1
        assert turn.task_id == 1
        assert turn.speaker == "A"
        assert turn.start == 0.0
        assert turn.end == 1.0
        assert turn.duration == 1.0
        assert len(turn.ipus) == 1

    def test_turn_text(self, sample_turns):
        turn = sample_turns[0]
        assert "hello" in turn.text

    def test_turn_id_builder(self):
        turn_id = Turn.id_builder(1, 1, "A", 0.0, 1.0)
        assert turn_id == "turn_01_01_A_0.00_1.00"

    def test_get_turn_by_id(self, sample_turns):
        turn = sample_turns[0]
        assert Turn.get_turn_by_id(turn.turn_id) == turn

    def test_turn_definition_correctness(self):
        """Verify that turns follow the definition: maximal sequence of IPUs without interlocutor speech during silences."""
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)
        
        for session in corpus.sessions.values():
            for task in session.tasks:
                all_ipus = sorted(task.ipus, key=lambda x: x.start)
                
                for turn in task.turns:
                    turn_ipus = sorted([IPU.get_ipu_by_id(ipu_id) for ipu_id in turn.ipu_ids], key=lambda x: x.start)
                    if len(turn_ipus) <= 1:
                        continue
                        
                    # Check each pair of consecutive IPUs in the turn
                    for i in range(len(turn_ipus) - 1):
                        current_ipu = turn_ipus[i]
                        next_ipu = turn_ipus[i + 1]
                        
                        # Find any interlocutor IPUs between these two IPUs
                        interlocutor_ipus = [
                            ipu for ipu in all_ipus
                            if ipu.speaker != turn.speaker
                            and intersects(current_ipu, ipu)
                        ]
                        assert not interlocutor_ipus, (
                            f"Found interlocutor IPUs between turn IPUs in "
                            f"session {session.session_id}, task {task.task_id}, "
                            f"turn {turn.turn_id}. Interlocutor IPUs: {interlocutor_ipus}"
                        )

    def test_no_consecutive_turns_same_speaker(self):
        """Verify there are no consecutive turns from the same speaker with silence between them."""
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)
        
        for session in corpus.sessions.values():
            for task in session.tasks:
                turns = sorted(task.turns, key=lambda x: x.start)
                
                for i in range(len(turns) - 1):
                    current_turn = turns[i]
                    next_turn = turns[i + 1]
                    
                    # Skip if turns are from different speakers
                    if current_turn.speaker != next_turn.speaker:
                        continue
                        
                    # Find any IPUs between these two turns
                    between_turn_ipus = [
                        ipu for ipu in task.ipus
                        if ipu.speaker != current_turn.speaker
                        and intersects(current_turn, ipu)
                    ]
                    
                    # If no interlocutor IPUs between turns, they should have been merged
                    assert between_turn_ipus, (
                        f"Found consecutive turns from speaker {current_turn.speaker} "
                        f"without interlocutor speech between them in "
                        f"session {session.session_id}, task {task.task_id}.\n"
                        f"Turn 1: {current_turn} ({current_turn.start:.2f}-{current_turn.end:.2f})\n"
                        f"Turn 2: {next_turn} ({next_turn.start:.2f}-{next_turn.end:.2f})"
                    )


class TestTask:
    def test_task_initialization(self, sample_task):
        assert sample_task.task_id == "01"
        assert sample_task.session_id == 1
        assert sample_task.images == ["img1.jpg", "img2.jpg"]
        assert sample_task.describer == "A"
        assert sample_task.target == "img1.jpg"
        assert sample_task.score == 1.0
        assert sample_task.time_used == 10.0
        assert len(sample_task.turn_transitions) == 2
        assert len(sample_task.ipus) == 2
        assert len(sample_task.wavs) == 2
        assert sample_task.duration == 10.0
        assert sample_task.start == 0.0

    def test_task_representation(self, sample_task):
        expected = "[Task 01 (A) 0.00:10.00 ] Turns 2 IPUs 2\n\t"
        expected += "[Turn (A) 0.00:1.00 ] \t hello\n\t"
        expected += "[Turn (B) 2.00:3.00 ] \t world\n\t"
        expected += "[IPU (A) 0.00:1.00 ] hello\n\t"
        expected += "[IPU (B) 2.00:3.00 ] world\n"
        assert str(sample_task) == expected

    def test_task_text_building(self, sample_task):
        expected_text = "\n\t[IPU (A) 0.00:1.00 ] hello\n\t[IPU (B) 2.00:3.00 ] world"
        assert sample_task.text == expected_text

    def test_task_repr(self, sample_task):
        expected = "[Task 01 (A) 0.00:10.00 ] Turns 2 IPUs 2"
        assert repr(sample_task) == expected

    def test_task_attributes(self, sample_task):
        assert sample_task.task_id == "01"
        assert sample_task.describer == "A"
        assert sample_task.score == 1.0

    def test_task_score_conversion(self, sample_ipus):
        turns = [
            Turn(
                session_id=1,
                task_id=2,
                ipu_ids=[sample_ipus[0].ipu_id],
                speaker="A",
                start=0.0,
                end=1.0,
            )
        ]
        task = Task(
            task_id="02",
            session_id=1,
            start=0.0,
            duration=10.0,
            images=["img1.jpg"],
            describer="A",
            target="img1.jpg",
            score="0.5",  # String score
            time_used=5.0,
            turn_transitions=[],
            turns=turns,  # Add turns argument
            ipus=sample_ipus,
            wavs={},
        )
        assert isinstance(task.score, float)
        assert task.score == 0.5

    def test_task_empty_ipus(self):
        # Create a task with empty IPUs - should initialize with start=0
        task = Task(
            task_id="03",
            session_id=1,
            start=0.0,
            duration=10.0,
            images=["img1.jpg"],
            describer="A",
            target="img1.jpg",
            score=1.0,
            time_used=5.0,
            turn_transitions=[],
            turns=[],
            ipus=[],
            wavs={},
        )
        assert task.start == 0.0
        assert len(task.ipus) == 0
        assert task.text == ""


class TestLoadTasksInfo:
    def test_load_tasks_info_batch1(self, sample_task_file):
        tasks = load_tasks_info(sample_task_file, batch=1)
        assert len(tasks) == 2
        assert tasks[0]["Images"] == ["img1", "img2"]
        assert tasks[0]["Describer"] == "A"
        assert float(tasks[0]["Score"]) == 1.0


class TestSpanishGamesCorpusDialogues:
    def test_initialization(self):
        corpus = SpanishGamesCorpusDialogues()
        assert corpus.corpus_raw is None
        assert corpus.sessions is None
        assert corpus.config.BANNED_SESSIONS == {28}

    def test_get_sessions_by_batch(self):
        corpus = SpanishGamesCorpusDialogues()
        corpus.sessions = {
            1: Session(session_id=1, batch=1, subject_a="A1", subject_b="B1", tasks=[]),
            2: Session(session_id=2, batch=2, subject_a="A2", subject_b="B2", tasks=[]),
        }
        batch1_sessions = corpus.get_sessions_by_batch(1)
        assert len(batch1_sessions) == 1
        assert 1 in batch1_sessions

    def test_batch1_task_distribution(self):
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)

        dev_tasks = list(corpus.dev_tasks(batch=1))
        held_out_tasks = list(corpus.held_out_tasks(batch=1))

        assert len(dev_tasks) == 132, "Batch 1 dev tasks count mismatch"
        assert len(held_out_tasks) == 64, "Batch 1 eval tasks count mismatch"

    def test_batch2_task_distribution(self):
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)

        dev_tasks = list(corpus.dev_tasks(batch=2))
        held_out_tasks = list(corpus.held_out_tasks(batch=2))

        assert len(dev_tasks) == 172, "Batch 2 dev tasks count mismatch"
        assert len(held_out_tasks) == 47, "Batch 2 eval tasks count mismatch"

    def test_batch1_transition_label_distribution(self):
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)

        dev_labels = {
            "BC": 565,
            "BC_O": 57,
            "BI": 61,
            "I": 151,
            "O": 491,
            "PI": 196,
            "S": 1466,
            "X1": 126,
            "X2": 464,
            "X2_O": 48,
            "X3": 352,
        }
        eval_labels = {
            "BC": 278,
            "BC_O": 29,
            "BI": 22,
            "I": 41,
            "O": 173,
            "PI": 60,
            "S": 577,
            "X1": 61,
            "X2": 232,
            "X2_O": 24,
            "X3": 136,
        }

        self._verify_label_distribution(corpus, 1, dev_labels, eval_labels)

    def test_batch2_transition_label_distribution(self):
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)

        dev_labels = {
            "BC": 555,
            "BC_O": 243,
            "BI": 118,
            "I": 283,
            "O": 767,
            "PI": 161,
            "S": 1804,
            "X1": 176,
            "X2": 497,
            "X2_O": 104,
            "X3": 324,
        }
        eval_labels = {
            "BC": 157,
            "BC_O": 46,
            "BI": 43,
            "I": 79,
            "O": 193,
            "PI": 34,
            "S": 650,
            "X1": 48,
            "X2": 109,
            "X2_O": 31,
            "X3": 93,
        }

        self._verify_label_distribution(corpus, 2, dev_labels, eval_labels)

    def _verify_label_distribution(self, corpus, batch, dev_expected, eval_expected):
        dev_tasks = list(corpus.dev_tasks(batch=batch))
        eval_tasks = list(corpus.held_out_tasks(batch=batch))

        dev_counts = self._count_transition_labels([t for t in dev_tasks])
        eval_counts = self._count_transition_labels([t for t in eval_tasks])

        for label, count in dev_expected.items():
            assert (
                dev_counts.get(label, 0) == count
            ), f"Batch {batch} dev {label} count mismatch"

        for label, count in eval_expected.items():
            assert (
                eval_counts.get(label, 0) == count
            ), f"Batch {batch} eval {label} count mismatch"

    def _count_transition_labels(self, tasks):
        counts = {}
        for task in tasks:
            for trans in task.turn_transitions:
                counts[trans.label] = counts.get(trans.label, 0) + 1
        return counts


    def test_raw_task_start(self):
        """Verify task start time in raw .tasks file matches expected value."""
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)
        
        SESSION_ID = 3
        TASK_ID = 2
        EXPECTED_START = 34.949
        
        tasks_mapping = corpus.corpus_raw["b1-dialogue-tasks"]
        task_key = f"s{SESSION_ID:02d}.objects.1.tasks"
        alt_key = f"s{SESSION_ID}.objects.1.tasks"
        
        tasks_file = tasks_mapping.get(task_key) or tasks_mapping.get(alt_key)
        tasks_info = load_tasks_info(tasks_file, batch=1)
        raw_start = next(t["Start"] for t in tasks_info if t["Task ID"] == TASK_ID)
        assert math.isclose(raw_start, EXPECTED_START, abs_tol=1e-6)

    def test_task_start_preserved(self):
        """Verify task start time is preserved when loaded by the tool."""
        SESSION_ID = 3
        TASK_ID = 2
        EXPECTED_START = 34.949
        
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)

        task = next(t for t in corpus.sessions[SESSION_ID].tasks if t.task_id == TASK_ID)
        assert math.isclose(task.start, EXPECTED_START, abs_tol=1e-6)

    def test_first_B_turn_included(self):
        """Verify first B turn (37.900-41.897s) is included in task turns."""
        corpus = SpanishGamesCorpusDialogues()
        corpus.load(load_audio=False)
        
        SESSION_ID = 3
        TASK_ID = 2
        FIRST_TURN_B = (37.900195, 41.897241)  

        task = next(t for t in corpus.sessions[SESSION_ID].tasks if t.task_id == TASK_ID)
        task_end = task.start + task.duration

        ipus = load_ipus_from_words(
            SESSION_ID, (task.start, task_end), corpus.corpus_raw["b1-dialogue-words"]
        )

        turns_B = load_turns_for_task(
            SESSION_ID,
            TASK_ID,
            turns_folder=corpus.corpus_raw["b1-dialogue-turns"],
            batch=1,
            ipus=ipus,
            task_boundaries=(task.start, task_end, None, None),
        )

        assert any(
            turn.speaker == "B"
            and math.isclose(turn.start, FIRST_TURN_B[0], abs_tol=1e-6)
            and math.isclose(turn.end, FIRST_TURN_B[1], abs_tol=1e-6)
            for turn in turns_B
        )


if __name__ == "__main__":
    pytest.main([__file__])
