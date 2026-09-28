"""Development / control splits (Brusco, 2021, cap. 4)."""

from types import SimpleNamespace

from games_corpus.base import BaseGamesCorpus
from games_corpus.types import BatchConfig


def _sessions(n_sessions: int, n_tasks: int) -> dict:
    return {
        s: SimpleNamespace(tasks=[SimpleNamespace(session_id=s, task_id=t) for t in range(1, n_tasks + 1)])
        for s in range(1, n_sessions + 1)
    }


def test_split_is_a_partition_with_the_control_rule():
    sessions = _sessions(12, 14)
    config = BatchConfig.create_english_config()
    dev = [(t.session_id, t.task_id) for t in BaseGamesCorpus._tasks_in_split(sessions, config, held_out=False)]
    control = [(t.session_id, t.task_id) for t in BaseGamesCorpus._tasks_in_split(sessions, config, held_out=True)]
    assert not set(dev) & set(control)
    assert len(dev) + len(control) == 12 * 14
    assert {s for s, _ in control if s in (7, 9, 11)} == {7, 9, 11}
    assert all(t in (13, 14) for s, t in control if s not in (7, 9, 11))


def test_slovak_session_4_uses_tasks_6_and_9():
    config = BatchConfig.create_slovak_config()
    assert config.is_heldout_task(4, 6) and config.is_heldout_task(4, 9)
    assert not config.is_heldout_task(4, 13)


def test_batch2_control_covers_every_annotated_session():
    config = BatchConfig.create_batch2_config()
    assert config.heldout_sessions == {21, 22}
    assert {s for s, _ in config.heldout_tasks} == {21, 22, 23, 24, 25, 26, 27, 29, 30}
