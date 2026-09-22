"""Shared types and data classes for the Games Corpus."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import ClassVar


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
        if label in ["L", "L-SIM", "N", "N-SIM", "?"]:
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "duration", self.end - self.start)

    def __str__(self) -> str:
        return self.text


@dataclass
class IPU:
    # Class-level storage
    _all_ipus: ClassVar[dict[str, "IPU"]] = {}

    words: list[Word]
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
    def get_ipu_by_id(cls, ipu_id: str) -> "IPU | None":
        return cls._all_ipus.get(ipu_id)

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the IPUs registry."""
        cls._all_ipus.clear()

    def __post_init__(self) -> None:
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
    ipu_ids: list[str]
    speaker: str
    start: float
    end: float
    duration: float = field(init=False)
    text: str = field(init=False)
    num_words: int = field(init=False)

    # Class-level storage (outside the dataclass fields)
    _all_turns: ClassVar[dict[str, "Turn"]] = {}

    @classmethod
    def get_turn_by_id(cls, turn_id: str) -> "Turn | None":
        return cls._all_turns.get(turn_id)

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the turns registry."""
        cls._all_turns.clear()

    @classmethod
    def id_builder(cls, session_id: int, task_id: int, speaker: str, turn_start: float, turn_end: float) -> str:
        return f"turn_{session_id:02d}_{task_id:02d}_{speaker}_{turn_start:.2f}_{turn_end:.2f}"

    @property
    def ipus(self) -> list[IPU]:
        """Get IPUs from their IDs."""
        result: list[IPU] = []
        for ipu_id in self.ipu_ids:
            ipu = IPU.get_ipu_by_id(ipu_id)
            if ipu is None:
                raise KeyError(f"IPU with ID '{ipu_id}' not found in registry")
            result.append(ipu)
        return result

    def __post_init__(self) -> None:
        if not self.ipu_ids:
            raise ValueError("IPUs list cannot be empty")

        self.turn_id = Turn.id_builder(self.session_id, self.task_id, self.speaker, self.start, self.end)

        # Register this turn
        Turn._all_turns[self.turn_id] = self

        self.duration = self.end - self.start
        self.text = f"[Turn ({self.speaker}) {self.start:.02f}:{self.end:.02f} ] \t " + " ".join(
            ipu.text for ipu in self.ipus
        )
        self.num_words = sum(ipu.num_words for ipu in self.ipus)

    def __str__(self) -> str:
        return self.text


@dataclass
class TurnTransition:
    label: str
    turn_id_from: str | None = field()
    turn_id_to: str = field()

    turn_from: Turn | None = field(init=False)
    turn_to: Turn = field(init=False)
    ipu_from: IPU | None = field(init=False)
    ipu_to: IPU = field(init=False)
    speaker_from: str | None = field(init=False)
    speaker_to: str = field(init=False)
    session_id: int = field(init=False)
    task_id: int = field(init=False)
    label_type: TurnTransitionType = field(init=False)
    # Signed seconds between ipu_from.end and ipu_to.start: positive = silence gap
    # before turn_to starts, negative = magnitude of speech overlap between the two
    # turns. Use overlapped_transition (below) rather than a sign check on this value
    # -- e.g. abs(transition_duration) for a magnitude regardless of which case it is.
    transition_duration: float = field(init=False)
    overlapped_transition: bool = field(init=False)

    def __post_init__(self) -> None:
        self.label_type = TurnTransitionType.from_string(self.label)

        if self.turn_id_from:
            turn_from = Turn.get_turn_by_id(self.turn_id_from)
            if turn_from is None:
                raise ValueError(f"Source turn not found: {self.turn_id_from}")
            self.turn_from = turn_from
        else:
            self.turn_from = None

        turn_to = Turn.get_turn_by_id(self.turn_id_to)
        if turn_to is None:
            raise ValueError(f"Target turn not found: {self.turn_id_to}")
        self.turn_to = turn_to

        self.speaker_from = self.turn_from.speaker if self.turn_from else None
        self.speaker_to = self.turn_to.speaker
        self.session_id = self.turn_to.session_id
        self.task_id = self.turn_to.task_id

        self.ipu_from = self.turn_from.ipus[-1] if self.turn_from and self.turn_from.ipus else None
        if not self.turn_to.ipus:
            raise ValueError(f"Target turn {self.turn_id_to} has no IPUs")
        self.ipu_to = self.turn_to.ipus[0]
        # See the transition_duration field comment above for the sign convention.
        self.transition_duration = self.ipu_to.start - self.ipu_from.end if self.ipu_from else 0.0
        self.overlapped_transition = self.transition_duration < 0


@dataclass
class Task:
    task_id: int
    session_id: int
    images: list[str]
    describer: str
    target: str
    score: float | str
    time_used: float | str
    turn_transitions: list[TurnTransition]
    turns: list[Turn]
    ipus: list[IPU]
    wavs: Mapping[str, Path | str]
    start: float
    duration: float
    text: str = field(init=False)

    def __post_init__(self) -> None:
        self.score = float(self.score)
        self.time_used = float(self.time_used)
        self.wavs = {k: Path(v) for k, v in self.wavs.items()}
        self.ipus = sorted(self.ipus, key=lambda x: x.start) if self.ipus else []
        self.text = self._build_text()

    def _build_text(self) -> str:
        if not self.ipus:
            return ""
        return "\n\t" + "\n\t".join([str(ipu) for ipu in self.ipus])

    def __str__(self) -> str:
        return (
            f"[Task {self.task_id:02d} ({self.describer}) {self.start:.02f}:{self.start + self.duration:.02f} ] Turns {len(self.turns)} IPUs {len(self.ipus)}\n\t"
            + "\n\t".join([str(turn) for turn in self.turns])
            + "\n\t"
            + "\n\t".join([str(ipu) for ipu in self.ipus])
            + "\n"
        )

    def __repr__(self) -> str:
        return f"[Task {self.task_id:02d} ({self.describer}) {self.start:.02f}:{self.start + self.duration:.02f} ] Turns {len(self.turns)} IPUs {len(self.ipus)}"


_SESSION_MISSING = object()


@dataclass(frozen=True, init=False)
class Session:
    session_id: int
    subject_a: str
    subject_b: str
    tasks: list[Task]
    batch: int | None = None

    # Class-level storage (outside the dataclass fields)
    _all_sessions: ClassVar[dict[int, "Session"]] = {}

    def __init__(
        self,
        session_id: int,
        *args: object,
        batch: int | None | object = _SESSION_MISSING,
        subject_a: str | object = _SESSION_MISSING,
        subject_b: str | object = _SESSION_MISSING,
        tasks: list[Task] | object = _SESSION_MISSING,
    ) -> None:
        if len(args) > 4:
            raise TypeError(f"Session() takes from 4 to 5 positional arguments but {len(args) + 1} were given")

        values = {
            "batch": batch,
            "subject_a": subject_a,
            "subject_b": subject_b,
            "tasks": tasks,
        }

        positional_names: tuple[str, ...]
        if len(args) == 3 and all(
            values[name] is _SESSION_MISSING for name in ("batch", "subject_a", "subject_b", "tasks")
        ):
            positional_names = ("subject_a", "subject_b", "tasks")
        else:
            positional_names = ("batch", "subject_a", "subject_b", "tasks")

        for name, value in zip(positional_names, args):
            if values[name] is not _SESSION_MISSING:
                raise TypeError(f"Session() got multiple values for argument '{name}'")
            values[name] = value

        missing_args = [name for name in ("subject_a", "subject_b", "tasks") if values[name] is _SESSION_MISSING]
        if missing_args:
            missing_str = ", ".join(f"'{name}'" for name in missing_args)
            raise TypeError(f"Session() missing required arguments: {missing_str}")

        if values["batch"] is _SESSION_MISSING:
            values["batch"] = None

        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "batch", values["batch"])
        object.__setattr__(self, "subject_a", values["subject_a"])
        object.__setattr__(self, "subject_b", values["subject_b"])
        object.__setattr__(self, "tasks", values["tasks"])
        self.__post_init__()

    def __post_init__(self) -> None:
        # Register this session
        Session._all_sessions[self.session_id] = self

    @classmethod
    def get_session_by_id(cls, session_id: int) -> "Session | None":
        return cls._all_sessions.get(session_id)

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the sessions registry."""
        cls._all_sessions.clear()

    def __str__(self) -> str:
        return f"[Session {self.session_id} ({self.subject_a}, {self.subject_b})] (tasks_count: {len(self.tasks)})"

    def __repr__(self) -> str:
        return f"[Session {self.session_id} ({self.subject_a}, {self.subject_b})] (tasks_count: {len(self.tasks)})"


@dataclass
class BatchConfig:
    """Configuration for a specific batch of the corpus (used by UBA Spanish Games Corpus)."""

    batch_num: int
    heldout_tasks: set[tuple[int, int]]
    heldout_sessions: set[int]

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
