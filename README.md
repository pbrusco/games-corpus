# Games Corpus

A Python library for working with collaborative dialogue game corpora:

- **UBA Spanish Games Corpus** — Spanish dialogues, automatically downloaded from CONICET
- **Columbia English Games Corpus** — English dialogues, requires manual download
- **Slovak Games Corpus** — Slovak dialogues, requires manual download

## Installation

### For users

```bash
pip install games-corpus
```

### For developers

This project uses [uv](https://docs.astral.sh/uv/) for development. If you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone and set up:

```bash
git clone https://github.com/pbrusco/games-corpus.git
cd games-corpus
uv sync
```

This creates a virtual environment and installs all dependencies (including dev tools and audio libraries). Run scripts with `uv run`:

```bash
uv run python examples/example_spanish.py
```

### Troubleshooting: SSL certificate error on macOS

If you see `SSL: CERTIFICATE_VERIFY_FAILED` when downloading the Spanish corpus, set the `SSL_CERT_FILE` environment variable:

```bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
```

## Examples

Full example scripts are available in the [examples/](https://github.com/pbrusco/games-corpus/tree/main/examples) directory on GitHub.

### Spanish Corpus

```bash
uv run python examples/example_spanish.py
```

### English Corpus

First, download the Columbia Games Corpus manually and place it in `corpus/games-english/`. Then:

```bash
uv run python examples/example_english.py
```

### Slovak Corpus

Download the Slovak Games Corpus manually and place it in `corpus/games-slovak/`. Then:

```bash
uv run python examples/example_slovak.py
```

### Audio Analysis (Spanish)

```bash
uv run python examples/example_with_audio.py
```

## Usage

### Spanish Corpus

```python
from games_corpus import SpanishGamesCorpus

corpus = SpanishGamesCorpus()
corpus.load(
    load_audio=False,
    features_path={1: "features/games-spanish-batch1", 2: "features/games-spanish-batch2"},
)

# Get all sessions from batch 1
batch1_sessions = corpus.get_sessions_by_batch(1)
print(f"Found {len(batch1_sessions)} sessions in batch 1")

# Access development tasks
for task in corpus.dev_tasks(batch=1):
    print(f"Task {task.task_id} from session {task.session_id}")
    print(f"  Describer: {task.describer}")
    print(f"  Score: {task.score}")
```

### English Corpus

```python
from games_corpus import EnglishGamesCorpus

corpus = EnglishGamesCorpus()
corpus.load(load_audio=False, features_path="features/games-english")

for session_id, session in corpus.sessions.items():
    print(f"Session {session_id}: {len(session.tasks)} tasks")
```

### Slovak Corpus

```python
from games_corpus import SlovakGamesCorpus

corpus = SlovakGamesCorpus()
corpus.load(load_audio=False, features_path="features/games-slovak")

for session_id, session in corpus.sessions.items():
    print(f"Session {session_id}: {len(session.tasks)} tasks")
```

## Project Structure

```
games-corpus/
├── games_corpus/              # Python package
│   ├── __init__.py            # Public API
│   ├── types.py               # Shared data types (Word, IPU, Turn, Task, Session)
│   ├── parsers.py             # Shared file parsers
│   ├── spanish.py             # SpanishGamesCorpus
│   ├── english.py             # EnglishGamesCorpus
│   ├── slovak.py              # SlovakGamesCorpus
│   ├── features.py            # Pre-extracted features loader
│   ├── downloader.py          # Remote file downloader (Spanish only)
│   ├── punctuation.py         # Machine-restored punctuation, generic (NOT human annotation)
│   └── data/punctuated_phrases/{corpus-slug}/  # Shipped pilot data, per corpus
├── features/                  # Pre-extracted acoustic features (Git LFS)
│   ├── games-english/
│   ├── games-spanish-batch1/
│   ├── games-spanish-batch2/
│   └── games-slovak/
├── examples/
│   ├── example_spanish.py     # Spanish corpus example
│   ├── example_english.py     # English corpus example
│   ├── example_slovak.py      # Slovak corpus example
│   ├── example_all_pitch.py   # Cross-corpus pitch comparison plot
│   └── example_with_audio.py  # Audio analysis example
├── tests/                     # Test suite
└── scripts/                   # Praat visualization scripts
```

## Data Structure

All three corpora share the same data model:

- **Sessions**: Individual recording sessions between two participants (A and B)
- **Tasks**: Collaborative game tasks within each session (describer, target image, score, timing)
- **Turns**: Speaking turns with timing information
- **IPUs**: Inter-Pausal Units (continuous speech segments separated by pauses)
- **Words**: Individual words with timing and speaker information
- **TurnTransitions**: Annotated turn-taking patterns between speakers (`tt.label`, following Gravano & Hirschberg 2011):
  - `S`: Smooth switch
  - `O`: Overlap (smooth switch with overlapping speech)
  - `PI`: Pause interruption
  - `I`: Interruption (with overlapping speech)
  - `BI`: Butting-in (failed interruption: the interlocutor does not get the floor)
  - `BC`: Backchannel
  - `BC_O`: Overlapping backchannel
  - `X1/X2/X2_O/X3`: First turn, Backchannel Continuation (with and without overlap), Simultaneous start.

  Each transition also exposes its **type without the overlap dimension**, `tt.kind` (see below).

The Spanish corpus additionally organizes sessions into **batches** (batch 1 and batch 2), with predefined development/evaluation splits accessible via `corpus.dev_tasks(batch)` and `corpus.held_out_tasks(batch)`.

### Corpus Overview

| Corpus | Language | Sessions | Tasks | Loading | Features |
|--------|----------|----------|-------|---------|----------|
| Spanish (UBA) | Argentine Spanish | 24 (2 batches) | 415 | Auto-download | Included (LFS) |
| English (Columbia) | English | 12 | 168 | Manual | Included (LFS) |
| Slovak | Slovak | 9 | 122 | Manual | Included (LFS) |

## Advanced Usage

### Working with Tasks and Turns

This works with any of the three corpora:

```python
# Analyze turn transitions in a task
task = list(corpus.sessions.values())[0].tasks[0]
for transition in task.turn_transitions:
    print(f"Transition type: {transition.label_type}")
    print(f"From speaker: {transition.turn_from.speaker if transition.turn_from else 'N/A'}")
    print(f"To speaker: {transition.turn_to.speaker}")
    # transition_duration is signed: positive = silence gap, negative = overlap
    # magnitude. Check overlapped_transition rather than the sign yourself.
    if transition.overlapped_transition:
        print(f"Overlap duration: {abs(transition.transition_duration):.2f}s")
    else:
        print(f"Gap duration: {transition.transition_duration:.2f}s")

# Access word-level information
for ipu in task.ipus:
    for word in ipu.words:
        print(f"{word.speaker}: {word.text} [{word.start:.2f}s - {word.end:.2f}s]")
```

### Transition kind and overlap as separate dimensions

The original labels mix two things: what happened to the floor, and whether there was
overlapping speech (`S` vs `O`, `PI` vs `I`, ...). `tt.kind` (a `TurnTransitionKind`,
available for all three corpora) keeps only the first, named after what happens to the
floor; the overlap is a separate attribute:

| `tt.kind` | original labels | what happens to the floor |
|---|---|---|
| `yield` | `S`, `O` | the speaker completes their utterance and the interlocutor takes the floor |
| `take` | `PI`, `I` | the interlocutor takes the floor before the speaker completes their utterance |
| `failed_take` | `BI` | the interlocutor tries to take the floor; the speaker keeps it |
| `backchannel` | `BC`, `BC_O` | brief listener signal; the speaker keeps the floor |
| `resume` | `X2`, `X2_O` | the speaker continues after a backchannel |
| `first_turn` / `simultaneous_start` / `ambiguous` | `X1` / `X3` / `A` | unchanged |

The kind values deliberately never reuse an original code (a `take` is a `PI` *or* an
`I`; calling it `I` would silently change what `I` means). In Gravano & Hirschberg's
terms, turn-yielding, turn-holding and backchannel-inviting cues are the signals that
precede these outcomes.

There are two notions of overlap, and they do not always agree:

- `tt.annotated_overlap`: the annotators' call, read off the label (`O`, `I`, `BI`,
  `BC_O`, `X2_O` → `True`; `X1`, `X3`, `A` → `None`).
- `tt.overlapped_transition`: computed from timestamps (the interlocutor's first IPU
  starts before the speaker's last IPU ends).

They agree on 99.0% (Spanish), 99.8% (English) and 99.8% (Slovak) of transitions. Two
details of how transitions are linked matter for this:

- An IPU belongs to a turn when they substantially overlap in time (at least half of the IPU
  or half of the turn), so an IPU of the speaker's next turn that starts a few ms after the
  turn ends is not counted in it.
- A transition comes from the interlocutor's most recent turn, except when that turn is a
  simultaneous start (annotated `X3`) that began less than 200 ms earlier: both speakers
  started at almost the same time, and the transition is linked to the interlocutor's
  previous turn, as the annotators did.

`(kind, annotated_overlap)`
rebuilds the original label exactly:

```python
from games_corpus import TurnTransitionKind, TurnTransitionType

tt.kind                        # TurnTransitionKind.TAKE
tt.annotated_overlap           # True  (it was an I, not a PI)
tt.overlapped_transition       # computed from timestamps
TurnTransitionType.from_kind(tt.kind, tt.annotated_overlap)  # TurnTransitionType.OVERLAPPED_INTERRUPTION
```

### Pre-extracted Acoustic Features

Pre-extracted features (pitch, jitter, shimmer, HNR, intensity, VAD) can be downloaded automatically from GitHub Releases:

```python
from games_corpus import EnglishGamesCorpus

corpus = EnglishGamesCorpus()
corpus.load(local_path="corpus/games-english")
corpus.download_features()  # downloads to features/games-english/

task = corpus.sessions[1].tasks[0]
df = corpus.get_features(task)
# df.columns: time, pitch_standardized_A, jitter_standardized_A, ..., vad_B
print(df.shape)  # (1555, 13) — one row per 10ms frame
```

Works the same for all corpora:

```python
corpus.download_features()  # downloads once, skips if already present
df = corpus.get_features(task)
```

Alternatively, pass `features_path` to `load()` if you have features in a custom location:

```python
corpus.load(features_path="my/custom/path")
```

Features are available per task at 100 Hz (10ms frames) with z-score standardized measurements for both speakers: pitch, jitter, shimmer, log HNR, intensity, and VAD.

### Spanish-Specific: Dev/Eval Splits

The Spanish corpus has predefined development and evaluation splits per batch:

```python
from games_corpus import SpanishGamesCorpus

corpus = SpanishGamesCorpus()
corpus.load(load_audio=False)

for task in corpus.dev_tasks(batch=1):
    print(f"Task {task.task_id}, session {task.session_id}")
```

### Machine-Restored Punctuation (pilot, not human annotation)

`get_punctuated_phrases` / `available_punctuated_sessions` are generic on
`BaseGamesCorpus` — they work the same way for all three corpora — but only
the Spanish corpus has any sessions processed so far.

> **Warning:** the source transcripts have no punctuation or capitalization at
> all (ASR-style). `get_punctuated_phrases` returns punctuation predicted by
> an LLM (Gemini, given the session audio + original transcript), **not**
> produced or checked by any corpus's human annotators. It's a noisy
> pseudo-label meant to recover information the plain transcript hides (e.g.
> a bare "sí" answering a real question vs. just a backchannel — only a
> restored "¿...?" tells them apart), not ground truth. Punctuation, casing,
> **and diacritics/accents** may all be added or corrected — "buho" → "búho"
> is a deliberate orthography fix, not a wording change. See
> `games_corpus.punctuation`'s module docstring for details on the fidelity
> check, its known ~2-7%-per-file disfluency-cleanup noise rate, and its
> limits. `available_punctuated_sessions()` lists what's covered for a given
> corpus; anything else raises `FileNotFoundError`.

```python
from games_corpus import SpanishGamesCorpus

corpus = SpanishGamesCorpus()
corpus.load(load_audio=False)

print(corpus.available_punctuated_sessions())  # currently: batch 1, sessions 1-14

task = next(t for t in corpus.dev_tasks(batch=1) if t.session_id == 2)
for phrase in corpus.get_punctuated_phrases(task):
    print(f"{phrase.speaker} [{phrase.start:.2f}-{phrase.end:.2f}] {phrase.text}")
```

## Library Features

- Unified data model across three corpora (Spanish, English, Slovak)
- Shared turn-transition annotation scheme (S, O, I, BC, PI, X1, X2, X3, etc.)
- Word-level and phrase-level timing information
- Pre-extracted acoustic features (pitch, jitter, shimmer, HNR, intensity, VAD)
- Optional audio file handling
- Dev/eval task splits (Spanish corpus)
- Machine-restored punctuation pilot, generic across corpora (currently Spanish only has data — NOT human annotation, see warning above)

## Testing

Run the test suite:

```bash
uv run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use the **Spanish corpus** in your research, please cite:

```bibtex
@techreport{gravano2023uba,
  title={Uba games corpus},
  author={Gravano, Agust{\i}n and Kamienkowski, Juan E and Brusco, Pablo},
  year={2023},
  institution={Tech. Rep., Consejo Nacional de Investigaciones Cient{\'\i}ficas y T{\'e}cnicas~…}
}
```

For detailed information about the Spanish corpus and its annotations, refer to the [paper](https://ri.conicet.gov.ar/handle/11336/191235).

For the **English** and **Slovak** corpora, please refer to their respective original publications.
