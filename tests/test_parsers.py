"""Parser edge case tests.

Tests marked with 'to_be_reviewed_by_human' cover interesting edge cases
that should be verified against the actual corpus data.
"""

from pathlib import Path

import pytest

from games_corpus.parsers import (
    load_objects_tasks,
    load_ipus_from_words,
    load_ipus_from_phrases,
)
from games_corpus.features import load_task_features
from games_corpus.types import TurnTransitionType

to_be_reviewed_by_human = pytest.mark.to_be_reviewed_by_human


# ---------------------------------------------------------------------------
# load_objects_tasks — field order variants
# ---------------------------------------------------------------------------


class TestLoadObjectsTasks:
    def test_standard_field_order(self, tmp_path):
        """English/Spanish B1: Images;Describer;Target;Score;Time-used"""
        f = tmp_path / "tasks.txt"
        f.write_text("0.0 10.0 Images:a,b;Describer:A;Target:a;Score:99;Time-used:10.0\n")
        tasks = load_objects_tasks(f)
        assert len(tasks) == 1
        assert tasks[0]["Score"] == "99"
        assert tasks[0]["Time-used"] == 10.0

    @to_be_reviewed_by_human
    def test_slovak_field_order(self, tmp_path):
        """Slovak has Time-used before Score, and a duplicate Describer field.
        The parser should handle this by parsing fields by name, not position."""
        f = tmp_path / "tasks.txt"
        f.write_text(
            "541.48 642.28 Images:alien,mirror,bluemoon;"
            "Describer:A;Target:bluemoon;Time-used:0.0;Describer:A;Score:90\n"
        )
        tasks = load_objects_tasks(f)
        assert len(tasks) == 1
        assert tasks[0]["Score"] == "90"
        assert tasks[0]["Time-used"] == 0.0
        assert tasks[0]["Describer"] == "A"
        assert tasks[0]["Target"] == "bluemoon"

    def test_skips_silence_lines(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("0.0 10.0 #\n10.0 20.0 Images:a,b;Describer:A;Target:a;Score:1;Time-used:5.0\n")
        tasks = load_objects_tasks(f)
        assert len(tasks) == 1

    def test_skips_comments_and_practice(self, tmp_path):
        """English corpus has 'comments' and 'talking-to-confederate' lines;
        Slovak has 'practice' and 'comments' lines."""
        f = tmp_path / "tasks.txt"
        f.write_text(
            "0.0 10.0 comments\n"
            "10.0 20.0 talking-to-confederate\n"
            "20.0 30.0 practice\n"
            "30.0 40.0 Images:a,b;Describer:B;Target:b;Score:50;Time-used:10.0\n"
        )
        tasks = load_objects_tasks(f)
        assert len(tasks) == 1
        assert tasks[0]["Describer"] == "B"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("")
        tasks = load_objects_tasks(f)
        assert tasks == []

    @to_be_reviewed_by_human
    def test_task_ids_are_sequential(self, tmp_path):
        """Task IDs should be 1-indexed and sequential regardless of gaps in the file."""
        f = tmp_path / "tasks.txt"
        f.write_text(
            "0.0 10.0 #\n"
            "10.0 20.0 Images:a;Describer:A;Target:a;Score:1;Time-used:5.0\n"
            "20.0 30.0 comments\n"
            "30.0 40.0 Images:b;Describer:B;Target:b;Score:2;Time-used:5.0\n"
        )
        tasks = load_objects_tasks(f)
        assert tasks[0]["Task ID"] == 1
        assert tasks[1]["Task ID"] == 2

    @to_be_reviewed_by_human
    def test_missing_optional_fields_have_defaults(self, tmp_path):
        """If a field is missing, it should get a sensible default."""
        f = tmp_path / "tasks.txt"
        # Missing Score and Time-used
        f.write_text("0.0 10.0 Images:a,b;Describer:A;Target:a\n")
        tasks = load_objects_tasks(f)
        assert len(tasks) == 1
        assert tasks[0]["Score"] == "0"
        assert tasks[0]["Time-used"] == 0


# ---------------------------------------------------------------------------
# load_ipus_from_words — delimiter and silence variants
# ---------------------------------------------------------------------------


class TestLoadIPUsFromWords:
    def test_space_delimited_words(self, tmp_path):
        """English corpus uses space-delimited .words files."""
        f = tmp_path / "A.words"
        f.write_text("0.0 1.0 #\n1.0 2.0 hello\n2.0 3.0 world\n3.0 4.0 #\n")
        ipus = load_ipus_from_words({"A": f}, (0.0, 5.0))
        assert len(ipus) == 1
        assert ipus[0].text == "hello world"
        assert ipus[0].speaker == "A"

    def test_tab_delimited_words(self, tmp_path):
        """Spanish corpus uses tab-delimited .words files."""
        f = tmp_path / "A.words"
        f.write_text("0.0\t1.0\t#\n1.0\t2.0\thola\n2.0\t3.0\tmundo\n3.0\t4.0\t#\n")
        ipus = load_ipus_from_words({"A": f}, (0.0, 5.0))
        assert len(ipus) == 1
        assert ipus[0].text == "hola mundo"

    @to_be_reviewed_by_human
    def test_multiple_ipus_separated_by_silence(self, tmp_path):
        """Silence (#) should split words into separate IPUs."""
        f = tmp_path / "A.words"
        f.write_text("0.0 1.0 hello\n1.0 2.0 #\n2.0 3.0 world\n")
        ipus = load_ipus_from_words({"A": f}, (0.0, 5.0))
        assert len(ipus) == 2
        assert ipus[0].text == "hello"
        assert ipus[1].text == "world"

    def test_task_boundary_filtering(self, tmp_path):
        """Words outside task boundaries should be excluded."""
        f = tmp_path / "A.words"
        f.write_text("0.0 1.0 before\n1.0 2.0 #\n5.0 6.0 inside\n6.0 7.0 #\n10.0 11.0 after\n")
        ipus = load_ipus_from_words({"A": f}, (4.0, 8.0))
        assert len(ipus) == 1
        assert ipus[0].text == "inside"

    @to_be_reviewed_by_human
    def test_two_speakers(self, tmp_path):
        """Both speakers' words should produce separate IPUs."""
        fa = tmp_path / "A.words"
        fb = tmp_path / "B.words"
        fa.write_text("0.0 1.0 hello\n1.0 2.0 #\n")
        fb.write_text("0.5 1.5 hi\n1.5 2.5 #\n")
        ipus = load_ipus_from_words({"A": fa, "B": fb}, (0.0, 5.0))
        assert len(ipus) == 2
        speakers = {ipu.speaker for ipu in ipus}
        assert speakers == {"A", "B"}

    @to_be_reviewed_by_human
    def test_utf8_words(self, tmp_path):
        """Slovak/Spanish words contain diacritics that must be preserved."""
        f = tmp_path / "A.words"
        f.write_text("0.0 1.0 môžem\n1.0 2.0 kliknúť\n2.0 3.0 #\n", encoding="utf-8")
        ipus = load_ipus_from_words({"A": f}, (0.0, 5.0))
        assert ipus[0].text == "môžem kliknúť"


# ---------------------------------------------------------------------------
# load_ipus_from_phrases — silence marker variants
# ---------------------------------------------------------------------------


class TestLoadIPUsFromPhrases:
    def test_tab_delimited_with_hash_silence(self, tmp_path):
        """Spanish B2 uses tab-delimited phrases with # for silence."""
        f = tmp_path / "A.phrases"
        f.write_text("0.0\t1.0\t#\n1.0\t3.0\thola mundo\n3.0\t4.0\t#\n")
        ipus = load_ipus_from_phrases({"A": f})
        assert len(ipus) == 1
        assert ipus[0].num_words == 2

    @to_be_reviewed_by_human
    def test_space_delimited_with_xxx_silence(self, tmp_path):
        """Slovak .Phrases uses space-delimited format with 'xxx' for silence."""
        f = tmp_path / "A.Phrases"
        f.write_text("0.0 1.0 xxx\n1.0 3.0 môžem kliknúť ďalej\n3.0 4.0 xxx\n")
        ipus = load_ipus_from_phrases({"A": f})
        assert len(ipus) == 1
        assert ipus[0].num_words == 3
        assert ipus[0].text == "môžem kliknúť ďalej"

    @to_be_reviewed_by_human
    def test_task_boundary_filtering(self, tmp_path):
        """Phrases outside task boundaries should be excluded when boundaries are provided."""
        f = tmp_path / "A.phrases"
        f.write_text("0.0\t1.0\t#\n1.0\t3.0\tbefore\n5.0\t7.0\tinside\n10.0\t12.0\tafter\n")
        ipus = load_ipus_from_phrases({"A": f}, task_boundaries=(4.0, 8.0))
        assert len(ipus) == 1
        assert ipus[0].text == "inside"

    @to_be_reviewed_by_human
    def test_word_timing_distributed_evenly(self, tmp_path):
        """When a phrase has multiple words, their timings should be evenly distributed."""
        f = tmp_path / "A.phrases"
        f.write_text("10.0\t14.0\tone two three four\n")
        ipus = load_ipus_from_phrases({"A": f})
        assert len(ipus) == 1
        words = ipus[0].words
        assert len(words) == 4
        assert words[0].start == pytest.approx(10.0)
        assert words[0].end == pytest.approx(11.0)
        assert words[3].start == pytest.approx(13.0)
        assert words[3].end == pytest.approx(14.0)


# ---------------------------------------------------------------------------
# TurnTransitionType — corpus-specific labels
# ---------------------------------------------------------------------------


class TestTurnTransitionTypeEdgeCases:
    @to_be_reviewed_by_human
    def test_ambiguous_labels_map_to_ambiguous(self):
        """L, L-SIM, N, N-SIM, and ? should all map to AMBIGUOUS.
        These appear in English and Slovak corpora."""
        for label in ["L", "L-SIM", "N", "N-SIM", "?"]:
            result = TurnTransitionType.from_string(label)
            assert result == TurnTransitionType.AMBIGUOUS, f"{label} should map to AMBIGUOUS"

    @to_be_reviewed_by_human
    def test_all_known_labels_are_parseable(self):
        """Every label that appears across all three corpora should be parseable."""
        all_labels = ["S", "O", "I", "BC", "BC_O", "BI", "PI", "X1", "X2", "X2_O", "X3", "A", "L", "N", "?"]
        for label in all_labels:
            result = TurnTransitionType.from_string(label)
            assert result is not None, f"Label '{label}' should be parseable"


# ---------------------------------------------------------------------------
# Features loader
# ---------------------------------------------------------------------------

FEATURES_PATH = Path(__file__).resolve().parent.parent / "features" / "games-english"
requires_english_features = pytest.mark.skipif(
    not (FEATURES_PATH / "tasks_features").exists(),
    reason="English features not available locally",
)


class TestLoadTaskFeaturesUnit:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_task_features(tmp_path, session_id=99, task_id=99)

    @requires_english_features
    @to_be_reviewed_by_human
    def test_all_168_feature_files_exist(self):
        """Every session/task combination (12 sessions x 14 tasks) should have a features file."""
        missing = []
        for session in range(1, 13):
            for task in range(1, 15):
                path = FEATURES_PATH / "tasks_features" / f"{session:02d}_{task}.csv"
                if not path.exists():
                    missing.append(f"{session:02d}_{task}")
        assert missing == [], f"Missing feature files: {missing}"

    @requires_english_features
    @to_be_reviewed_by_human
    def test_feature_columns_consistent_across_files(self):
        """All feature files should have the same 13 columns."""
        import pandas as pd

        expected_columns = None
        inconsistent = []
        for session in range(1, 13):
            path = FEATURES_PATH / "tasks_features" / f"{session:02d}_1.csv"
            if path.exists():
                df = pd.read_csv(path, nrows=1)
                if expected_columns is None:
                    expected_columns = list(df.columns)
                elif list(df.columns) != expected_columns:
                    inconsistent.append(f"{session:02d}_1")
        assert inconsistent == [], f"Inconsistent columns in: {inconsistent}"

    @requires_english_features
    @to_be_reviewed_by_human
    def test_time_column_is_monotonically_increasing(self):
        """The time column should be strictly increasing in each feature file."""
        import pandas as pd

        df = pd.read_csv(FEATURES_PATH / "tasks_features" / "01_1.csv")
        assert df["time"].is_monotonic_increasing

    @requires_english_features
    @to_be_reviewed_by_human
    def test_vad_values_are_binary(self):
        """VAD columns should only contain 0.0 and 1.0."""
        import pandas as pd

        df = pd.read_csv(FEATURES_PATH / "tasks_features" / "01_1.csv")
        for col in ["vad_A", "vad_B"]:
            unique_vals = set(df[col].dropna().unique())
            assert unique_vals <= {0.0, 1.0}, f"{col} has non-binary values: {unique_vals}"
