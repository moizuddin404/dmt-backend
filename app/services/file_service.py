from fastapi import  UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import csv

from app.utils.llm2 import generate_table_mapping
from app.dao.insert_data import insert_data_to_tables
from app.dao.insert_file_logs import insert_file_log
from app.models.core import FileUploadLog
from app.utils import load_schema, audit_metrics

class FileService:
    UPLOAD_DIR = Path("uploaded_files")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    async def handle_file_mapping_preview(cls, file: UploadFile, db: Session) -> dict:
        """
        Name: handle_file_mapping_preview
        Params: file: UploadFile, db: Session
        Description: Handles the preview of a CSV file upload and generates a mapping of CSV headers to expected schema fields.
        Return: A dictionary containing the mapping and basic preview info (like sample rows and expected columns).
        """
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are supported.")

        saved_path = cls.UPLOAD_DIR / file.filename
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with saved_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames or []

        if not headers:
            raise HTTPException(status_code=400, detail="No headers found.")

        sample_data = rows[:5]
        mapping = await generate_table_mapping(headers, sample_data)

        schema = load_schema()
        expected_columns = [col for table in schema.values() for col in table]

        return {
            "file_name": file.filename,
            "mapping": mapping["mappings"],
            "expected_columns": expected_columns,
            "sample_data": sample_data,
            "local_path": str(saved_path),
            "total_rows": len(rows)
        }


    @classmethod
    def handle_file_processing(cls, filename: str, final_mapping: dict, db: Session) -> dict:
        """
        Name: handle_file_processing
        Params: filename: str, final_mapping: dict, db: Session
        Description: Loads the saved CSV file by filename, applies the final mapping,
        inserts data into the database, and creates an audit log.
        Return: message, number of rows inserted, and audit metrics.
        """
        #debug
        print(f"Processing file: {filename} with mapping: {final_mapping}")
        if not filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are supported.")

        saved_path = cls.UPLOAD_DIR / filename

        if not saved_path.exists():
            raise HTTPException(status_code=404, detail="File not found on server.")

        with saved_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames or []

        if not headers:
            raise HTTPException(status_code=400, detail="CSV file has no headers.")

        schema = load_schema()
        audit = audit_metrics(schema, headers, final_mapping, rows)

        # file size
        file_size_bytes = saved_path.stat().st_size
        file_size_kb = round(file_size_bytes / (1024 ), 3)

        # STEP 1: Insert into file log first and get the file_id
        file_log = FileUploadLog(
            filename=filename,
            file_type="csv",
            status="processed",
            mapped_tables=audit["mapped_tables"],
            mapped_columns=audit["mapped_columns"],
            missing_columns=audit["missing_columns"],
            extra_columns=audit["extra_columns"],
            empty_cells=audit["empty_cells"],
            total_rows=len(rows),
            local_path=str(saved_path),
            total_input_columns=audit["total_column_count"],
            file_size=file_size_kb
        )
        db.add(file_log)
        db.commit()
        db.refresh(file_log)
        file_id = file_log.file_id

        
        insert_data_to_tables(final_mapping, rows, db, file_id=file_id)

        return {
            "message": "File processed and data inserted successfully.",
            "rows": len(rows),
            "audit": audit,
            "file_id": file_id
        }