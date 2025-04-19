"""Shared types and data classes for the Games Corpus"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
from enum import Enum
import logging


class TurnTransitionType(Enum):
    # Regular transitions
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
        return "Transition " + self.value


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
    # Class-level storage
    _all_ipus = {}

    words: List[Word]
    speaker: str = field(init=False)
    start: float = field(init=False)
    end: float = field(init=False)
    duration: float = field(init=False)
    text: str = field(init=False)
    num_words: int = field(init=False)

    @classmethod
    def id_builder(cls, speaker: str, start: float, end: float) -> str:
        return f"ipu_{speaker}_{start:.2f}_{end:.2f}"

    @classmethod
    def get_ipu_by_id(cls, ipu_id: str) -> Optional["IPU"]:
        return cls._all_ipus.get(ipu_id)

    @classmethod
    def clear_registry(cls):
        """Clear the IPUs registry"""
        cls._all_ipus.clear()

    def __post_init__(self):
        self.start = self.words[0].start
        self.end = self.words[-1].end
        self.speaker = self.words[0].speaker
        self.duration = self.end - self.start
        self.text = " ".join(word.text for word in self.words)
        self.num_words = len(self.words)

        # Register this IPU
        self.ipu_id = IPU.id_builder(self.speaker, self.start, self.end)
        IPU._all_ipus[self.ipu_id] = self

    def __str__(self) -> str:
        return f"[IPU ({self.speaker}) {self.start:.02f}:{self.end:.02f} ] {self.text}"


@dataclass
class Turn:
    session_id: int
    task_id: int
    ipu_ids: List[str]  # Changed from ipus to ipu_ids
    speaker: str
    start: float
    end: float
    duration: float = field(init=False)
    text: str = field(init=False)
    num_words: int = field(init=False)

    # Class-level storage (outside the dataclass fields)
    _all_turns = {}

    @classmethod
    def get_turn_by_id(cls, turn_id: str) -> Optional["Turn"]:
        return cls._all_turns[turn_id]

    @classmethod
    def clear_registry(cls):
        """Clear the turns registry"""
        cls._all_turns.clear()

    @classmethod
    def id_builder(cls, session_id, task_id, speaker, turn_start, turn_end):
        return f"turn_{session_id:02d}_{task_id:02d}_{speaker}_{turn_start:.2f}_{turn_end:.2f}"

    @property
    def ipus(self) -> List[IPU]:
        """Get IPUs from their IDs"""
        return [IPU.get_ipu_by_id(ipu_id) for ipu_id in self.ipu_ids]

    def __post_init__(self):
        if not self.ipu_ids:  # Changed from ipus to ipu_ids
            raise ValueError("IPUs list cannot be empty")

        self.turn_id = Turn.id_builder(
            self.session_id, self.task_id, self.speaker, self.start, self.end
        )

        # Register this turn
        Turn._all_turns[self.turn_id] = self

        self.duration = self.end - self.start
        self.text = (
            f"[Turn ({self.speaker}) {self.start:.02f}:{self.end:.02f} ] \t "
            + " ".join(ipu.text for ipu in self.ipus)  # Using the property
        )
        self.num_words = sum(ipu.num_words for ipu in self.ipus)  # Using the property

    def __str__(self) -> str:
        return self.text


@dataclass
class TurnTransition:
    label: str
    turn_id_from: Optional[str] = field()
    turn_id_to: str = field()

    turn_from: Optional[Turn] = field(init=False)
    turn_to: Turn = field(init=False)
    ipu_from: Optional[IPU] = field(init=False)
    ipu_to: IPU = field(init=False)
    speaker_from: Optional[str] = field(init=False)
    speaker_to: str = field(init=False)
    session_id: int = field(init=False)
    task_id: int = field(init=False)
    label_type: TurnTransitionType = field(init=False)
    transition_duration: float = field(init=False)
    overlapped_transition: bool = field(init=False)

    def __post_init__(self):
        self.label_type = TurnTransitionType.from_string(self.label)

        self.turn_from = (
            Turn.get_turn_by_id(self.turn_id_from) if self.turn_id_from else None
        )
        self.turn_to = Turn.get_turn_by_id(self.turn_id_to)

        self.speaker_from = self.turn_from.speaker if self.turn_from else None
        self.speaker_to = self.turn_to.speaker
        self.session_id = self.turn_to.session_id
        self.task_id = self.turn_to.task_id

        self.ipu_from = self.turn_from.ipus[-1] if self.turn_from else None
        self.ipu_to = self.turn_to.ipus[0]
        self.transition_duration = (
            self.ipu_to.start - self.ipu_from.end if self.ipu_from else 0
        )
        self.overlapped_transition = self.transition_duration < 0


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
    start: float
    duration: float
    text: str = field(init=False)

    def __post_init__(self):
        self.score = float(self.score)
        self.ipus = sorted(self.ipus, key=lambda x: x.start) if self.ipus else []
        self.text = self._build_text()

    def _build_text(self) -> str:
        if not self.ipus:
            return ""
        return "\n\t" + "\n\t".join([str(ipu) for ipu in self.ipus])

    def __str__(self) -> str:
        return (
            f"[Task {self.task_id} ({self.describer}) {self.start:.02f}:{self.start + self.duration:.02f} ] Turns {len(self.turns)} IPUs {len(self.ipus)}\n\t"
            + "\n\t".join([str(turn) for turn in self.turns])
            + "\n\t"
            + "\n\t".join([str(ipu) for ipu in self.ipus])
            + "\n"
        )

    def __repr__(self):
        return f"[Task {self.task_id} ({self.describer}) {self.start:.02f}:{self.start + self.duration:.02f} ] Turns {len(self.turns)} IPUs {len(self.ipus)}"


@dataclass(frozen=True)
class Session:
    session_id: int
    batch: int
    subject_a: str
    subject_b: str
    tasks: List[Task]

    # Class-level storage (outside the dataclass fields)
    _all_sessions = {}

    def __post_init__(self):
        # Register this session
        Session._all_sessions[self.session_id] = self

    @classmethod
    def get_session_by_id(cls, session_id: int) -> Optional["Session"]:
        return cls._all_sessions.get(session_id)

    @classmethod
    def clear_registry(cls):
        """Clear the sessions registry"""
        cls._all_sessions.clear()

    def __str__(self) -> str:
        return f"[Session {self.session_id} ({self.subject_a}, {self.subject_b})] (tasks_count: {len(self.tasks)})"

    def __repr__(self):
        return f"[Session {self.session_id} ({self.subject_a}, {self.subject_b})] (tasks_count: {len(self.tasks)})"


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
