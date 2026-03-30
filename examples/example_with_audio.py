"""Example: audio analysis and visualization for the Spanish Games Corpus."""

import logging

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from games_corpus import SpanishGamesCorpus


def plot_audio_and_features(y, sr, title="", turns=None, task_start=0):
    """Visualize audio waveform, mel spectrogram, and MFCCs with turn boundaries."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)

    fig, axs = plt.subplots(3, 1, figsize=(14, 8))
    fig.suptitle(title, fontsize=13)

    # Waveform
    librosa.display.waveshow(y, sr=sr, ax=axs[0])
    axs[0].set_title("Waveform")

    # Turn boundaries
    if turns:
        palette = sns.color_palette("husl", n_colors=len(turns))
        for i, turn in enumerate(turns):
            turn_start = turn.start - task_start
            turn_end = turn.end - task_start
            color = palette[i % len(palette)]

            for ax in axs:
                ax.axvline(x=turn_start, color=color, linestyle="--", alpha=0.5)
                ax.axvline(x=turn_end, color=color, linestyle="--", alpha=0.5)

            mid = (turn_start + turn_end) / 2
            text = " ".join(ipu.text for ipu in turn.ipus)
            axs[0].text(mid, axs[0].get_ylim()[1], f"Turn {i + 1}", color=color, ha="center", va="bottom", fontsize=8)
            axs[0].text(mid, axs[0].get_ylim()[0], text, color=color, ha="center", va="top", rotation=45, fontsize=7)

    # Mel spectrogram
    librosa.display.specshow(librosa.power_to_db(mel_spec, ref=np.max), y_axis="mel", x_axis="time", sr=sr, ax=axs[1])
    axs[1].set_title("Mel Spectrogram")

    # MFCCs
    librosa.display.specshow(mfcc, x_axis="time", ax=axs[2])
    axs[2].set_title("MFCCs")

    plt.tight_layout()
    return fig


def plot_stereo_and_transitions(y_a, y_b, sr, title="", transitions=None, task_start=0):
    """Visualize stereo audio and turn transitions between speakers."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
    fig.suptitle(title, fontsize=13)

    librosa.display.waveshow(y_a, sr=sr, ax=ax1)
    librosa.display.waveshow(y_b, sr=sr, ax=ax2)
    ax1.set_title("Speaker A")
    ax2.set_title("Speaker B")

    if transitions:
        colors = {"S": "green", "BC": "blue", "PI": "red", "O": "purple", "I": "orange"}

        for trans in transitions:
            if not trans.turn_from:
                continue

            # Shade turns
            for turn, speaker in [(trans.turn_from, trans.speaker_from), (trans.turn_to, trans.speaker_to)]:
                ax = ax1 if speaker == "A" else ax2
                ax.axvspan(turn.start - task_start, turn.end - task_start, alpha=0.08, color="gray")

            # Transition label
            color = colors.get(trans.label, "gray")
            start_t = trans.ipu_from.end - task_start
            end_t = trans.ipu_to.start - task_start
            mid = (start_t + end_t) / 2
            y_pos = -0.5 if trans.speaker_from == "A" else 0.5
            target_ax = ax1 if trans.speaker_from == "A" else ax2
            target_ax.text(
                mid,
                y_pos,
                f"{trans.label}\n{abs(trans.transition_duration):.2f}s",
                color=color,
                ha="center",
                va="center",
                fontsize=7,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
            )

        legend_handles = [plt.Line2D([0], [0], color=c, label=label) for label, c in colors.items()]
        ax1.legend(handles=legend_handles, loc="upper right", fontsize=8)

    sns.despine()
    plt.tight_layout()
    return fig


def main():
    sns.set_theme(style="whitegrid", context="notebook")

    corpus = SpanishGamesCorpus()
    corpus.load(load_audio=True)

    task = next(corpus.dev_tasks(batch=1))

    print(f"\n=== Analyzing Task {task.task_id} (Session {task.session_id}) ===")
    print(f"  Describer:  {task.describer}")
    print(f"  Target:     {task.target}")
    print(f"  Score:      {task.score}")
    print(f"  Duration:   {task.duration:.2f}s")
    print(f"  Speakers:   {list(task.wavs.keys())}")

    audio = {}
    for speaker, wav_path in task.wavs.items():
        y, sr = librosa.load(wav_path)
        start = int(task.start * sr)
        end = int((task.start + task.duration) * sr)
        y_task = y[start:end]
        audio[speaker] = y_task

        # Extract features
        mfccs = librosa.feature.mfcc(y=y_task, sr=sr, n_mfcc=13)
        spectral_centroid = librosa.feature.spectral_centroid(y=y_task, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y_task)

        print(f"\n  Speaker {speaker}:")
        print(f"    Sample rate:    {sr} Hz")
        print(f"    Duration:       {len(y_task) / sr:.2f}s")
        print(f"    MFCCs shape:    {mfccs.shape}")
        print(f"    Spectral centroid (mean): {np.mean(spectral_centroid):.2f}")
        print(f"    Zero crossing rate (mean): {np.mean(zcr):.2f}")

        # Per-speaker plot
        speaker_turns = [t for t in task.turns if t.speaker == speaker]
        plot_audio_and_features(
            y_task,
            sr,
            title=f"Task {task.task_id} - Speaker {speaker} ({task.describer} describing '{task.target}')",
            turns=speaker_turns,
            task_start=task.start,
        )
        plt.show()

    # Stereo visualization
    if "A" in audio and "B" in audio:
        plot_stereo_and_transitions(
            audio["A"],
            audio["B"],
            sr,
            title=f"Task {task.task_id} - Stereo View (Session {task.session_id})",
            transitions=task.turn_transitions,
            task_start=task.start,
        )
        plt.show()

    # Transition statistics
    print("\n=== Turn Transition Analysis ===")
    stats = {}
    for trans in task.turn_transitions:
        s = stats.setdefault(trans.label, {"count": 0, "total_dur": 0.0, "overlaps": 0})
        s["count"] += 1
        s["total_dur"] += trans.transition_duration
        if trans.overlapped_transition:
            s["overlaps"] += 1

    for label, s in stats.items():
        avg = s["total_dur"] / s["count"]
        overlap_pct = (s["overlaps"] / s["count"]) * 100
        print(f"\n  {label}: {s['count']} transitions, avg duration {avg:.3f}s, {overlap_pct:.0f}% overlapped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
