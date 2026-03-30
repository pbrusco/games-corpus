"""Example: loading and exploring the Columbia English Games Corpus."""

import logging
from collections import Counter

from games_corpus import EnglishGamesCorpus


def main():
    corpus = EnglishGamesCorpus()
    corpus.load(load_audio=False, features_path="features/games-english")

    # --- Corpus overview ---
    print("=== Columbia English Games Corpus ===\n")
    total_tasks = sum(len(s.tasks) for s in corpus.sessions.values())
    print(f"{len(corpus.sessions)} sessions, {total_tasks} tasks")

    # --- First task detail ---
    session = corpus.sessions[1]
    task = session.tasks[0]
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
    counts = Counter()
    for session in corpus.sessions.values():
        for task in session.tasks:
            for tt in task.turn_transitions:
                counts[tt.label] += 1
    print(dict(sorted(counts.items())))

    # --- Features ---
    print("\n=== Pre-extracted Features ===\n")
    task = corpus.sessions[1].tasks[0]
    features = corpus.get_features(task)
    print(f"Session {task.session_id}, task {task.task_id}: {features.shape[0]} frames, {features.shape[1]} columns")
    print(f"  Time range: {features['time'].min():.2f}s - {features['time'].max():.2f}s")
    print(f"  Columns: {', '.join(features.columns)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
