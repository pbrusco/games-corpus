"""Corpus file downloader for remote corpora."""

import logging
import time
import zipfile
from pathlib import Path

import requests


class CorpusDownloader:
    """Handles downloading and extracting corpus files"""

    def __init__(self, url: str, local_path: Path, max_retries: int = 3, retry_delay: int = 5):
        self.url = url
        self.local_path = local_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def download_corpus(self, files_to_download: dict):
        """Download all corpus files"""
        for file_id, file_name in files_to_download.items():
            if ".zip" in file_name:
                self._download_and_extract_zip(file_id, file_name)
            else:
                self._download_file(file_name)

    def _download_and_extract_zip(self, file_id: str, file_name: str):
        zip_file_path = self.local_path / file_name
        extracted_folder_path = self.local_path / file_id

        if extracted_folder_path.exists():
            logging.info(f"{file_name} already downloaded.")
            return

        if not zip_file_path.exists():
            self._download_file(file_name, zip_file_path)

        logging.info(f"Extracting {file_name}...")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(self.local_path)

    def _download_file(self, file_name: str, save_path: Path = None):
        save_path = save_path or self.local_path / file_name
        if save_path.exists():
            logging.info(f"{file_name} already exists.")
            return

        for attempt in range(self.max_retries):
            try:
                logging.info(f"Downloading {file_name} (attempt {attempt + 1})...")
                response = requests.get(self.url.format(filename=file_name), timeout=30)
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return
            except requests.exceptions.SSLError as e:
                raise RuntimeError(
                    f"SSL certificate verification failed while downloading {file_name}.\n"
                    "This is a common issue on macOS with Homebrew Python.\n"
                    "Try one of the following fixes:\n"
                    "  1. Set the SSL_CERT_FILE environment variable before running:\n"
                    '     export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")\n'
                    "  2. Or point it to the Homebrew CA bundle:\n"
                    "     export SSL_CERT_FILE=/opt/homebrew/etc/openssl@3/cert.pem\n"
                ) from e
            except (requests.RequestException, IOError) as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to download {file_name}: {e}")
                time.sleep(self.retry_delay)
