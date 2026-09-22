"""Tests for modernization features: BaseGamesCorpus, safe lookups, downloader streaming."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from games_corpus import (
    BaseGamesCorpus,
    EnglishGamesCorpus,
    SlovakGamesCorpus,
    SpanishGamesCorpus,
    IPU,
    Session,
    Task,
    Turn,
    TurnTransition,
    Word,
)
from games_corpus.downloader import CorpusDownloader


class TestBaseGamesCorpus:
    def test_all_corpora_inherit_base(self):
        assert issubclass(SpanishGamesCorpus, BaseGamesCorpus)
        assert issubclass(EnglishGamesCorpus, BaseGamesCorpus)
        assert issubclass(SlovakGamesCorpus, BaseGamesCorpus)

    def test_cannot_instantiate_incomplete_subclass(self):
        class IncompleteCorpus(BaseGamesCorpus):
            pass

        with pytest.raises(TypeError):
            IncompleteCorpus()  # type: ignore[abstract]

    def test_polymorphic_corpus_interface(self):
        corpora: list[BaseGamesCorpus] = [
            SpanishGamesCorpus(),
            EnglishGamesCorpus(),
            SlovakGamesCorpus(),
        ]
        names = [c.name for c in corpora]
        assert names == [
            "UBA Games Corpus",
            "Columbia Games Corpus",
            "Slovak Games Corpus",
        ]

    def test_base_games_corpus_load_contract(self):
        class DummyCorpus(BaseGamesCorpus):
            def __init__(self):
                self.loaded = False

            @property
            def name(self) -> str:
                return "Dummy"

            def load(
                self,
                local_path: str | Path | None = None,
                load_audio: bool = False,
                features_path: str | Path | dict[int, str | Path] | None = None,
                **kwargs,
            ) -> None:
                self.loaded = True

            def download_features(self, features_dir: str = "features") -> None:
                pass

            def get_features(self, task: Task):
                import pandas as pd

                return pd.DataFrame()

        c: BaseGamesCorpus = DummyCorpus()
        c.load(local_path="/tmp", load_audio=True, features_path="/tmp/features")
        assert getattr(c, "loaded", False) is True


class TestTypesModernization:
    def test_turn_get_by_id_returns_none_when_missing(self):
        Turn.clear_registry()
        assert Turn.get_turn_by_id("non_existent_turn_id") is None

    def test_session_batch_optional(self):
        Session.clear_registry()
        s = Session(session_id=99, subject_a="A", subject_b="B")
        assert s.batch is None
        assert s.session_id == 99

    def test_task_wavs_conversion_to_path(self):
        task = Task(
            task_id=1,
            session_id=1,
            start=0.0,
            duration=5.0,
            images=["img1.jpg"],
            describer="A",
            target="img1.jpg",
            score=1.0,
            time_used=5.0,
            turn_transitions=[],
            turns=[],
            ipus=[],
            wavs={"A": "/audio/A.wav", "B": Path("/audio/B.wav")},
        )
        assert isinstance(task.wavs["A"], Path)
        assert isinstance(task.wavs["B"], Path)
        assert task.wavs["A"] == Path("/audio/A.wav")

    def test_task_id_is_int_and_formatted_with_leading_zero(self):
        task = Task(
            task_id=5,
            session_id=1,
            start=0.0,
            duration=5.0,
            images=["img1.jpg"],
            describer="A",
            target="img1.jpg",
            score=1.0,
            time_used=5.0,
            turn_transitions=[],
            turns=[],
            ipus=[],
            wavs={},
        )
        assert isinstance(task.task_id, int)
        assert task.task_id == 5
        assert "[Task 05 (A)" in str(task)
        assert "[Task 05 (A)" in repr(task)

    def test_turn_ipus_raises_keyerror_on_missing_ipu(self):
        IPU.clear_registry()
        Turn.clear_registry()
        word = Word(start=0.0, end=1.0, text="hello", speaker="A")
        ipu = IPU(words=[word])
        turn = Turn(
            session_id=1,
            task_id=1,
            speaker="A",
            start=0.0,
            end=1.0,
            ipu_ids=[ipu.ipu_id],
        )
        assert turn.ipus == [ipu]
        turn.ipu_ids.append("missing_ipu_id")
        with pytest.raises(KeyError, match="missing_ipu_id"):
            _ = turn.ipus

    def test_turn_transition_raises_value_error_on_missing_turn_from(self):
        IPU.clear_registry()
        Turn.clear_registry()
        word = Word(start=2.0, end=3.0, text="hi", speaker="A")
        ipu = IPU(words=[word])
        turn_to = Turn(
            session_id=1,
            task_id=1,
            speaker="A",
            start=2.0,
            end=3.0,
            ipu_ids=[ipu.ipu_id],
        )
        with pytest.raises(ValueError, match="Source turn not found"):
            TurnTransition(label="S", turn_id_from="non_existent_source", turn_id_to=turn_to.turn_id)


class TestDownloaderStreaming:
    def test_download_file_creates_parent_directories(self, tmp_path):
        target_dir = tmp_path / "deep" / "nested" / "path"
        downloader = CorpusDownloader(url="https://example.com/{filename}", local_path=target_dir)

        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response) as mock_get:
            downloader._download_file("test.txt")
            mock_get.assert_called_once_with("https://example.com/test.txt", stream=True, timeout=60)

        saved_file = target_dir / "test.txt"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"chunk1chunk2"

    def test_downloader_atomic_streaming_cleans_up_on_failure(self, tmp_path):
        import requests

        target_dir = tmp_path / "download"
        downloader = CorpusDownloader(
            url="https://example.com/{filename}",
            local_path=target_dir,
            max_retries=1,
            retry_delay=0,
        )

        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.RequestException("Network error")

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to download test.txt"):
                downloader._download_file("test.txt")

        assert not (target_dir / "test.txt").exists()
        assert not (target_dir / "test.txt.part").exists()
