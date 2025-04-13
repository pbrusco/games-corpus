# UBA Games Corpus

A Python library for working with the UBA Games Corpus, a collection of Spanish dialogues from task-oriented, collaborative interactions.

## Installation

```bash
pip install -r requirements.txt
```

## Examples

The repository includes two example scripts:

### Basic Usage
Run the basic example to see how to load and process the corpus:

```bash
python example.py
```

This shows:
- Loading the corpus
- Accessing sessions and tasks 
- Examining turn transitions
- Basic corpus statistics

### Audio Analysis
Run the audio visualization example:

```bash
python example_with_audio.py
```

This demonstrates:
- Loading and processing audio files
- Visualizing waveforms and spectrograms
- Analyzing turn transitions with audio
- Stereo visualization of conversations between speakers
- Audio feature extraction (MFCCs, spectral centroid, etc.)

## Requirements
- librosa
- matplotlib
- numpy
- soundfile
- pytest (for tests)

## Usage

Basic example of loading and accessing the corpus:

```python
from games_corpus import SpanishGamesCorpusDialogues

# Initialize and load the corpus
corpus = SpanishGamesCorpusDialogues()
corpus.load(
    # url="https://custom-url.com/{filename}",  # optional custom URL
    # local_path="./data",  # optional local path
    load_audio=False  # set to True if you need audio files
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

## Project Structure

```
games-corpus/
├── games_corpus/
│   ├── __init__.py
│   ├── games_corpus.py        # Main corpus class and data loading
│   ├── games_corpus_types.py  # Data classes for corpus elements
│   └── games_corpus_parsers.py # File parsing and data extraction
├── tests/
│   └── games_corpus_tests.py  # Comprehensive test suite
├── examples/
│   └── example.py            # Usage examples
└── data/                     # Optional local data directory
    ├── b1-dialogue-tasks/    # Batch 1 task information
    ├── b1-dialogue-turns/    # Batch 1 turn annotations
    ├── b2-dialogue-tasks/    # Batch 2 task information
    └── b2-dialogue-turns/    # Batch 2 turn annotations
```

## Data Structure

The corpus is organized into:

- **Batches**: Collection of sessions (currently batches 1 and 2)
- **Sessions**: Individual recording sessions between two participants
- **Tasks**: Game tasks within each session, including:
  - Task ID and Session ID
  - Images used in the task
  - Describer role assignment
  - Target image
  - Score and completion time
- **Turns**: Speaking turns with timing information
- **IPUs**: Inter-Pausal Units containing words and timing
- **Words**: Individual words with timing and speaker information
- **TurnTransitions**: Annotated turn-taking patterns between speakers:
  - `S`: Smooth switch
  - `O`: Overlap
  - `I`: Interruption
  - `BC`: Backchannel
  - `BC_O`: Overlapping backchannel
  - `BI`: Backchannel with interruption
  - `PI`: Pause interruption
  - `X1/X2/X2_O/X3`: First turn, Backchannel Continuation (with and without overlap), Simulaneuos speech. 

### Corpus Statistics

**Batch 1:**
- Development set: 132 tasks
- Evaluation set: 64 tasks
- Turn transition distribution:
  Development set:
  - Smooth switches (S): 1,466
  - Backchannels (BC): 565
  - Overlapping backchannels (BC_O): 57
  - Backchannel interruptions (BI): 61
  - Interruptions (I): 151
  - Overlaps (O): 491
  - Pause interruptions (PI): 196
  - First turns (X1): 126
  - Backchannel continuations (X2): 464
  - Overlapping continuations (X2_O): 48
  - Simultaneous speech (X3): 352

  Evaluation set:
  - Smooth switches (S): 577
  - Backchannels (BC): 278
  - Overlapping backchannels (BC_O): 29
  - Backchannel interruptions (BI): 22
  - Interruptions (I): 41
  - Overlaps (O): 173
  - Pause interruptions (PI): 60
  - First turns (X1): 61
  - Backchannel continuations (X2): 232
  - Overlapping continuations (X2_O): 24
  - Simultaneous speech (X3): 136

**Batch 2:**
- Development set: 172 tasks
- Evaluation set: 47 tasks

## Advanced Usage Examples

### Working with Tasks and Turns

```python
from games_corpus import SpanishGamesCorpusDialogues

corpus = SpanishGamesCorpusDialogues()
corpus.load(load_audio=False)

# Get development tasks for analysis
dev_tasks = list(corpus.dev_tasks(batch=1))

# Analyze turn transitions in a task
task = dev_tasks[0]
for transition in task.turn_transitions:
    print(f"Transition type: {transition.type}")
    print(f"From speaker: {transition.from_turn.speaker}")
    print(f"To speaker: {transition.to_turn.speaker}")
    print(f"Gap duration: {transition.gap_duration:.2f}s")

# Access word-level information
for ipu in task.ipus:
    for word in ipu.words:
        print(f"{word.speaker}: {word.text} [{word.start:.2f}s - {word.end:.2f}s]")
```

### Working with Sessions

```python
# Get all sessions from batch 1
batch1_sessions = corpus.get_sessions_by_batch(1)

# Analyze participant interactions
for session_id, session in batch1_sessions.items():
    print(f"\nSession {session_id}:")
    print(f"Participants: {session.subject_a} and {session.subject_b}")
    print(f"Number of tasks: {len(session.tasks)}")
    
    # Calculate session statistics
    total_score = sum(task.score for task in session.tasks)
    avg_duration = sum(task.time_used for task in session.tasks) / len(session.tasks)
    print(f"Average task duration: {avg_duration:.2f}s")
    print(f"Total score: {total_score}")
```

## Features

- Load corpus data from remote URL or local path
- Access session and task metadata
- Extract turn-taking patterns and transitions
- Process word-level timing information
- Optional audio file handling
- Development and held-out task splits

## Testing

Run the test suite:

```bash
pytest games_corpus_tests.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this corpus in your research, please cite the following paper:

```bibtex
@techreport{gravano2023uba,
  title={Uba games corpus},
  author={Gravano, Agust{\i}n and Kamienkowski, Juan E and Brusco, Pablo},
  year={2023},
  institution={Tech. Rep., Consejo Nacional de Investigaciones Cient{\'\i}ficas y T{\'e}cnicas~…}
}
```

For detailed information about the corpus and its annotations, please refer to the [paper](https://ri.conicet.gov.ar/handle/11336/191235).
