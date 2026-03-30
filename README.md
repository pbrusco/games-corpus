# Games Corpus

A Python library for working with collaborative dialogue game corpora:

- **UBA Spanish Games Corpus** — Spanish dialogues, automatically downloaded from CONICET
- **Columbia English Games Corpus** — English dialogues, requires manual download
- **Slovak Games Corpus** — Slovak dialogues, requires manual download

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. uv is a fast Python package manager that handles virtual environments, dependency resolution, and Python version management in a single tool.

### Install uv

If you don't have uv installed yet:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or with Homebrew
brew install uv
```

See the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for more options.

### Set up the project

```bash
uv sync
```

This creates a virtual environment, installs Python if needed, and installs all dependencies (including audio). That's it.

### Running scripts

Use `uv run` to execute scripts in the project environment (no need to activate anything):

```bash
uv run python examples/example_spanish.py
```

### Troubleshooting: SSL certificate error on macOS

If you see `SSL: CERTIFICATE_VERIFY_FAILED` when downloading the corpus, this is a known issue with Homebrew Python on macOS. Fix it by setting the `SSL_CERT_FILE` environment variable before running:

```bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
```

Or point directly to the Homebrew CA bundle:

```bash
export SSL_CERT_FILE=/opt/homebrew/etc/openssl@3/cert.pem
```

## Examples

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
│   └── downloader.py          # Remote file downloader (Spanish only)
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
- **TurnTransitions**: Annotated turn-taking patterns between speakers:
  - `S`: Smooth switch
  - `O`: Overlap
  - `I`: Interruption
  - `BC`: Backchannel
  - `BC_O`: Overlapping backchannel
  - `BI`: Backchannel with interruption
  - `PI`: Pause interruption
  - `X1/X2/X2_O/X3`: First turn, Backchannel Continuation (with and without overlap), Simultaneous speech.

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
    print(f"Gap duration: {transition.transition_duration:.2f}s")

# Access word-level information
for ipu in task.ipus:
    for word in ipu.words:
        print(f"{word.speaker}: {word.text} [{word.start:.2f}s - {word.end:.2f}s]")
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

## Library Features

- Unified data model across three corpora (Spanish, English, Slovak)
- Shared turn-transition annotation scheme (S, O, I, BC, PI, X1, X2, X3, etc.)
- Word-level and phrase-level timing information
- Pre-extracted acoustic features (pitch, jitter, shimmer, HNR, intensity, VAD)
- Optional audio file handling
- Dev/eval task splits (Spanish corpus)

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
