from games_corpus import SpanishGamesCorpusDialogues
import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt


def plot_audio_and_features(y, sr, title=""):
    """Helper function to visualize audio and its features"""
    # Calculate features
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
    
    # Create subplots
    fig, axs = plt.subplots(3, 1, figsize=(12, 8))
    fig.suptitle(title)
    
    # Plot waveform
    librosa.display.waveshow(y, sr=sr, ax=axs[0])
    axs[0].set_title('Waveform')
    
    # Plot mel spectrogram
    librosa.display.specshow(
        librosa.power_to_db(mel_spec, ref=np.max),
        y_axis='mel', 
        x_axis='time',
        sr=sr,
        ax=axs[1]
    )
    axs[1].set_title('Mel spectrogram')
    
    # Plot MFCCs
    librosa.display.specshow(
        mfcc, 
        x_axis='time',
        ax=axs[2]
    )
    axs[2].set_title('MFCC')
    
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
        fig = plot_audio_and_features(
            y_task, 
            sr, 
            f"Task {task.task_id} - Speaker {speaker}\nSession {task.session_id} ({task.describer} describing {task.target})"
        )
        plt.show()

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
