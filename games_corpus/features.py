"""Pre-extracted acoustic/prosodic features loader and downloader."""

import logging
import zipfile
from pathlib import Path

import pandas as pd
import requests

GITHUB_RELEASE_URL = "https://github.com/pbrusco/games-corpus/releases/download/v0.2.1/{filename}"

FEATURES_ZIPS = {
    "games-english": "games-english.zip",
    "games-spanish-batch1": "games-spanish-batch1.zip",
    "games-spanish-batch2": "games-spanish-batch2.zip",
    "games-slovak": "games-slovak.zip",
}


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


def download_features(features_dir: str, zip_names: list[str]) -> None:
    """Download and extract feature zip files from GitHub Releases.

    Args:
        features_dir: Base directory where features are stored (e.g. "features")
        zip_names: List of zip names to download (keys from FEATURES_ZIPS)
    """
    features_path = Path(features_dir)
    features_path.mkdir(parents=True, exist_ok=True)

    for name in zip_names:
        zip_filename = FEATURES_ZIPS[name]
        target_dir = features_path / name / "tasks_features"

        if target_dir.exists() and any(target_dir.iterdir()):
            logging.info(f"Features already present at {target_dir}")
            continue

        url = GITHUB_RELEASE_URL.format(filename=zip_filename)
        zip_path = features_path / zip_filename

        logging.info(f"Downloading {zip_filename}...")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Extracting {zip_filename}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(features_path)

        zip_path.unlink()
        logging.info(f"Features ready at {target_dir}")
