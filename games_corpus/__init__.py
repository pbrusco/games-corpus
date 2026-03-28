"""Games Corpus library — supporting the UBA Spanish and Columbia English Games Corpora."""

from games_corpus.types import (
    Word,
    IPU,
    Turn,
    TurnTransition,
    TurnTransitionType,
    Task,
    Session,
    BatchConfig,
)
from games_corpus.spanish import SpanishGamesCorpus, SpanishGamesCorpusDialogues
from games_corpus.english import EnglishGamesCorpus

__all__ = [
    "Word",
    "IPU",
    "Turn",
    "TurnTransition",
    "TurnTransitionType",
    "Task",
    "Session",
    "BatchConfig",
    "SpanishGamesCorpus",
    "SpanishGamesCorpusDialogues",
    "EnglishGamesCorpus",
]
