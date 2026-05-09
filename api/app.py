from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import datetime
from sqlalchemy.orm import Session # type: ignore
from pydantic import BaseModel
from typing import Optional

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.parse_text import parse_cbc_report
from models.predict import predict_severity

# Import database models
from .database import PatientCase, Patient, PatientHistory, DoctorReminder, get_db
app = FastAPI(title="Down Syndrome AI API", description="API for predicting Down Syndrome severity from medical reports")

# Allow CORS for Flutter app to connect from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/patients")
def get_all_patients(db: Session = Depends(get_db)):
    """
    Get all patients with their latest status and trend.
    """
    patients = db.query(Patient).order_by(Patient.updated_at.desc()).all()
    return {"success": True, "patients": patients}

@app.get("/patient/{patient_name}/history")
def get_patient_history(patient_name: str, db: Session = Depends(get_db)):
    """
    Get the historical assessments for a specific patient to track progress (Improving, Stable, Worsening).
    """
    patient = db.query(Patient).filter(Patient.patient_name == patient_name).first()
    
    if not patient:
        return {"success": False, "message": "No history found for this patient."}
        
    history_records = db.query(PatientHistory).filter(PatientHistory.patient_id == patient.id).order_by(PatientHistory.created_at.asc()).all()
    
    history_list = []
    for case in history_records:
        history_list.append({
            "id": case.id,
            "date": case.created_at,
            "record_source": case.record_source,
            "ai_diagnosis": case.ai_diagnosis,
            "confidence_percentage": round(case.confidence, 2) if case.confidence else 0.0,
            "recommendation": case.recommendation
        })
        
    return {
        "success": True,
        "patient_name": patient.patient_name,
        "disease_type": patient.disease_type,
        "current_status": patient.latest_ai_status,
        "latest_trend": patient.status_trend,
        "total_assessments": len(history_records),
        "history": history_list
    }

@app.get("/patient/{patient_name}/reminders")
def get_patient_reminders(patient_name: str, db: Session = Depends(get_db)):
    """
    Get active reminders for a specific patient.
    """
    patient = db.query(Patient).filter(Patient.patient_name == patient_name).first()
    if not patient:
        return {"success": False, "message": "Patient not found."}
        
    reminders = db.query(DoctorReminder).filter(
        DoctorReminder.patient_id == patient.id,
        DoctorReminder.is_resolved == False
    ).order_by(DoctorReminder.created_at.desc()).all()
    
    return {"success": True, "reminders": reminders}


class FollowUpRequest(BaseModel):
    patient_name: str
    vitals: dict = {}
    latest_lab_text: str = ""
    latest_chat_text: str = ""

@app.post("/auto_analyze_followup")
async def auto_analyze_followup(data: FollowUpRequest, db: Session = Depends(get_db)):
    """
    Automatically analyzes a patient's state based on Follow-up sections.
    Creates a new history record and updates the patient's trend.
    Also creates a Doctor Reminder if the condition worsens.
    """
    try:
        # 1. Parse texts
        raw_text = data.latest_lab_text + "\n" + data.latest_chat_text
        parsed_data = parse_cbc_report(raw_text)
        
        # Merge vitals
        for k, v in data.vitals.items():
            parsed_data[k] = v
            
        # 2. Run Prediction Model
        result = predict_severity(parsed_data)
        severity = result['Prediction'] # 'Low', 'Medium', or 'High'
        confidence = result['Confidence'] * 100
        
        # 3. Find or Create Patient
        patient = db.query(Patient).filter(Patient.patient_name == data.patient_name).first()
        is_new_patient = False
        
        if not patient:
            patient = Patient(
                patient_name=data.patient_name,
                latest_ai_status=severity,
                status_trend="Stable"
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            is_new_patient = True

        # 4. Calculate Trend if it's an existing patient
        trend = patient.status_trend
        if not is_new_patient:
            severity_map = {"Low": 1, "Medium": 2, "High": 3, "Unknown": 0}
            prev_sev = severity_map.get(patient.latest_ai_status, 0)
            curr_sev = severity_map.get(severity, 0)
            
            if curr_sev != 0 and prev_sev != 0:
                if curr_sev < prev_sev:
                    trend = "Improving 🟢"
                elif curr_sev > prev_sev:
                    trend = "Worsening 🔴"
                else:
                    trend = "Stable 🟡"
            
            # Update patient latest status
            patient.latest_ai_status = severity
            patient.status_trend = trend
            patient.updated_at = datetime.datetime.utcnow()
            db.commit()

        # 5. Add Patient History Record
        history_record = PatientHistory(
            patient_id=patient.id,
            record_source="Auto-Analyzed Follow-up",
            extracted_medical_features=parsed_data,
            vitals_history=data.vitals,
            chat_notes_or_symptoms=data.latest_chat_text,
            ai_diagnosis=severity,
            confidence=confidence,
            recommendation="Auto-generated from Follow-up data."
        )
        db.add(history_record)
        
        # 6. Create a Reminder if Worsening
        if "Worsening" in trend:
            reminder = DoctorReminder(
                patient_id=patient.id,
                reminder_type="Deterioration Alert",
                reminder_text=f"Patient {patient.patient_name}'s condition has worsened to {severity}. Please review."
            )
            db.add(reminder)
            
        db.commit()
        
        return {
            "success": True,
            "patient_name": patient.patient_name,
            "severity_state": severity,
            "trend": trend
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/")
def read_root():
    return {"message": "Down Syndrome AI API is running with Advanced DB support!"}

if __name__ == "__main__":
    print("Starting API Server on http://0.0.0.0:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
