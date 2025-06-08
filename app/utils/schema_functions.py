import json
from pathlib import Path

SCHEMA_PATH = Path("app/schemas/schema.json")

def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def get_expected_columns(schema: dict):
    expected_cols = []
    for table, columns in schema.items():
        expected_cols.extend(columns)
    return list(set(expected_cols))
