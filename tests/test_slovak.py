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
