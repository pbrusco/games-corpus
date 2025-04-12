from games_corpus import SpanishGamesCorpusDialogues
import logging
from collections import defaultdict


def main():
    # Initialize the corpus
    corpus = SpanishGamesCorpusDialogues()

    # Load the corpus (optionally specify custom URL or local path)
    corpus.load(
        # url="https://custom-url.com/{filename}",  # optional custom URL
        # local_path="./data",  # optional custom path
        load_audio=False  # set to True if you need audio files
    )

    # Example 1: Get all sessions from batch 1
    batch1_sessions = corpus.get_sessions_by_batch(1)
    print(f"Found {len(batch1_sessions)} sessions in batch 1")

    # Example 2: Iterate through development tasks for batch 1
    for task in corpus.dev_tasks(batch=1):
        print(f"\nTask {task.task_id} from session {task.session_id}:")
        print(f"  Describer: {task.describer}")
        print(f"  Target: {task.target}")
        print(f"  Score: {task.score}")
        print(f"  Duration: {task.duration:.2f}s")
        break

    # Example 3: Access turn transitions
    for task in corpus.dev_tasks(batch=1):
        print(f"\nTurn transitions in task {task.task_id}:")
        for transition in task.turn_transitions:
            print(f"  {transition.label}: {transition.ipu_from} -> {transition.ipu_to}")
        break

    for task in corpus.dev_tasks(batch=1):
        print(f"\nTurn transitions in task {task.task_id}:")
        for transition in task.turn_transitions:
            print(f"  {transition.label}: {transition.turn_from} -> {transition.turn_to}")
        break


    ## Show an example of the turns inside a task:
    for task in corpus.dev_tasks(batch=1):
        print(f"\nTurns in task {task.task_id}:")
        for turn in task.turns:
            print(turn)
        break

    for batch in [1, 2]:
        dev_counts = defaultdict(int)
        eval_counts = defaultdict(int)
        dev_tasks = 0
        eval_tasks = 0
        for task in corpus.dev_tasks(batch=batch):
            dev_tasks += 1
            for transition in task.turn_transitions:

                dev_counts[transition.label] += 1

        for task in corpus.held_out_tasks(batch=batch):
            eval_tasks += 1
            for transition in task.turn_transitions:
                eval_counts[transition.label] += 1

        print(f"Dev set tasks: {dev_tasks}")
        print(f"Eval set tasks: {eval_tasks}")

        print("Dev labels:", sorted(dev_counts.items(), key=lambda x: x[0]))
        print("Eval labels:", sorted(eval_counts.items(), key=lambda x: x[0]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
