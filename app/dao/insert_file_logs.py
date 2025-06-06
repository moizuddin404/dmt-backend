# app/services/insert_file_logs.py
from sqlalchemy.orm import Session
from app.models.core import FileUploadLog

def insert_file_log(
    db: Session,
    filename: str,
    file_type: str,
    status: str,
    mapped_tables: list,
    mapped_columns: list,
    missing_columns: list,
    extra_columns: list,
    empty_cells: int,
    invalid_types: list,
    total_rows: int,
    local_path: str
) -> int:
    """
    Insert a file upload log entry and return its generated file_id.
    """
    file_log = FileUploadLog(
        filename=filename,
        file_type=file_type,
        status=status,
        mapped_tables=mapped_tables,
        mapped_columns=mapped_columns,
        missing_columns=missing_columns,
        extra_columns=extra_columns,
        empty_cells=empty_cells,
        invalid_types=invalid_types,
        total_rows=total_rows,
        local_path = local_path,
    )
    db.add(file_log)
    db.commit()
    db.refresh(file_log)
    return file_log.file_id
