# app/models/core.py
from sqlalchemy import (
    FLOAT, Column, Integer, Text, Date, ForeignKey, Table, TIMESTAMP, ARRAY, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Junction table for patient and their conditions
patient_conditions = Table(
    "patient_condition",
    Base.metadata,
    Column("patient_id", Integer, ForeignKey("patient.patient_id"), primary_key=True),
    Column("condition_id", Integer, ForeignKey("medical_condition.condition_id"), primary_key=True),
)

# Hospital
class Hospital(Base):
    __tablename__ = "hospital"
    hospital_id = Column(Integer, primary_key=True)
    hospital_name = Column(Text)
    hospital_address = Column(Text)
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    patients = relationship("Patient", back_populates="hospital")

# Patients
class Patient(Base):
    __tablename__ = "patient"
    patient_id = Column(Integer, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)
    date_of_birth = Column(Date)
    gender = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    country = Column(Text)
    hospital_id = Column(Integer, ForeignKey("hospital.hospital_id"))
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    hospital = relationship("Hospital", back_populates="patients")
    diagnoses = relationship("Diagnosis", back_populates="patient", cascade="all, delete")
    histories = relationship("FamilyHistory", back_populates="patient", cascade="all, delete")
    treatments = relationship("Treatment", back_populates="patient", cascade="all, delete")
    lifestyle = relationship("Lifestyle", uselist=False, back_populates="patient", cascade="all, delete")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete")
    conditions = relationship("Condition", secondary=patient_conditions, back_populates="patients")

# Conditions Table
class Condition(Base):
    __tablename__ = "medical_condition"
    condition_id = Column(Integer, primary_key=True)
    condition_name = Column(Text)

    patients = relationship("Patient", secondary=patient_conditions, back_populates="conditions")

# Dependent tables: family_history, diagnosis, treatments, lifestyle, lab_results
class FamilyHistory(Base):
    __tablename__ = "family_history"
    history_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"))
    relative = Column(Text)
    condition_id = Column(Integer, ForeignKey("medical_condition.condition_id"))
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    patient = relationship("Patient", back_populates="histories")
    condition = relationship("Condition")

class Diagnosis(Base):
    __tablename__ = "diagnosis"
    diagnosis_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"))
    diagnosis_date = Column(Date)
    condition_id = Column(Integer, ForeignKey("medical_condition.condition_id"))
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    patient = relationship("Patient", back_populates="diagnoses")
    condition = relationship("Condition")

class Treatment(Base):
    __tablename__ = "treatment"
    treatment_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"))
    treatment_type = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    outcome = Column(Text)
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    patient = relationship("Patient", back_populates="treatments")

class Lifestyle(Base):
    __tablename__ = "lifestyle"
    lifestyle_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"))
    smoking_status = Column(Text)
    alcohol_use = Column(Text)
    exercise_habit = Column(Text)
    diet = Column(Text)
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    patient = relationship("Patient", back_populates="lifestyle")

class LabResult(Base):
    __tablename__ = "lab_result"
    result_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patient.patient_id"))
    test_name = Column(Text)
    test_value = Column(Text)
    unit = Column(Text)
    test_date = Column(Date)
    file_id = Column(Integer, ForeignKey("file_upload_log.file_id"))

    patient = relationship("Patient", back_populates="lab_results")

# Upload audit
class FileUploadLog(Base):
    __tablename__ = "file_upload_log"
    file_id = Column(Integer, primary_key=True)
    filename = Column(Text)
    file_type = Column(Text)
    upload_time = Column(TIMESTAMP, server_default=func.now())
    status = Column(Text)
    mapped_tables = Column(ARRAY(Text))
    mapped_columns = Column(ARRAY(Text))
    missing_columns = Column(ARRAY(Text))
    extra_columns = Column(ARRAY(Text))
    empty_cells = Column(Integer)
    total_rows = Column(Integer)
    local_path = Column(Text)
    total_input_columns = Column(Integer)
    file_size = Column(FLOAT)
