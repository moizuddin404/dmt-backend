from sqlalchemy.orm import Session, joinedload
from app.models.core import (
    Patient, Hospital, Condition, Treatment,
    Diagnosis, Lifestyle, LabResult, FamilyHistory
)

def fetch_full_database_data(db: Session) -> dict:
    """
    Description: Fetching complete data from database
    """
    result = {}
    table_order = ["patient", "lifestyle", "diagnosis", "lab_result", "treatment", "hospital", "family_history"]

    def reorder_fields(data: dict, order: list):
        return {field: data.pop(field) for field in order if field in data} | data

    patients = db.query(Patient).options(joinedload(Patient.hospital)).all()
    enriched_patients = []
    for p in patients:
        p_data = p.__dict__.copy()
        p_data.pop("_sa_instance_state", None)
        p_data["hospital_name"] = p.hospital.hospital_name if p.hospital else None
        p_data.pop("hospital_id", None)
        ordered_fields = [
            "patient_id", "first_name", "last_name", "phone", "email",
            "gender", "address", "country", "date_of_birth", "hospital_name", "file_id"
        ]
        enriched_patients.append(reorder_fields(p_data, ordered_fields))
    result["patient"] = enriched_patients

    lifestyles = db.query(Lifestyle).options(joinedload(Lifestyle.patient)).all()
    result["lifestyle"] = [
        reorder_fields({
            "lifestyle_id": l.lifestyle_id,
            "patient_id": l.patient_id,
            "first_name": l.patient.first_name if l.patient else None,
            "alcohol_use": l.alcohol_use,
            "diet": l.diet,
            "smoking_status": l.smoking_status,
            "exercise_habit": l.exercise_habit,
            "file_id": l.file_id
        }, [
            "lifestyle_id", "patient_id", "first_name", "alcohol_use",
            "diet", "smoking_status", "exercise_habit", "file_id"
        ]) for l in lifestyles
    ]

    diagnoses = db.query(Diagnosis).options(joinedload(Diagnosis.condition), joinedload(Diagnosis.patient)).all()
    result["diagnosis"] = [
        {
            "diagnosis_id": d.diagnosis_id,
            "patient_id": d.patient_id,
            "first_name": d.patient.first_name if d.patient else None,
            "diagnosis_date": d.diagnosis_date,
            "condition_name": d.condition.condition_name if d.condition else None,
            "file_id": d.file_id
        } for d in diagnoses
    ]

    lab_results = db.query(LabResult).options(joinedload(LabResult.patient)).all()
    result["lab_result"] = [
        reorder_fields({
            "result_id": lr.result_id,
            "patient_id": lr.patient_id,
            "first_name": lr.patient.first_name if lr.patient else None,
            "test_name": lr.test_name,
            "test_value": lr.test_value,
            "unit": lr.unit,
            "test_date": lr.test_date,
            "file_id": lr.file_id
        }, [
            "result_id", "patient_id", "first_name", "test_name",
            "test_value", "unit", "test_date", "file_id"
        ]) for lr in lab_results
    ]

    treatments = db.query(Treatment).options(joinedload(Treatment.patient)).all()
    result["treatment"] = [
        reorder_fields({
            "treatment_id": t.treatment_id,
            "patient_id": t.patient_id,
            "first_name": t.patient.first_name if t.patient else None,
            "treatment_type": t.treatment_type,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "outcome": t.outcome,
            "file_id": t.file_id
        }, [
            "treatment_id", "patient_id", "first_name", "treatment_type",
            "start_date", "end_date", "outcome", "file_id"
        ]) for t in treatments
    ]

    hospitals = db.query(Hospital).all()
    result["hospital"] = [
        reorder_fields({
            "hospital_id": h.hospital_id,
            "hospital_name": h.hospital_name,
            "hospital_address": h.hospital_address,
            "file_id": h.file_id
        }, [
            "hospital_id", "hospital_name", "hospital_address", "file_id"
        ]) for h in hospitals
    ]

  
    histories = db.query(FamilyHistory).options(joinedload(FamilyHistory.condition), joinedload(FamilyHistory.patient)).all()
    result["family_history"] = [
        {
            "history_id": fh.history_id,
            "patient_id": fh.patient_id,
            "first_name": fh.patient.first_name if fh.patient else None,
            "relative": fh.relative,
            "condition_name": fh.condition.condition_name if fh.condition else None,
            "file_id": fh.file_id
        } for fh in histories
    ]

    return result
