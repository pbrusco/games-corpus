"""Integration tests for the Columbia English Games Corpus."""

from pathlib import Path

import pytest
from games_corpus import EnglishGamesCorpus, TurnTransitionType

ENGLISH_CORPUS_PATH = Path(__file__).resolve().parent.parent / "corpus" / "games-english"
requires_english_corpus = pytest.mark.skipif(
    not (ENGLISH_CORPUS_PATH / "README.sessions-info").exists(),
    reason="English corpus not available locally",
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
