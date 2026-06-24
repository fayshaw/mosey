import pandas as pd
import pytest

from src.walk_utils import merge_into_database


def _make_audit_df(rows):
    """Build a small DataFrame mimicking geocoded audit rows."""
    defaults = {
        "Timestamp": None,
        "along": "Main St",
        "begin": "Cross St",
        "end": "Salem St",
        "endpoint": "begin",
        "lat": 42.4259,
        "lon": -71.0662,
        "geocoding_status": "success",
        "color": "gold",
        "Walkability of the area, based on the findings above:  ": "Mixed",
    }
    records = []
    for row in rows:
        record = {**defaults, **row}
        records.append(record)
    return pd.DataFrame(records)


class TestCreateDatabase:
    def test_creates_file_when_none_exists(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        df = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "along": "Bell Rock St"},
            {"Timestamp": "2025-11-07 13:51:05", "along": "Main St"},
        ])

        result = merge_into_database(df, db_path)

        assert db_path.exists()
        assert len(result) == 2
        saved = pd.read_csv(db_path)
        assert len(saved) == 2

    def test_columns_match_input(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        df = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19"},
        ])

        merge_into_database(df, db_path)

        saved = pd.read_csv(db_path)
        assert list(saved.columns) == list(df.columns)


class TestAppendNewRows:
    def test_new_rows_appended(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        existing = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "along": "Bell Rock St"},
            {"Timestamp": "2025-11-07 13:51:05", "along": "Main St"},
        ])
        merge_into_database(existing, db_path)

        new_data = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "along": "Bell Rock St"},
            {"Timestamp": "2025-11-07 13:51:05", "along": "Main St"},
            {"Timestamp": "2025-12-01 10:00:00", "along": "Salem St"},
            {"Timestamp": "2025-12-01 10:15:00", "along": "Cross St"},
        ])
        result = merge_into_database(new_data, db_path)

        assert len(result) == 4
        saved = pd.read_csv(db_path)
        assert len(saved) == 4
        assert "Salem St" in saved["along"].values
        assert "Cross St" in saved["along"].values

    def test_begin_and_end_rows_both_added(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        existing = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "endpoint": "begin"},
        ])
        merge_into_database(existing, db_path)

        new_data = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "endpoint": "begin"},
            {"Timestamp": "2025-12-01 10:00:00", "endpoint": "begin"},
            {"Timestamp": "2025-12-01 10:00:00", "endpoint": "end"},
        ])
        result = merge_into_database(new_data, db_path)

        assert len(result) == 3
        new_rows = result[result["Timestamp"] == "2025-12-01 10:00:00"]
        assert len(new_rows) == 2
        assert set(new_rows["endpoint"]) == {"begin", "end"}


class TestManualFixesSurvive:
    def test_existing_lat_lon_not_overwritten(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        existing = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "lat": 42.999, "lon": -71.999,
             "endpoint": "begin"},
        ])
        merge_into_database(existing, db_path)

        new_data = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "lat": 42.4259, "lon": -71.0662,
             "endpoint": "begin"},
        ])
        result = merge_into_database(new_data, db_path)

        row = result[result["Timestamp"] == "2025-11-07 13:43:19"].iloc[0]
        assert row["lat"] == pytest.approx(42.999)
        assert row["lon"] == pytest.approx(-71.999)


class TestTimestampNormalization:
    def test_milliseconds_ignored_in_matching(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        existing = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19.883", "endpoint": "begin"},
        ])
        merge_into_database(existing, db_path)

        new_data = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19", "endpoint": "begin"},
        ])
        result = merge_into_database(new_data, db_path)

        assert len(result) == 1


class TestEdgeCases:
    def test_empty_new_data_is_noop(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        existing = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19"},
            {"Timestamp": "2025-11-07 13:51:05"},
        ])
        merge_into_database(existing, db_path)

        empty = _make_audit_df([])
        result = merge_into_database(empty, db_path)

        assert len(result) == 2
        saved = pd.read_csv(db_path)
        assert len(saved) == 2

    def test_columns_consistent_after_merge(self, tmp_path):
        db_path = tmp_path / "walk_audit_database.csv"
        existing = _make_audit_df([
            {"Timestamp": "2025-11-07 13:43:19"},
        ])
        merge_into_database(existing, db_path)

        new_data = _make_audit_df([
            {"Timestamp": "2025-12-01 10:00:00"},
        ])
        merge_into_database(new_data, db_path)

        saved = pd.read_csv(db_path)
        assert list(saved.columns) == list(existing.columns)
