import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import SessionLocal, Patient, PatientHistory

def test_db():
    db = SessionLocal()
    try:
        # Create a test patient
        patient = Patient(patient_name="Ahmed Ali", latest_ai_status="Medium", status_trend="Stable")
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        # Add history
        history = PatientHistory(
            patient_id=patient.id,
            record_source="Initial Setup",
            ai_diagnosis="Medium",
            confidence=85.5
        )
        db.add(history)
        db.commit()
        
        print("Test patient added successfully!")
        
        # Verify
        p = db.query(Patient).first()
        print(f"Patient in DB: {p.patient_name}, Status: {p.latest_ai_status}")
        
        h = db.query(PatientHistory).filter(PatientHistory.patient_id == p.id).all()
        print(f"Total History Records: {len(h)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
