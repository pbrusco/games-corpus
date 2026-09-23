"""Games Corpus library — supporting the UBA Spanish, Columbia English, and Slovak Games Corpora."""

from games_corpus.types import (
    Word,
    IPU,
    Turn,
    TurnTransition,
    TurnTransitionKind,
    TurnTransitionType,
    Task,
    Session,
    BatchConfig,
)
from games_corpus.base import BaseGamesCorpus
from games_corpus.punctuation import PunctuatedPhrase
from games_corpus.spanish import SpanishGamesCorpus
from games_corpus.english import EnglishGamesCorpus
from games_corpus.slovak import SlovakGamesCorpus

__all__ = [
    "BaseGamesCorpus",
    "Word",
    "IPU",
    "Turn",
    "TurnTransition",
    "TurnTransitionKind",
    "TurnTransitionType",
    "Task",
    "Session",
    "BatchConfig",
    "PunctuatedPhrase",
    "SpanishGamesCorpus",
    "EnglishGamesCorpus",
    "SlovakGamesCorpus",
]
