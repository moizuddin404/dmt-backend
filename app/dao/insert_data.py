from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.core import (
    Patient, Hospital, Lifestyle, LabResult,
    Treatment, Diagnosis, FamilyHistory,
    patient_conditions, FileUploadLog
)
from app.dao.insert_medical_conditions import get_or_create_condition
from app.utils import filter_valid_columns, parse_date
from datetime import datetime, date

def extract_value(row: dict, col_info):
    if isinstance(col_info, list):
        values = [row.get(col, "") for col in col_info]
        merged_val = " ".join(str(v).strip() for v in values if v)
        return merged_val or None
    elif isinstance(col_info, str) and col_info:
        val = row.get(col_info, None)
        return val if val != '' else None
    return None

def insert_data_to_tables(mapping: dict, sample_data: list, db: Session, file_id: int):
    try:
        for row in sample_data:
            hospital_mapping = mapping.get("hospital", {})
            hospital_data = {
                attr: extract_value(row, col_info)
                for attr, col_info in hospital_mapping.items()
            }

            hospital = None
            if any(v is not None for v in hospital_data.values()):
                hospital = db.query(Hospital).filter_by(
                    hospital_name=hospital_data.get("hospital_name"),
                    hospital_address=hospital_data.get("hospital_address")
                ).first()
                if not hospital:
                    hospital_data["file_id"] = file_id
                    hospital = Hospital(**filter_valid_columns(Hospital, hospital_data))
                    db.add(hospital)
                    db.flush()

            patient_mapping = mapping.get("patient", {})
            patient_data = {
                attr: extract_value(row, col_info)
                for attr, col_info in patient_mapping.items()
            }

            if hospital:
                patient_data["hospital_id"] = hospital.hospital_id
            patient_data["file_id"] = file_id

            patient = Patient(**filter_valid_columns(Patient, patient_data))
            db.add(patient)
            db.flush()

            lifestyle_mapping = mapping.get("lifestyle", {})
            lifestyle_data = {
                attr: extract_value(row, col_info)
                for attr, col_info in lifestyle_mapping.items()
            }

            if any(v is not None for v in lifestyle_data.values()):
                lifestyle_data["patient_id"] = patient.patient_id
                lifestyle_data["file_id"] = file_id
                lifestyle = Lifestyle(**filter_valid_columns(Lifestyle, lifestyle_data))
                db.add(lifestyle)

            lab_mapping = mapping.get("lab_result", {})
            lab_data = {}
            for attr, col_info in lab_mapping.items():
                val = extract_value(row, col_info)
                if "date" in attr and val:
                    val = parse_date(val)
                lab_data[attr] = val

            if any(v is not None for v in lab_data.values()):
                lab_data["patient_id"] = patient.patient_id
                lab_data["file_id"] = file_id
                lab_result = LabResult(**filter_valid_columns(LabResult, lab_data))
                db.add(lab_result)

            treatment_mapping = mapping.get("treatment", {})
            treatment_data = {}
            for attr, col_info in treatment_mapping.items():
                val = extract_value(row, col_info)
                if "date" in attr and val:
                    val = parse_date(val)
                treatment_data[attr] = val

            if any(v is not None for v in treatment_data.values()):
                treatment_data["patient_id"] = patient.patient_id
                treatment_data["file_id"] = file_id
                treatment = Treatment(**filter_valid_columns(Treatment, treatment_data))
                db.add(treatment)

            diagnosis_mapping = mapping.get("diagnosis", {})
            diagnosis_data = {}
            for attr, col_info in diagnosis_mapping.items():
                if attr == "condition_id" or attr == "condition_name":
                    condition_name = extract_value(row, col_info)
                    if condition_name:
                        diagnosis_data["condition_id"] = get_or_create_condition(db, condition_name)
                else:
                    val = extract_value(row, col_info)
                    if "diagnosis_date" in attr and val:
                        print(f"Trying to parse diagnosis_date value: {val}")
                        val = parse_date(val)
                        print(f"Parsed date: {val}")

                    #debug
                    print(f"Extracted {attr}: {val} from row: {row}")
                    diagnosis_data[attr] = val

            if any(v is not None for v in diagnosis_data.values()):
                diagnosis_data["patient_id"] = patient.patient_id
                diagnosis_data["file_id"] = file_id
                diagnosis = Diagnosis(**filter_valid_columns(Diagnosis, diagnosis_data))
                db.add(diagnosis)

            history_mapping = mapping.get("family_history", {})
            history_data = {}
            for attr, col_info in history_mapping.items():
                if attr == "condition_id" or attr == "condition_name":
                    condition_name = extract_value(row, col_info)
                    if condition_name:
                        history_data["condition_id"] = get_or_create_condition(db, condition_name)
                else:
                    val = extract_value(row, col_info)
                    history_data[attr] = val

            if any(v is not None for v in history_data.values()):
                history_data["patient_id"] = patient.patient_id
                history_data["file_id"] = file_id
                family_history = FamilyHistory(**filter_valid_columns(FamilyHistory, history_data))
                db.add(family_history)

            pc_mapping = (
                mapping.get("medical_condition")
                or mapping.get("diagnosis")
                or mapping.get("family_history")
                or {}
            )
            for attr, col_info in pc_mapping.items():
                if attr == "condition_name" or attr == "condition_id":
                    condition_names_str = extract_value(row, col_info)
                    if condition_names_str:
                        condition_list = [c.strip() for c in condition_names_str.split(",") if c.strip()]
                        for cname in condition_list:
                            condition_id = get_or_create_condition(db, cname)
                            db.execute(patient_conditions.insert().values(
                                patient_id=patient.patient_id,
                                condition_id=condition_id
                            ))

        db.commit()
        return file_id

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error during data insertion: {e}")
        raise e
