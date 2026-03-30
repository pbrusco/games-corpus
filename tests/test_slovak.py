"""Integration tests for the Slovak Games Corpus."""

from pathlib import Path

import pytest
from games_corpus import SlovakGamesCorpus, TurnTransitionType

SLOVAK_CORPUS_PATH = Path(__file__).resolve().parent.parent / "corpus" / "games-slovak"
requires_slovak_corpus = pytest.mark.skipif(
    not (SLOVAK_CORPUS_PATH / "documents" / "sessions_info.txt").exists(),
    reason="Slovak corpus not available locally",
)


@requires_slovak_corpus
class TestSlovakGamesCorpus:
    @pytest.fixture(scope="class")
    def corpus(self):
        c = SlovakGamesCorpus()
        c.load(local_path=str(SLOVAK_CORPUS_PATH), load_audio=False)
        return c

    def test_load_sessions(self, corpus):
        assert len(corpus.sessions) == 9

    def test_session_ids(self, corpus):
        assert set(corpus.sessions.keys()) == set(range(1, 10))

    def test_session_has_tasks(self, corpus):
        for session in corpus.sessions.values():
            assert len(session.tasks) > 0, f"Session {session.session_id} has no tasks"

    def test_total_task_count(self, corpus):
        total = sum(len(s.tasks) for s in corpus.sessions.values())
        assert total == 122

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
        assert float(task.score) > 0
        assert task.duration > 0

    def test_transition_labels_valid(self, corpus):
        for session in corpus.sessions.values():
            for task in session.tasks:
                for trans in task.turn_transitions:
                    TurnTransitionType.from_string(trans.label)

    def test_first_session_subjects(self, corpus):
        session = corpus.sessions[1]
        assert session.subject_a == "1"
        assert session.subject_b == "2"

    def test_corpus_not_found_raises(self):
        corpus = SlovakGamesCorpus()
        with pytest.raises(FileNotFoundError):
            corpus.load(local_path="/nonexistent/path")

    def test_get_features_without_path_raises(self, corpus):
        task = corpus.sessions[1].tasks[0]
        with pytest.raises(ValueError, match="No features path configured"):
            corpus.get_features(task)


to_be_reviewed_by_human = pytest.mark.to_be_reviewed_by_human


@requires_slovak_corpus
class TestSlovakCorpusDataQuality:
    """Interesting edge cases specific to the Slovak corpus."""

    @pytest.fixture(scope="class")
    def corpus(self):
        c = SlovakGamesCorpus()
        c.load(local_path=str(SLOVAK_CORPUS_PATH), load_audio=False)
        return c

    @to_be_reviewed_by_human
    def test_transition_label_distribution(self, corpus):
        """Verify total transition counts across the Slovak corpus."""
        from collections import Counter

        counts = Counter()
        for session in corpus.sessions.values():
            for task in session.tasks:
                for trans in task.turn_transitions:
                    counts[trans.label] += 1
        total = sum(counts.values())
        assert total > 3000, f"Expected >3000 total transitions, got {total}"
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
        tolerance = 1.0  # 1 second tolerance
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
    def test_ipus_have_nonempty_text(self, corpus):
        """Every IPU should contain at least one word of actual text."""
        empty_ipus = []
        for session in corpus.sessions.values():
            for task in session.tasks:
                for ipu in task.ipus:
                    if not ipu.text.strip():
                        empty_ipus.append(f"s{task.session_id} t{task.task_id} ipu@{ipu.start:.2f}")
        assert empty_ipus == [], f"Empty IPUs found: {empty_ipus[:10]}"
