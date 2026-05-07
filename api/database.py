from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./cases.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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

Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
