import math

def filter_valid_columns(model, row_data):
    model_columns = model.__table__.columns.keys()
    return {key: val for key, val in row_data.items() if key in model_columns}

def extract_mapped_columns(mapping: dict) -> set:
    mapped = set()
    for table_mapping in mapping.values(): 
        for col_info in table_mapping.values():
            if isinstance(col_info, list):
                mapped.update(col_info)
            elif isinstance(col_info, str):
                mapped.add(col_info)
    return mapped

def sanitize_sample_data(data):
    def clean_value(val):
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return val

    return [
        {k: clean_value(v) for k, v in row.items()}
        for row in data
    ]

