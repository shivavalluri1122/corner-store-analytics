import time

import pytest

from pipeline.db import build_and_load, get_connection
from pipeline.ingest import ingest_csv
from pipeline.validate import validate_line_items


def test_full_pipeline_handles_large_dataset_quickly(large_clean_path):
    if not large_clean_path.exists():
        pytest.skip("large_clean.csv not present; regenerate with `python -m data.synthetic.generate_dataset`")

    start = time.perf_counter()
    df = ingest_csv(large_clean_path)
    result = validate_line_items(df)
    conn = get_connection()
    tables = build_and_load(conn, df)
    elapsed = time.perf_counter() - start

    assert result.is_valid
    assert len(tables["line_items"]) == len(df)
    assert elapsed < 30, f"pipeline took {elapsed:.1f}s on the large dataset, expected < 30s"
