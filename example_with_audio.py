from games_corpus import SpanishGamesCorpusDialogues
import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt


def plot_audio_and_features(y, sr, title="", turns=None, task_start=0):
    """Helper function to visualize audio and its features"""
    # Calculate features
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)

    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(12, 8))
    fig.suptitle(title)

    # Plot waveform with turn boundaries
    librosa.display.waveshow(y, sr=sr, ax=axs[0])
    axs[0].set_title("Waveform")

    # Add turn boundaries if provided
    if turns:
        colors = ["r", "g", "b", "c", "m", "y"]  # Cycle through these colors
        for i, turn in enumerate(turns):
            # Convert turn times to plot coordinates
            turn_start = turn.start - task_start
            turn_end = turn.end - task_start
            color = colors[i % len(colors)]

            # Add vertical lines for turn boundaries in all subplots
            for ax in axs:
                ax.axvline(x=turn_start, color=color, linestyle="--", alpha=0.5)
                ax.axvline(x=turn_end, color=color, linestyle="--", alpha=0.5)

            # Add turn label and transcript
            mid_point = (turn_start + turn_end) / 2
            # Get turn text (remove the metadata part)
            turn_text = " ".join([ipu.text for ipu in turn.ipus])
            # Add turn number at the top
            axs[0].text(
                mid_point,
                ax.get_ylim()[1],
                f"Turn {i+1}",
                color=color,
                ha="center",
                va="bottom",
            )
            # Add transcript below the waveform
            axs[0].text(
                mid_point,
                ax.get_ylim()[0],
                turn_text,
                color=color,
                ha="center",
                va="top",
                rotation=45,
                fontsize=8,
            )

    # Plot mel spectrogram
    librosa.display.specshow(
        librosa.power_to_db(mel_spec, ref=np.max),
        y_axis="mel",
        x_axis="time",
        sr=sr,
        ax=axs[1],
    )
    axs[1].set_title("Mel spectrogram")

    # Plot MFCCs
    librosa.display.specshow(mfcc, x_axis="time", ax=axs[2])
    axs[2].set_title("MFCC")

    plt.tight_layout()
    return fig


def plot_stereo_audio_and_transitions(
    y_a, y_b, sr, title="", transitions=None, task_start=0
):
    """Helper function to visualize stereo audio and turn transitions"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle(title)

    # Plot waveforms for both speakers
    librosa.display.waveshow(y_a, sr=sr, ax=ax1, label="Speaker A")
    librosa.display.waveshow(y_b, sr=sr, ax=ax2, label="Speaker B")
    ax1.set_title("Speaker A")
    ax2.set_title("Speaker B")

    # Add turn boundaries and transitions if provided
    if transitions:
        colors = {"S": "g", "BC": "b", "PI": "r", "O": "m", "I": "y"}

        # First pass: draw turn boundaries
        for trans in transitions:
            if not trans.turn_from:
                continue

            # Draw turn boundaries for source turn
            turn_from_start = trans.turn_from.start - task_start
            turn_from_end = trans.turn_from.end - task_start
            ax = ax1 if trans.speaker_from == "A" else ax2
            ax.axvspan(turn_from_start, turn_from_end, alpha=0.1, color="gray")

            # Draw turn boundaries for target turn
            turn_to_start = trans.turn_to.start - task_start
            turn_to_end = trans.turn_to.end - task_start
            ax = ax1 if trans.speaker_to == "A" else ax2
            ax.axvspan(turn_to_start, turn_to_end, alpha=0.1, color="gray")

        # Second pass: draw transition arrows
        for trans in transitions:
            if not trans.turn_from:
                continue

            color = colors.get(trans.label, "gray")
            start_time = trans.ipu_from.end - task_start
            end_time = trans.ipu_to.start - task_start

            # Calculate arrow positions - moved closer to the waveforms
            if trans.speaker_from == "A" and trans.speaker_to == "B":
                # A to B transition
                ax1.annotate(
                    "",
                    xy=(start_time, -0.5),
                    xytext=(start_time, 0),
                    arrowprops=dict(arrowstyle="->", color=color),
                )
                ax2.annotate(
                    "",
                    xy=(end_time, 0.5),
                    xytext=(end_time, 0),
                    arrowprops=dict(arrowstyle="->", color=color),
                )
            elif trans.speaker_from == "B" and trans.speaker_to == "A":
                # B to A transition
                ax2.annotate(
                    "",
                    xy=(start_time, 0.5),
                    xytext=(start_time, 0),
                    arrowprops=dict(arrowstyle="->", color=color),
                )
                ax1.annotate(
                    "",
                    xy=(end_time, -0.5),
                    xytext=(end_time, 0),
                    arrowprops=dict(arrowstyle="->", color=color),
                )

            # Add transition label with duration - positioned between the plots
            mid_point = (start_time + end_time) / 2
            duration_text = f"{trans.label}\n{abs(trans.transition_duration):.2f}s"
            # Adjust y_pos to be between the two waveforms
            y_pos = -0.5 if trans.speaker_from == "A" else 0.5
            ax_for_label = ax1 if trans.speaker_from == "A" else ax2
            ax_for_label.text(
                mid_point,
                y_pos,
                duration_text,
                color=color,
                ha="center",
                va="center",
                fontsize=8,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
            )

    # Add legends
    transition_legend = [
        plt.Line2D([0], [0], color=c, label=l) for l, c in colors.items()
    ]
    ax1.legend(handles=transition_legend, loc="upper right")

    plt.tight_layout()
    return fig


def main():
    # Initialize and load the corpus with audio
    corpus = SpanishGamesCorpusDialogues()
    corpus.load(load_audio=True)

    # Get the first development task from batch 1
    task = next(corpus.dev_tasks(batch=1))

    print(f"\n=== Analyzing Task {task.task_id} (Session {task.session_id}) ===")
    print(f"Describer: {task.describer}")
    print(f"Target image: {task.target}")
    print(f"Score: {task.score}")
    print(f"Task duration: {task.duration:.2f}s")
    print(f"Available audio channels: {list(task.wavs.keys())}")

    # Load audio for each speaker
    for speaker, wav_path in task.wavs.items():
        print(f"\nProcessing audio for speaker {speaker}")
        print(f"Audio file: {wav_path}")

        # Load the audio file
        y, sr = librosa.load(wav_path)

        # Get audio segment for this specific task
        start_sample = int(task.start * sr)
        end_sample = int((task.start + task.duration) * sr)
        y_task = y[start_sample:end_sample]

        # Extract some basic features
        mfccs = librosa.feature.mfcc(y=y_task, sr=sr, n_mfcc=13)
        spectral_centroid = librosa.feature.spectral_centroid(y=y_task, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y_task)

        print(f"Sample rate: {sr} Hz")
        print(f"Duration: {len(y_task)/sr:.2f}s")
        print(f"MFCCs shape: {mfccs.shape}")
        print(f"Mean spectral centroid: {np.mean(spectral_centroid):.2f}")
        print(f"Mean zero crossing rate: {np.mean(zero_crossing_rate):.2f}")

        # Plot audio and features
        speaker_turns = [t for t in task.turns if t.speaker == speaker]
        fig = plot_audio_and_features(
            y_task,
            sr,
            f"Task {task.task_id} - Speaker {speaker}\nSession {task.session_id} ({task.describer} describing {task.target})",
            turns=speaker_turns,
            task_start=task.start,
        )
        plt.show()

        # Store audio for stereo visualization
        if speaker == "A":
            y_a = y_task
        else:
            y_b = y_task

    # After processing both speakers, show stereo visualization
    if "y_a" in locals() and "y_b" in locals():
        fig = plot_stereo_audio_and_transitions(
            y_a,
            y_b,
            sr,
            f"Task {task.task_id} - Stereo View\nSession {task.session_id}",
            transitions=task.turn_transitions,
            task_start=task.start,
        )
        plt.show()

        # Print turn transition statistics
        print("\nTurn Transition Analysis:")
        print("--------------------------")
        transition_types = {}
        for trans in task.turn_transitions:
            if trans.label not in transition_types:
                transition_types[trans.label] = {
                    "count": 0,
                    "avg_duration": 0,
                    "overlap_count": 0,
                }
            stats = transition_types[trans.label]
            stats["count"] += 1
            stats["avg_duration"] += trans.transition_duration
            if trans.overlapped_transition:
                stats["overlap_count"] += 1

        for label, stats in transition_types.items():
            avg_duration = stats["avg_duration"] / stats["count"]
            overlap_pct = (stats["overlap_count"] / stats["count"]) * 100
            print(f"\nTransition type: {label}")
            print(f"Count: {stats['count']}")
            print(f"Average duration: {avg_duration:.3f}s")
            print(f"Overlapped transitions: {overlap_pct:.1f}%")

    # Example: get audio for a specific turn
    print(f"\nExample turn analysis for speaker {speaker}:")
    for turn in task.turns:
        if turn.speaker == speaker:
            print(f"Turn: {turn}")
            # Get audio segment for this turn
            turn_start_sample = int((turn.start - task.start) * sr)
            turn_end_sample = int((turn.end - task.start) * sr)
            y_turn = y_task[turn_start_sample:turn_end_sample]

            # Calculate energy
            energy = np.sum(y_turn**2)
            print(f"Turn energy: {energy:.2f}")
            break


if __name__ == "__main__":
    main()
