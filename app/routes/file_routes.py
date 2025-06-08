import mimetypes
from fastapi import APIRouter, Body, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import csv

from app.database.deps import get_db
from app.services import file_service
from app.dao import file_statistics, fetch_full_database_data
from app.models.core import (
    Patient, Hospital, Lifestyle, LabResult,
    Treatment, Diagnosis, FamilyHistory, Condition, patient_conditions
)

router = APIRouter()

UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/logs/")
def get_file_logs(db: Session = Depends(get_db)):
    """
    Endpoint to get all file logs
    """
    return file_statistics.get_file_logs(db)

@router.get("/preview")
async def preview_file(filename: str):
    safe_filename = Path(filename).name
    file_path = UPLOAD_DIR / safe_filename
    print("Looking for file:", file_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        path=file_path,
        media_type=mime_type or "application/octet-stream",
        filename=safe_filename
    )

@router.get("/data/all")
def get_full_database_data(db: Session = Depends(get_db)):
    data = fetch_full_database_data(db)
    if not data or not any(data.values()):
        raise HTTPException(status_code=404, detail="No data available in the database.")
    return data

@router.get("/data/{file_id}")
def get_data_by_file(file_id: int, db: Session = Depends(get_db)):
    result = {}

    patients = db.query(Patient).filter(Patient.file_id == file_id).all()
    if not patients:
        raise HTTPException(status_code=404, detail="No data found for this file ID")

    patient_ids = [p.patient_id for p in patients]
    hospital_ids = {p.hospital_id for p in patients if p.hospital_id}

    hospitals = db.query(Hospital).filter(Hospital.hospital_id.in_(hospital_ids)).all()
    hospital_map = {h.hospital_id: h for h in hospitals}

    enriched_patients = []
    for p in patients:
        p_data = p.__dict__.copy()
        if p.hospital_id and p.hospital_id in hospital_map:
            p_data["hospital"] = hospital_map[p.hospital_id].__dict__
        p_data.pop("_sa_instance_state", None)
        enriched_patients.append(p_data)

    result["patient"] = enriched_patients

    def fetch_related(model, enrich_condition=False):
        records = db.query(model).filter(model.patient_id.in_(patient_ids)).all()
        enriched = []
        for r in records:
            r_data = r.__dict__.copy()

            if enrich_condition and r_data.get("condition_id"):
                cond = db.query(Condition).filter_by(condition_id=r_data["condition_id"]).first()
                if cond:
                    r_data["condition_name"] = cond.condition_name
                r_data.pop("condition_id", None)

            r_data.pop("_sa_instance_state", None)
            enriched.append(r_data)
        return enriched

    tables = {
        "treatment": Treatment,
        "diagnosis": (Diagnosis, True),
        "lifestyle": Lifestyle,
        "lab_result": LabResult,
        "family_history": (FamilyHistory, True)
    }

    for name, model_info in tables.items():
        if isinstance(model_info, tuple):
            model, enrich = model_info
        else:
            model, enrich = model_info, False

        table_data = fetch_related(model, enrich_condition=enrich)
        if table_data:
            result[name] = table_data

    return result


@router.post("/upload/preview")
async def upload_file_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint to handle file upload, mapping and return mapping preview.
    """
    return await file_service.handle_file_mapping_preview(file, db)

@router.post("/upload/process")
async def finalize_file_mapping(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint to insert data into database according to mapping received
    """
    file_name = payload.get("file_name")
    final_mapping = payload.get("mapping")

    if not file_name or not final_mapping:
        raise HTTPException(status_code=400, detail="Missing file_name or mapping.")

    return file_service.handle_file_processing(file_name, final_mapping, db)
