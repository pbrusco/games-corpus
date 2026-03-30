"""Plot the first minute of pitch for the first task of each corpus, all in one figure."""

import logging

import matplotlib.pyplot as plt
import seaborn as sns
from games_corpus import SpanishGamesCorpus, EnglishGamesCorpus, SlovakGamesCorpus


def plot_pitch(ax, features, label, color):
    """Plot pitch time series for both speakers, relative to task start."""
    t0 = features["time"].iloc[0]
    time = features["time"] - t0

    mask = time <= 60
    time = time[mask]

    for speaker, linestyle in [("A", "-"), ("B", "--")]:
        col = f"pitch_standardized_{speaker}"
        pitch = features[col][mask]
        ax.plot(time, pitch, linestyle=linestyle, color=color, alpha=0.7, label=f"{label} {speaker}")


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

    fig, ax = plt.subplots(figsize=(14, 5))

    for (label, corpus, task), color in zip(corpora, palette):
        features = corpus.get_features(task)
        plot_pitch(ax, features, label, color)
        logging.info(f"{label}: session {task.session_id}, task {task.task_id} ({features.shape[0]} frames)")

    ax.set_xlabel("Time from task start (s)")
    ax.set_ylabel("Pitch (z-scored)")
    ax.set_title("Pitch contour - first minute of first task per corpus")
    ax.set_xlim(0, 60)
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    sns.despine()
    plt.tight_layout()
    plt.savefig("pitch_all_corpora.png", dpi=150)
    print("Saved pitch_all_corpora.png")
    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
