from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime

# ----------------------------
# Hospital
# ----------------------------

class HospitalBase(BaseModel):
    hospital_name: str
    hospital_address: str

class HospitalCreate(HospitalBase):
    pass

class Hospital(HospitalBase):
    hospital_id: int

    class Config:
        orm_mode = True


# ----------------------------
# Medical Condition
# ----------------------------

class MedicalConditionBase(BaseModel):
    condition_name: str

class MedicalConditionCreate(MedicalConditionBase):
    pass

class MedicalCondition(MedicalConditionBase):
    condition_id: int

    class Config:
        orm_mode = True


# ----------------------------
# Patient
# ----------------------------

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: Optional[str]
    email: Optional[EmailStr]
    address: Optional[str]
    country: Optional[str]
    hospital_id: Optional[int]

class PatientCreate(PatientBase):
    condition_ids: Optional[List[int]] = []

class Patient(PatientBase):
    patient_id: int
    conditions: List[MedicalCondition] = []

    class Config:
        orm_mode = True


# ----------------------------
# Family History
# ----------------------------

class FamilyHistoryBase(BaseModel):
    relative: str
    condition_id: int

class FamilyHistoryCreate(FamilyHistoryBase):
    patient_id: int

class FamilyHistory(FamilyHistoryBase):
    history_id: int

    class Config:
        orm_mode = True


# ----------------------------
# Diagnosis
# ----------------------------

class DiagnosisBase(BaseModel):
    diagnosis_date: date
    condition_id: int

class DiagnosisCreate(DiagnosisBase):
    patient_id: int

class Diagnosis(DiagnosisBase):
    diagnosis_id: int

    class Config:
        orm_mode = True


# ----------------------------
# Treatment
# ----------------------------

class TreatmentBase(BaseModel):
    treatment_type: str
    start_date: date
    end_date: Optional[date]
    outcome: Optional[str]

class TreatmentCreate(TreatmentBase):
    patient_id: int

class Treatment(TreatmentBase):
    treatment_id: int

    class Config:
        orm_mode = True


# ----------------------------
# Lifestyle
# ----------------------------

class LifestyleBase(BaseModel):
    smoking_status: Optional[str]
    alcohol_use: Optional[str]
    exercise_habit: Optional[str]
    diet: Optional[str]

class LifestyleCreate(LifestyleBase):
    patient_id: int

class Lifestyle(LifestyleBase):
    lifestyle_id: int

    class Config:
        orm_mode = True


# ----------------------------
# Lab Result
# ----------------------------

class LabResultBase(BaseModel):
    test_name: str
    test_value: str
    unit: str
    test_date: date

class LabResultCreate(LabResultBase):
    patient_id: int

class LabResult(LabResultBase):
    result_id: int

    class Config:
        orm_mode = True


# ----------------------------
# File Upload Log
# ----------------------------

class FileUploadLogBase(BaseModel):
    filename: str
    file_type: str
    status: str
    mapped_tables: Optional[List[str]] = []
    mapped_columns: Optional[List[str]] = []
    missing_columns: Optional[List[str]] = []
    extra_columns: Optional[List[str]] = []
    empty_cells: Optional[int]
    invalid_types: Optional[List[str]] = []
    total_rows: Optional[int]
    local_path: Optional[str]

class FileUploadLogCreate(FileUploadLogBase):
    pass

class FileUploadLog(FileUploadLogBase):
    file_id: int
    upload_time: Optional[datetime]

    class Config:
        orm_mode = True
