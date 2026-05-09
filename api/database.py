from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker, relationship # type: ignore
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'cases_v2.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ----------------- OLD TABLE (Kept for backward compatibility) -----------------
class PatientCase(Base):
    __tablename__ = "patient_cases"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, default="Unknown")
    filename = Column(String)
    extracted_data = Column(JSON)
    diagnosis = Column(String) # High, Medium, Low
    risk_level = Column(String) # Same as diagnosis or custom
    confidence = Column(Float)
    recommendation = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ----------------- NEW TABLES -----------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, index=True)
    disease_type = Column(String, default="Down Syndrome")
    latest_ai_status = Column(String, default="Unknown") # Low, Medium, High
    status_trend = Column(String, default="Stable") # Improving, Stable, Worsening
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    history = relationship("PatientHistory", back_populates="patient", cascade="all, delete-orphan")
    reminders = relationship("DoctorReminder", back_populates="patient", cascade="all, delete-orphan")

class PatientHistory(Base):
    __tablename__ = "patient_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    record_source = Column(String) # e.g., 'Lab Report', 'X-Ray', 'Vitals', 'Chat'
    uploaded_reports = Column(String, nullable=True) # File path or name
    extracted_medical_features = Column(JSON, nullable=True)
    vitals_history = Column(JSON, nullable=True)
    chat_notes_or_symptoms = Column(String, nullable=True)
    ai_diagnosis = Column(String, nullable=True) # Low, Medium, High
    confidence = Column(Float, nullable=True)
    recommendation = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="history")

class DoctorReminder(Base):
    __tablename__ = "doctor_reminders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    reminder_type = Column(String) # e.g., 'Deterioration Alert', 'Follow-up'
    reminder_text = Column(String)
    reminder_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="reminders")

Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
