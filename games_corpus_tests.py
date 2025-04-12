import pytest
from games_corpus import (
    SpanishGamesCorpusDialogues,
    Task,
    Session,
    Word,
    IPU,
    TurnTransition,
    TurnTransitionType,
    load_tasks_info,
    find_nearest_ipu,
)


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
def sample_task(sample_ipus):
    task = Task(
        task_id="01",
        session_id=1,
        images=["img1.jpg", "img2.jpg"],
        describer="A",
        target="img1.jpg",
        score="1.0",
        time_used=10.0,
        turn_transitions=[
            TurnTransition(label="H", ipu_from=sample_ipus[0], ipu_to=sample_ipus[1])
        ],
        ipus=sample_ipus,
        wavs={"A": "/path/to/wav/A.wav", "B": "/path/to/wav/B.wav"},
    )
    return task


class TestTurnTransitionType:
    def test_from_string_valid(self):
        assert TurnTransitionType.from_string("H") == TurnTransitionType.HOLD_TURN
        assert TurnTransitionType.from_string("S") == TurnTransitionType.SMOOTH_SWITCH
        assert TurnTransitionType.from_string("BC") == TurnTransitionType.BACKCHANNEL

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            TurnTransitionType.from_string("INVALID")

    def test_str_representation(self):
        assert str(TurnTransitionType.HOLD_TURN) == "H"
        assert str(TurnTransitionType.BACKCHANNEL) == "BC"


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
        assert repr(word) == "Word(0.0, 1.0, hello)"


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
        assert "[0.0:2.0] A: hello world" in repr(sample_ipu)


class TestTurnTransition:
    def test_turn_transition_initialization(self, sample_ipus):
        transition = TurnTransition(
            label="H", ipu_from=sample_ipus[0], ipu_to=sample_ipus[1]
        )
        assert transition.label == TurnTransitionType.HOLD_TURN
        assert transition.transition_duration == 1.0
        assert not transition.overlapped_transition

    def test_overlapped_transition(self, sample_ipus):
        ipu_overlapped = IPU(
            words=[Word(start=0.5, end=1.5, text="overlap", speaker="B")]
        )
        transition = TurnTransition(
            label="O", ipu_from=sample_ipus[0], ipu_to=ipu_overlapped
        )
        assert transition.overlapped_transition


class TestTask:
    def test_task_initialization(self, sample_task):
        assert sample_task.task_id == "01"
        assert sample_task.session_id == 1
        assert sample_task.images == ["img1.jpg", "img2.jpg"]
        assert sample_task.describer == "A"
        assert sample_task.target == "img1.jpg"
        assert sample_task.score == 1.0
        assert sample_task.duration == 10.0
        assert len(sample_task.turn_transitions) == 1
        assert len(sample_task.ipus) == 2
        assert len(sample_task.wavs) == 2

    def test_task_start_time(self, sample_task):
        assert sample_task.start == 0.0  # Based on first IPU start time

    def test_task_text_building(self, sample_task):
        expected_text = "\n\t[0.0:1.0] A: hello\n\t[2.0:3.0] B: world"
        assert sample_task.text == expected_text

    def test_task_representation(self, sample_task):
        expected = f"Task(01, 1, A, img1.jpg, 1.0, 10.0, 2 IPUs, 2 wavs)"
        assert repr(sample_task) == expected

    def test_task_getitem(self, sample_task):
        assert sample_task["task_id"] == "01"
        assert sample_task["describer"] == "A"
        assert sample_task["score"] == 1.0

    def test_task_score_conversion(self, sample_ipus):
        # Test that string scores are properly converted to float
        task = Task(
            task_id="02",
            session_id=1,
            images=["img1.jpg"],
            describer="A",
            target="img1.jpg",
            score="0.5",  # String score
            time_used=5.0,
            turn_transitions=[],
            ipus=sample_ipus,
            wavs={},
        )
        assert isinstance(task.score, float)
        assert task.score == 0.5

    def test_task_empty_ipus(self):
        with pytest.raises(IndexError):
            # Should raise error when trying to get start time from empty ipus
            Task(
                task_id="03",
                session_id=1,
                images=["img1.jpg"],
                describer="A",
                target="img1.jpg",
                score=1.0,
                time_used=5.0,
                turn_transitions=[],
                ipus=[],
                wavs={},
            )


class TestLoadTasksInfo:
    def test_load_tasks_info_batch1(self, sample_task_file):
        tasks = load_tasks_info(sample_task_file, batch=1)
        assert len(tasks) == 2
        assert tasks[0]["Images"] == ["img1", "img2"]
        assert tasks[0]["Describer"] == "A"
        assert float(tasks[0]["Score"]) == 1.0


class TestFindNearestIPU:
    def test_find_nearest_ipu(self, sample_ipus):
        found_ipu = find_nearest_ipu(sample_ipus, 0.1, 1.1, max_diff=0.3)
        assert found_ipu == sample_ipus[0]

    def test_find_nearest_ipu_no_match(self, sample_ipus):
        found_ipu = find_nearest_ipu(sample_ipus, 5.0, 6.0, max_diff=0.1)
        assert found_ipu is None


class TestSpanishGamesCorpusDialogues:
    def test_initialization(self):
        corpus = SpanishGamesCorpusDialogues()
        assert corpus.corpus_raw is None
        assert corpus.sessions is None
        assert corpus.banned_sessions == {28}

    def test_get_sessions_by_batch(self):
        corpus = SpanishGamesCorpusDialogues()
        corpus.sessions = {
            1: Session(session_id=1, batch=1, subject_a="A1", subject_b="B1", tasks=[]),
            2: Session(session_id=2, batch=2, subject_a="A2", subject_b="B2", tasks=[]),
        }
        batch1_sessions = corpus.get_sessions_by_batch(1)
        assert len(batch1_sessions) == 1
        assert 1 in batch1_sessions


if __name__ == "__main__":
    pytest.main([__file__])
