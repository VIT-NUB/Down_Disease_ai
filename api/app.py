from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import datetime
from sqlalchemy.orm import Session  # type: ignore
from pydantic import BaseModel

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.parse_text import parse_cbc_report
from ocr.extract_text import extract_text_from_file
from models.predict import predict_severity

# Import database models
from api.database import PatientCase, Patient, PatientHistory, DoctorReminder, get_db


app = FastAPI(
    title="Down Syndrome AI API",
    description="API for predicting Down Syndrome severity from medical reports"
)

# Allow CORS for Flutter / Backend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Helpers
# =========================

def get_or_create_patient(db: Session, patient_name: str, severity: str):
    patient = db.query(Patient).filter(Patient.patient_name == patient_name).first()
    is_new_patient = False

    if not patient:
        patient = Patient(
            patient_name=patient_name,
            disease_type="Down Syndrome",
            latest_ai_status=severity,
            status_trend="Stable"
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        is_new_patient = True

    return patient, is_new_patient


def calculate_trend(previous_status: str, current_status: str):
    severity_map = {
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Unknown": 0
    }

    prev_sev = severity_map.get(previous_status, 0)
    curr_sev = severity_map.get(current_status, 0)

    if curr_sev == 0 or prev_sev == 0:
        return "Stable"

    if curr_sev < prev_sev:
        return "Improving"
    elif curr_sev > prev_sev:
        return "Worsening"
    else:
        return "Stable"


# =========================
# Patients APIs
# =========================

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
    Get the historical assessments for a specific patient.
    """
    patient = db.query(Patient).filter(Patient.patient_name == patient_name).first()

    if not patient:
        return {"success": False, "message": "No history found for this patient."}

    history_records = (
        db.query(PatientHistory)
        .filter(PatientHistory.patient_id == patient.id)
        .order_by(PatientHistory.created_at.asc())
        .all()
    )

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

    reminders = (
        db.query(DoctorReminder)
        .filter(
            DoctorReminder.patient_id == patient.id,
            DoctorReminder.is_resolved == False
        )
        .order_by(DoctorReminder.created_at.desc())
        .all()
    )

    return {"success": True, "reminders": reminders}


# =========================
# Text Follow-up Analysis
# =========================

class FollowUpRequest(BaseModel):
    patient_name: str
    vitals: dict = {}
    latest_lab_text: str = ""
    latest_chat_text: str = ""


@app.post("/auto_analyze_followup")
async def auto_analyze_followup(data: FollowUpRequest, db: Session = Depends(get_db)):
    """
    Analyze patient follow-up data from text/vitals/chat notes.
    """
    try:
        raw_text = data.latest_lab_text + "\n" + data.latest_chat_text
        parsed_data = parse_cbc_report(raw_text)

        for k, v in data.vitals.items():
            parsed_data[k] = v

        result = predict_severity(parsed_data)
        severity = result["Prediction"]
        confidence = result["Confidence"] * 100

        patient, is_new_patient = get_or_create_patient(db, data.patient_name, severity)

        trend = patient.status_trend

        if not is_new_patient:
            trend = calculate_trend(patient.latest_ai_status, severity)
            patient.latest_ai_status = severity
            patient.status_trend = trend
            patient.updated_at = datetime.datetime.utcnow()
            db.commit()

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

        if trend == "Worsening":
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
            "trend": trend,
            "confidence_percentage": round(confidence, 2),
            "extracted_features": parsed_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# =========================
# File Upload Prediction
# =========================

@app.post("/predict")
async def predict_patient_status(
    file: UploadFile = File(...),
    patient_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Receive uploaded medical file, extract text, analyze values,
    predict severity, save patient history, and return AI status.

    Supported files:
    - PDF
    - Images
    - TXT
    - DOCX
    """
    try:
        file_bytes = await file.read()

        extracted_text = extract_text_from_file(file_bytes, file.filename)

        if not extracted_text.strip():
            return {
                "success": False,
                "message": "Could not extract text from uploaded file.",
                "filename": file.filename
            }

        parsed_data = parse_cbc_report(extracted_text)

        if not parsed_data:
            return {
                "success": False,
                "message": "Text extracted, but no medical values were detected.",
                "filename": file.filename,
                "extracted_text_preview": extracted_text[:500]
            }

        result = predict_severity(parsed_data)
        severity = result["Prediction"]
        confidence = result["Confidence"] * 100

        patient, is_new_patient = get_or_create_patient(db, patient_name, severity)

        trend = patient.status_trend

        if not is_new_patient:
            trend = calculate_trend(patient.latest_ai_status, severity)
            patient.latest_ai_status = severity
            patient.status_trend = trend
            patient.updated_at = datetime.datetime.utcnow()
            db.commit()

        history_record = PatientHistory(
            patient_id=patient.id,
            record_source="Uploaded Medical File",
            uploaded_reports=file.filename,
            extracted_medical_features=parsed_data,
            ai_diagnosis=severity,
            confidence=confidence,
            recommendation="Auto-generated from uploaded medical file."
        )

        db.add(history_record)

        if trend == "Worsening":
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
            "filename": file.filename,
            "severity_state": severity,
            "trend": trend,
            "confidence_percentage": round(confidence, 2),
            "extracted_features": parsed_data,
            "message": "File analyzed successfully and saved to patient history."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# =========================
# Root
# =========================

@app.get("/")
def read_root():
    return {
        "message": "Down Syndrome AI API is running with Advanced DB and File Upload support!"
    }


# =========================
# Server Startup
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting API Server on http://0.0.0.0:{port}")
    uvicorn.run("api.app:app", host="0.0.0.0", port=port)