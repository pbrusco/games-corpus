from games_corpus import EnglishGamesCorpus
import logging
from collections import defaultdict


def main():
    corpus = EnglishGamesCorpus()
    corpus.load(load_audio=False, features_path="features/games-english")

    print(f"Loaded {len(corpus.sessions)} sessions")

    # Show first session's first task
    for session_id, session in corpus.sessions.items():
        print(f"\nSession {session_id}: {len(session.tasks)} tasks")
        if session.tasks:
            task = session.tasks[0]
            print(f"  Task {task.task_id}: {task.describer} describing '{task.target}'")
            print(f"  Score: {task.score}, Duration: {task.duration:.2f}s")

            if task.turn_transitions:
                print(f"\n  Turn transitions ({len(task.turn_transitions)}):")
                for transition in task.turn_transitions[:5]:
                    print(f"    {transition.label_type.name:20} | {transition.ipu_from} -> {transition.ipu_to}")
                if len(task.turn_transitions) > 5:
                    print(f"    ... and {len(task.turn_transitions) - 5} more")

            if task.turns:
                print(f"\n  Turns ({len(task.turns)}):")
                for turn in task.turns[:3]:
                    print(f"    {turn}")
                if len(task.turns) > 3:
                    print(f"    ... and {len(task.turns) - 3} more")
        break

    # Label distribution across all sessions
    counts = defaultdict(int)
    total_tasks = 0
    for session in corpus.sessions.values():
        for task in session.tasks:
            total_tasks += 1
            for transition in task.turn_transitions:
                counts[transition.label] += 1

    print(f"\nTotal tasks: {total_tasks}")
    print("Transition label distribution:", sorted(counts.items(), key=lambda x: x[0]))

    # Features example
    task = list(corpus.sessions.values())[0].tasks[0]
    features = corpus.get_features(task)
    print(f"\nFeatures for session {task.session_id}, task {task.task_id}:")
    print(f"  Shape: {features.shape}")
    print(f"  Columns: {list(features.columns)}")
    print(f"  Time range: {features['time'].min():.2f}s - {features['time'].max():.2f}s")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
