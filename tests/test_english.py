"""Integration tests for the Columbia English Games Corpus."""

from pathlib import Path

import pytest
from games_corpus import EnglishGamesCorpus, TurnTransitionType

ENGLISH_CORPUS_PATH = Path(__file__).resolve().parent.parent / "corpus" / "games-english"
ENGLISH_FEATURES_PATH = Path(__file__).resolve().parent.parent / "features" / "games-english"
requires_english_corpus = pytest.mark.skipif(
    not (ENGLISH_CORPUS_PATH / "README.sessions-info").exists(),
    reason="English corpus not available locally",
)
requires_english_features = pytest.mark.skipif(
    not (ENGLISH_FEATURES_PATH / "tasks_features").exists(),
    reason="English features not available locally",
)


@requires_english_corpus
class TestEnglishGamesCorpus:
    @pytest.fixture(scope="class")
    def corpus(self):
        c = EnglishGamesCorpus()
        c.load(local_path=str(ENGLISH_CORPUS_PATH), load_audio=False)
        return c

    def test_load_sessions(self, corpus):
        assert len(corpus.sessions) == 12

    def test_session_ids(self, corpus):
        assert set(corpus.sessions.keys()) == set(range(1, 13))

    def test_session_has_tasks(self, corpus):
        for session in corpus.sessions.values():
            assert len(session.tasks) > 0, f"Session {session.session_id} has no tasks"

    def test_total_task_count(self, corpus):
        total = sum(len(s.tasks) for s in corpus.sessions.values())
        assert total == 168

    def test_task_has_turns(self, corpus):
        task = corpus.sessions[1].tasks[0]
        assert len(task.turns) > 0

    def test_task_has_transitions(self, corpus):
        task = corpus.sessions[1].tasks[0]
        assert len(task.turn_transitions) > 0

    def test_task_metadata(self, corpus):
        task = corpus.sessions[1].tasks[0]
        assert task.describer in ("A", "B")
        assert task.target != ""
        assert task.score > 0
        assert task.duration > 0

    def test_transition_labels_valid(self, corpus):
        for session in corpus.sessions.values():
            for task in session.tasks:
                for trans in task.turn_transitions:
                    # Should not raise
                    TurnTransitionType.from_string(trans.label)

    def test_first_session_subjects(self, corpus):
        session = corpus.sessions[1]
        assert session.subject_a == "101"
        assert session.subject_b == "102"

    def test_corpus_not_found_raises(self):
        corpus = EnglishGamesCorpus()
        with pytest.raises(FileNotFoundError):
            corpus.load(local_path="/nonexistent/path")

    def test_get_features_without_path_raises(self, corpus):
        task = corpus.sessions[1].tasks[0]
        with pytest.raises(ValueError, match="No features path configured"):
            corpus.get_features(task)


@requires_english_corpus
@requires_english_features
class TestEnglishFeatures:
    @pytest.fixture(scope="class")
    def corpus(self):
        c = EnglishGamesCorpus()
        c.load(
            local_path=str(ENGLISH_CORPUS_PATH),
            features_path=str(ENGLISH_FEATURES_PATH),
            load_audio=False,
        )
        return c

    def test_get_features_returns_dataframe(self, corpus):
        task = corpus.sessions[1].tasks[0]
        df = corpus.get_features(task)
        assert len(df) > 0
        assert "time" in df.columns

    def test_features_have_expected_columns(self, corpus):
        task = corpus.sessions[1].tasks[0]
        df = corpus.get_features(task)
        expected = ["time", "pitch_standardized_A", "vad_A", "pitch_standardized_B", "vad_B"]
        for col in expected:
            assert col in df.columns, f"Missing column: {col}"

    def test_features_time_range_matches_task(self, corpus):
        task = corpus.sessions[1].tasks[0]
        df = corpus.get_features(task)
        assert df["time"].min() >= task.start - 1.0
        assert df["time"].max() <= task.start + task.duration + 1.0

    def test_features_file_not_found(self, corpus):
        from games_corpus.types import Task

        fake_task = Task(
            task_id=999,
            session_id=99,
            images=[],
            describer="A",
            target="x",
            score=0,
            time_used=0,
            turn_transitions=[],
            turns=[],
            ipus=[],
            wavs={},
            start=0,
            duration=0,
        )
        with pytest.raises(FileNotFoundError):
            corpus.get_features(fake_task)


to_be_reviewed_by_human = pytest.mark.to_be_reviewed_by_human


@requires_english_corpus
class TestEnglishCorpusDataQuality:
    """Interesting edge cases specific to the English corpus."""

    @pytest.fixture(scope="class")
    def corpus(self):
        c = EnglishGamesCorpus()
        c.load(local_path=str(ENGLISH_CORPUS_PATH), load_audio=False)
        return c

    @to_be_reviewed_by_human
    def test_transition_label_distribution(self, corpus):
        """Verify total transition counts across the English corpus."""
        from collections import Counter

        counts = Counter()
        for session in corpus.sessions.values():
            for task in session.tasks:
                for trans in task.turn_transitions:
                    counts[trans.label] += 1
        total = sum(counts.values())
        assert total > 4000, f"Expected >4000 total transitions, got {total}"
        assert counts["S"] > 1000, f"Expected >1000 smooth switches, got {counts['S']}"

    @to_be_reviewed_by_human
    def test_all_sessions_have_both_speakers(self, corpus):
        """Every session should have turns from both speakers A and B."""
        for session_id, session in corpus.sessions.items():
            speakers = set()
            for task in session.tasks:
                for turn in task.turns:
                    speakers.add(turn.speaker)
            assert speakers == {"A", "B"}, f"Session {session_id} missing speaker(s): has {speakers}"

    @to_be_reviewed_by_human
    def test_task_scores_in_valid_range(self, corpus):
        """All task scores should be between 0 and 100."""
        for session in corpus.sessions.values():
            for task in session.tasks:
                assert 0 <= float(task.score) <= 100, (
                    f"Session {task.session_id} task {task.task_id}: score={task.score}"
                )

    @to_be_reviewed_by_human
    @pytest.mark.xfail(reason="Known corpus data quality issue — some turns extend beyond task boundaries")
    def test_turns_are_within_task_boundaries(self, corpus):
        """Every turn should start and end within its task's time boundaries (with tolerance)."""
        tolerance = 1.0
        violations = []
        for session in corpus.sessions.values():
            for task in session.tasks:
                task_end = task.start + task.duration
                for turn in task.turns:
                    if turn.start < task.start - tolerance or turn.end > task_end + tolerance:
                        violations.append(
                            f"s{task.session_id} t{task.task_id}: turn {turn.start:.2f}-{turn.end:.2f} "
                            f"outside task {task.start:.2f}-{task_end:.2f}"
                        )
        assert violations == [], "Turns outside task boundaries:\n" + "\n".join(violations[:10])

    @to_be_reviewed_by_human
    def test_every_task_has_14_tasks_per_session(self, corpus):
        """Each English session should have exactly 14 object tasks."""
        for session_id, session in corpus.sessions.items():
            assert len(session.tasks) == 14, f"Session {session_id} has {len(session.tasks)} tasks, expected 14"
