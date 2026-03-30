"""Plot the first minute of pitch for the first task of each corpus, split by speaker."""

import logging

import matplotlib.pyplot as plt
import seaborn as sns
from games_corpus import SpanishGamesCorpus, EnglishGamesCorpus, SlovakGamesCorpus


def main():
    sns.set_theme(style="whitegrid", context="notebook", palette="colorblind")

    # Load all corpora with features
    spanish = SpanishGamesCorpus()
    spanish.load(
        load_audio=False,
        features_path={1: "features/games-spanish-batch1", 2: "features/games-spanish-batch2"},
    )

    english = EnglishGamesCorpus()
    english.load(load_audio=False, features_path="features/games-english")

    slovak = SlovakGamesCorpus()
    slovak.load(load_audio=False, features_path="features/games-slovak")

    corpora = [
        ("Spanish B1", spanish, next(spanish.dev_tasks(batch=1))),
        ("Spanish B2", spanish, next(spanish.dev_tasks(batch=2))),
        ("English", english, list(english.sessions.values())[0].tasks[0]),
        ("Slovak", slovak, list(slovak.sessions.values())[0].tasks[0]),
    ]

    palette = sns.color_palette("colorblind", n_colors=4)

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

    for (label, corpus, task), color in zip(corpora, palette):
        features = corpus.get_features(task)
        t0 = features["time"].iloc[0]
        time = features["time"] - t0
        mask = time <= 60

        ax_a.plot(time[mask], features["pitch_standardized_A"][mask], color=color, alpha=0.7, label=label)
        ax_b.plot(time[mask], features["pitch_standardized_B"][mask], color=color, alpha=0.7, label=label)
        logging.info(f"{label}: session {task.session_id}, task {task.task_id} ({features.shape[0]} frames)")

    ax_a.set_ylabel("Pitch (z-scored)")
    ax_b.set_ylabel("Pitch (z-scored)")
    ax_b.set_xlabel("Time from task start (s)")

    ax_a.set_title("Speaker A (describer)", fontsize=12)
    ax_b.set_title("Speaker B (follower)", fontsize=12)

    ax_a.set_xlim(0, 60)
    ax_a.legend(loc="upper right", fontsize=9)
    ax_b.legend(loc="upper right", fontsize=9)

    fig.suptitle("Pitch contour — first minute of first task per corpus", fontsize=14, y=1.01)
    sns.despine()
    plt.tight_layout()
    plt.savefig("pitch_all_corpora.png", dpi=150, bbox_inches="tight")
    print("Saved pitch_all_corpora.png")
    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
