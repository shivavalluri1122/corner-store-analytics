"""Pandera-based validation of ingested sales data, producing a report the
Streamlit app can show to the user before rendering any dashboard.
"""

from dataclasses import dataclass, field

import pandas as pd
from pandera.errors import SchemaErrors

from models.schemas import CLEAN_LINE_ITEM_SCHEMA


@dataclass
class ValidationResult:
    is_valid: bool
    row_count: int
    errors: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def validate_line_items(df: pd.DataFrame) -> ValidationResult:
    """Validate a cleaned (post pipeline.ingest) DataFrame against
    CLEAN_LINE_ITEM_SCHEMA. Collects every failure (missing columns, nulls
    from failed parsing, out-of-range values) instead of stopping at the
    first one.
    """
    try:
        CLEAN_LINE_ITEM_SCHEMA.validate(df, lazy=True)
        return ValidationResult(is_valid=True, row_count=len(df))
    except SchemaErrors as exc:
        return ValidationResult(is_valid=False, row_count=len(df), errors=exc.failure_cases)
