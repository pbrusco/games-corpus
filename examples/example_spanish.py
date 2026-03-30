"""Example: loading and exploring the UBA Spanish Games Corpus."""

import logging
from collections import Counter

from games_corpus import SpanishGamesCorpus


def main():
    corpus = SpanishGamesCorpus()
    corpus.load(
        load_audio=False,
        features_path={1: "features/games-spanish-batch1", 2: "features/games-spanish-batch2"},
    )

    # --- Corpus overview ---
    print("=== UBA Spanish Games Corpus ===\n")
    for batch in [1, 2]:
        sessions = corpus.get_sessions_by_batch(batch)
        dev = list(corpus.dev_tasks(batch=batch))
        held_out = list(corpus.held_out_tasks(batch=batch))
        print(f"Batch {batch}: {len(sessions)} sessions, {len(dev)} dev tasks, {len(held_out)} eval tasks")

    # --- First task detail ---
    task = next(corpus.dev_tasks(batch=1))
    print(f"\n=== Task {task.task_id} (Session {task.session_id}) ===")
    print(f"  Describer: {task.describer}")
    print(f"  Target:    {task.target}")
    print(f"  Score:     {task.score}")
    print(f"  Duration:  {task.duration:.2f}s")

    # --- Turns ---
    print(f"\n  Turns ({len(task.turns)}):")
    for turn in task.turns[:5]:
        print(f"    {turn}")
    if len(task.turns) > 5:
        print(f"    ... and {len(task.turns) - 5} more")

    # --- Turn transitions ---
    print(f"\n  Turn transitions ({len(task.turn_transitions)}):")
    for tt in task.turn_transitions[:5]:
        print(f"    {tt.label_type.name:20} | {tt.ipu_from} -> {tt.ipu_to}")
    if len(task.turn_transitions) > 5:
        print(f"    ... and {len(task.turn_transitions) - 5} more")

    # --- Label distribution ---
    print("\n=== Transition Label Distribution ===\n")
    for batch in [1, 2]:
        dev_counts = Counter()
        for task in corpus.dev_tasks(batch=batch):
            for tt in task.turn_transitions:
                dev_counts[tt.label] += 1
        print(f"Batch {batch} dev: {dict(sorted(dev_counts.items()))}")

    # --- Features ---
    print("\n=== Pre-extracted Features ===\n")
    for batch in [1, 2]:
        task = next(corpus.dev_tasks(batch=batch))
        features = corpus.get_features(task)
        print(
            f"Batch {batch}, session {task.session_id}, task {task.task_id}: "
            f"{features.shape[0]} frames, "
            f"time {features['time'].min():.2f}s - {features['time'].max():.2f}s"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
