from games_corpus import SpanishGamesCorpusDialogues
import librosa

# Example usage
if __name__ == "__main__":

    games_corpus = SpanishGamesCorpusDialogues()
    games_corpus.load(load_audio=False, local_path="./uba_games_corpus/")
    # Example to access a specific session and task
    example_session_id = 1
    if example_session_id in games_corpus.sessions:
        example_session = games_corpus.sessions[example_session_id]
        print(
            f"\nExample Task in example Session {example_session_id}: {example_session}"
        )
        task = example_session.tasks[0]
        print(f"  Task {task.task_id}: {task.text} (Score: {task.score})")

    # Example to get sessions by batch
    batch_1_sessions = games_corpus.get_sessions_by_batch(1)
    print(f"\nBatch 1 Sessions: {batch_1_sessions}")

    # Note: The above code will load the corpus and print the sessions and tasks.
    # This is a simple demonstration of how to load and access the UBA Games Corpus.

    for task in games_corpus.dev_tasks(batch=1):
        print("FIRST TASK IN DEV SET", task)
        for transition in task.turn_transitions:
            print(
                f"  {transition.label}: {transition.ipu_from.text} -> {transition.ipu_to.text}"
            )
        break



    # Read the wav corresponding to the first task in the dev set and compute it's duration:
    # Will only work if the audio files are loaded
    if task.wavs:
        wavs_speaker_A = task.wavs["A"]
        print(f"Wav file for Task {task.task_id}: {wavs_speaker_A}")
        y, sr = librosa.load(
            wavs_speaker_A,
            sr=None,
            offset=task.start,
            duration=task.duration,
        )
        duration = librosa.get_duration(y=y, sr=sr)
        print(f"Duration of the task wav file: {duration:.2f} seconds")



    print(len(list(games_corpus.dev_tasks(batch=1))))
    print(len(list(games_corpus.held_out_tasks(batch=1))))

    for task in games_corpus.held_out_tasks(batch=1):
        print(task.session_id, task.task_id)

    print(len(list(games_corpus.held_out_tasks(batch=2))))