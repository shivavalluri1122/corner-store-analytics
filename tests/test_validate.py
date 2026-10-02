from pipeline.ingest import ingest_csv
from pipeline.validate import validate_line_items


def test_clean_dataset_passes_validation(small_clean_path):
    df = ingest_csv(small_clean_path)
    result = validate_line_items(df)
    assert result.is_valid
    assert result.error_count == 0
    assert result.row_count == len(df)


def test_malformed_dataset_fails_validation(malformed_path):
    df = ingest_csv(malformed_path)
    result = validate_line_items(df)
    assert not result.is_valid
    assert result.error_count > 0


def test_malformed_dataset_reports_missing_columns(malformed_path):
    df = ingest_csv(malformed_path)
    result = validate_line_items(df)
    failure_cases = result.errors["failure_case"].astype(str)
    assert failure_cases.str.contains("sku").any()
    assert failure_cases.str.contains("net_sales").any()
