from fastapi import  UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import csv
import pandas as pd
import numpy as np

from app.utils.llm2 import generate_table_mapping
from app.dao.insert_data import insert_data_to_tables
from app.models.core import FileUploadLog
from app.utils import load_schema, audit_metrics, sanitize_sample_data

SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".xls", ".xlsx"}

class FileService:
    UPLOAD_DIR = Path("uploaded_files")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    

    @classmethod
    async def handle_file_mapping_preview(cls, file: UploadFile, db: Session) -> dict:
        """
        Handles file preview for CSV, TSV, and Excel files.
        Converts non-CSV files to a uniform CSV-like format for downstream processing.
        """
        ext = Path(file.filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        saved_path = cls.UPLOAD_DIR / file.filename
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if ext == ".csv":
            df = pd.read_csv(saved_path)
        elif ext == ".tsv":
            df = pd.read_csv(saved_path, sep="\t")
        elif ext in {".xls", ".xlsx"}:
            df = pd.read_excel(saved_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")

        if df.empty or df.columns.isnull().any():
            raise HTTPException(status_code=400, detail="No headers found.")

        headers = df.columns.tolist()
        df = df.replace([np.nan, np.inf, -np.inf], None)
        sample_data = sanitize_sample_data(df.head(5).to_dict(orient="records"))
        mapping = await generate_table_mapping(headers, sample_data)

        schema = load_schema()
        expected_columns = [col for table in schema.values() for col in table]

        return {
            "file_name": file.filename,
            "mapping": mapping["mappings"],
            "expected_columns": expected_columns,
            "sample_data": sample_data,
            "local_path": str(saved_path),
            "total_rows": len(df)
        }

    @classmethod
    def handle_file_processing(cls, filename: str, final_mapping: dict, db: Session) -> dict:
        """
        Loads a file (CSV, TSV, Excel) by filename, applies the final mapping,
        inserts data into the database, and logs audit metrics.
        """
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        saved_path = cls.UPLOAD_DIR / filename

        if not saved_path.exists():
            raise HTTPException(status_code=404, detail="File not found on server.")

        try:
            if ext == ".csv":
                df = pd.read_csv(saved_path)
            elif ext == ".tsv":
                df = pd.read_csv(saved_path, sep="\t")
            elif ext in {".xls", ".xlsx"}:
                df = pd.read_excel(saved_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

        if df.empty or df.columns.isnull().any():
            raise HTTPException(status_code=400, detail="No headers found or file is empty.")

        headers = df.columns.tolist()
        df = df.replace([np.nan, np.inf, -np.inf], None)
        rows = df.to_dict(orient="records")

        schema = load_schema()
        audit = audit_metrics(schema, headers, final_mapping, rows)

        file_size_bytes = saved_path.stat().st_size
        file_size_kb = round(file_size_bytes / 1024, 3)

        file_log = FileUploadLog(
            filename=filename,
            file_type=ext.lstrip("."),
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