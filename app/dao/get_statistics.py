from fastapi import Depends
from requests import Session

from app.database.deps import get_db
from app.models.core import FileUploadLog

class FileStatistics:
    def get_file_logs(self, db: Session):
        """
        Description: Getting File statistics for file management component
        """
        logs = db.query(FileUploadLog).order_by(FileUploadLog.upload_time.desc()).all()
        return [
            {
                "file_id": log.file_id,
                "filename": log.filename,
                "file_type": log.file_type,
                "upload_time": log.upload_time,
                "status": log.status,
                "mapped_tables": log.mapped_tables,
                "mapped_columns": (log.mapped_columns),
                "missing_columns": log.missing_columns,
                "extra_columns": log.extra_columns,
                "empty_cells": log.empty_cells,
                "total_rows": log.total_rows,
                "total_input_columns": log.total_input_columns,
                "size": log.file_size
            }
            for log in logs
        ]