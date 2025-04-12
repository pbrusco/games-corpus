"""Shared types and data classes for the Games Corpus"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
from enum import Enum


class TurnTransitionType(Enum):
    # Regular transitions
    HOLD_TURN = "H"
    SMOOTH_SWITCH = "S"
    BACKCHANNEL = "BC"
    PAUSED_INTERRUPTION = "PI"

    # Overlapped transitions
    OVERLAPPED_SWITCH = "O"
    OVERLAPPED_BACKCHANNEL = "BC_O"
    OVERLAPPED_INTERRUPTION = "I"
    OVERLAPPED_BUTT_IN = "BI"

    # Special transitions
    FIRST_TURN = "X1"
    BACKCHANNEL_CONTINUATION = "X2"
    OVERLAPPED_BACKCHANNEL_CONTINUATION = "X2_O"
    SIMULTANEOUS_START = "X3"

    AMBIGUOUS = "A"

    @classmethod
    def from_string(cls, label: str) -> "TurnTransitionType":
        label = label.upper()
        if label in ["L", "L-SIM", "N", "N-SIM"]:
            label = "A"
        for member in cls:
            if member.value == label:
                return member
        raise ValueError(f"Unknown transition label: {label}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str
    speaker: str
    duration: float = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "duration", self.end - self.start)

    def __str__(self) -> str:
        return self.text


@dataclass
class IPU:
    words: List[Word]
    start: float = field(init=False)
    end: float = field(init=False)
    speaker: str = field(init=False)
    duration: float = field(init=False)
    text: str = field(init=False)
    num_words: int = field(init=False)

    def __post_init__(self):
        self.start = self.words[0].start
        self.end = self.words[-1].end
        self.speaker = self.words[0].speaker
        self.duration = self.end - self.start
        self.text = " ".join(word.text for word in self.words)
        self.num_words = len(self.words)

    def __str__(self) -> str:
        return self.text


@dataclass
class Turn:
    ipus: List[IPU]
    speaker: str
    start: float = field(init=False)
    end: float = field(init=False)
    duration: float = field(init=False)
    text: str = field(init=False)
    num_words: int = field(init=False)

    def __post_init__(self):
        if not self.ipus:
            raise ValueError("IPUs list cannot be empty")
        self.start = self.ipus[0].start
        self.end = self.ipus[-1].end
        self.duration = self.end - self.start
        self.text = f"({self.speaker}) " + " ".join(ipu.text for ipu in self.ipus)
        self.num_words = sum(ipu.num_words for ipu in self.ipus)

    def __str__(self) -> str:
        return self.text


@dataclass
class TurnTransition:
    label: str
    ipu_from: Optional[IPU]
    ipu_to: IPU
    turn_from: str
    turn_to: str
    label_type: TurnTransitionType = field(init=False)
    duration: float = field(init=False)
    overlapped_transition: bool = field(init=False)

    def __post_init__(self):
        self.label_type = TurnTransitionType.from_string(self.label)
        self.duration = self.ipu_to.start - self.ipu_from.end if self.ipu_from else 0
        self.overlapped_transition = self.duration < 0


@dataclass
class Task:
    task_id: int
    session_id: int
    images: List[str]
    describer: str
    target: str
    score: float
    time_used: float
    turn_transitions: List["TurnTransition"]
    turns: List["Turn"]
    ipus: List["IPU"]
    wavs: Dict[str, str]
    start: float = field(init=False)
    duration: float = field(init=False)
    text: str = field(init=False)

    def __post_init__(self):
        self.score = float(self.score)
        self.start = self.ipus[0].start if self.ipus else 0
        self.duration = float(self.time_used)
        self.ipus = sorted(self.ipus, key=lambda x: x.start) if self.ipus else []
        self.text = self._build_text()

    def _build_text(self) -> str:
        if not self.ipus:
            return ""
        return "\n\t" + "\n\t".join([str(ipu) for ipu in self.ipus])


@dataclass(frozen=True)
class Session:
    session_id: int
    batch: int
    subject_a: str
    subject_b: str
    tasks: List[Task]


@dataclass
class BatchConfig:
    """Configuration for a specific batch of the corpus"""
    batch_num: int
    heldout_tasks: Set[Tuple[int, int]]
    heldout_sessions: Set[int]

    @classmethod
    def create_batch1_config(cls) -> "BatchConfig":
        return cls(
            batch_num=1,
            heldout_tasks=set((i, j) for i in range(1, 15) for j in (13, 14)),
            heldout_sessions={7, 12, 13},
        )

    @classmethod
    def create_batch2_config(cls) -> "BatchConfig":
        return cls(
            batch_num=2,
            heldout_tasks=set((i, j) for i in range(15, 29) for j in (13, 14)),
            heldout_sessions={21, 22, 28},
        )

    def is_heldout_task(self, session_id: int, task_id: int) -> bool:
        return (session_id, task_id) in self.heldout_tasks

    def is_heldout_session(self, session_id: int) -> bool:
        return session_id in self.heldout_sessions
