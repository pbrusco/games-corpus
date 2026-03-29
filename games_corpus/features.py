"""Pre-extracted acoustic/prosodic features loader."""

from pathlib import Path

import pandas as pd


def load_task_features(features_path: Path, session_id: int, task_id: int) -> pd.DataFrame:
    """Load pre-extracted acoustic features for a task.

    Args:
        features_path: Root path to the features directory (e.g. features/games-english/)
        session_id: Session number
        task_id: Task number within the session

    Returns:
        DataFrame with columns: time, pitch_standardized_{A,B}, jitter_standardized_{A,B},
        shimmer_standardized_{A,B}, logHNR_standardized_{A,B}, intensity_standardized_{A,B},
        vad_{A,B}
    """
    csv_path = features_path / "tasks_features" / f"{session_id:02d}_{task_id}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Features file not found: {csv_path}")
    return pd.read_csv(csv_path)
