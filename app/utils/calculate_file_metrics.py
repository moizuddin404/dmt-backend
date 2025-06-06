from .schema_functions import get_expected_columns
from .filter_data import extract_mapped_columns

def extract_all_csv_columns(mappings_dict):
    csv_columns = []
    for value in mappings_dict.values():
        if isinstance(value, dict):
            csv_columns.extend([v for v in value.values() if v])  # Filters out None and ''
        else:
            if value:
                csv_columns.append(value)
    return csv_columns

def audit_metrics(schema: dict, headers: list[str], mapping: dict, rows: list[dict]):
    # Step 1: Expected columns from the schema
    expected_columns = set(get_expected_columns(schema))

    # Step 2: Mapped tables: Ignore "extras" and check if at least one non-null mapping
    mapped_tables = [
        table for table, cols in mapping.items()
        if table != "extras" and any(val for val in cols.values())
    ]

    # Step 3: Mapped columns (CSV columns) where schema_col is valid and value is not null
    mapped_columns = {
        schema_col: csv_col if isinstance(csv_col, list) else [csv_col]
        for table_mapping in mapping.values()
        for schema_col, csv_col in table_mapping.items()
        if schema_col in expected_columns
    }

    # Step 4: Mapped schema columns to compute what's missing
    mapped_schema_columns = {
        schema_col
        for table, cols in mapping.items()
        if table != "extras"
        for schema_col, csv_col in cols.items()
        if csv_col
    }

    # Step 5: Missing schema columns
    missing_columns = [col for col in expected_columns if col not in mapped_schema_columns]

    # Step 6: Extra columns = in CSV header but not in expected OR not used in mapping
    used_csv_columns = set(
        csv_col
        for csv_col_list in mapped_columns.values()
        for csv_col in csv_col_list
        if csv_col
    ) # CSV columns used in valid mappings
    header_set = set(headers)
    extra_columns = header_set - expected_columns - used_csv_columns

    # Step 7: Also add extras from mapping['extras'] if they are not mapped to schema fields
    for extra_col, mapped_val in mapping.get("extras", {}).items():
        if extra_col not in expected_columns:
            extra_columns.add(extra_col)

    # Step 8: Empty cells count
    empty_cells = sum(
        1 for row in rows
        for val in row.values()
        if val is None or str(val).strip() == ""
    )

    # Step 9: Total columns = all non-null mapped CSV columns from all mappings
    total_columns = {
        col
        for table, cols in mapping.items()
        for csv_col in cols.values()
        for col in (csv_col if isinstance(csv_col, list) else [csv_col])
    }
    return {
        "mapped_tables": mapped_tables,
        "mapped_columns": list(mapped_columns),
        "missing_columns": missing_columns,
        "extra_columns": list(extra_columns),
        "empty_cells": empty_cells,
        "total_columns": list(total_columns),
        "mapped_column_count": len(mapped_columns),
        "total_column_count": len(total_columns)
    }

