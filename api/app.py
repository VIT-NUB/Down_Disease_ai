from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
from sqlalchemy.orm import Session # type: ignore

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.parse_text import parse_cbc_report
from models.predict import predict_severity

# Import database
from database import PatientCase, get_db

app = FastAPI(title="Down Syndrome AI API", description="API for predicting Down Syndrome severity from medical reports")

# Allow CORS for Flutter app to connect from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional



@app.get("/history")
def get_all_history(db: Session = Depends(get_db)):
    """
    Get all previously saved patient cases.
    """
    cases = db.query(PatientCase).order_by(PatientCase.created_at.desc()).all()
    return {"success": True, "cases": cases}

@app.get("/patient/{patient_name}/history")
def get_patient_history(patient_name: str, db: Session = Depends(get_db)):
    """
    Get the historical assessments for a specific patient to track progress (Improving, Stable, Worsening).
    """
    cases = db.query(PatientCase).filter(PatientCase.patient_name == patient_name).order_by(PatientCase.created_at.asc()).all()
    
    if not cases:
        return {"success": False, "message": "No history found for this patient."}
        
    history = []
    severity_map = {"Low": 1, "Medium": 2, "High": 3, "Incomplete": 0}
    
    for i, case in enumerate(cases):
        trend = "Initial Assessment"
        if i > 0:
            prev_severity = severity_map.get(cases[i-1].risk_level, 0)
            curr_severity = severity_map.get(case.risk_level, 0)
            
            if curr_severity == 0 or prev_severity == 0:
                trend = "N/A (Incomplete Data)"
            elif curr_severity < prev_severity:
                trend = "Improving 🟢"
            elif curr_severity > prev_severity:
                trend = "Worsening 🔴"
            else:
                trend = "Stable 🟡"
                
        history.append({
            "id": case.id,
            "date": case.created_at,
            "diagnosis": case.diagnosis,
            "risk_level": case.risk_level,
            "confidence_percentage": round(case.confidence, 2) if case.confidence else 0.0,
            "trend": trend
        })
        
    latest = history[-1]
    
    return {
        "success": True,
        "patient_name": patient_name,
        "total_assessments": len(cases),
        "current_status": latest["risk_level"],
        "latest_trend": latest["trend"],
        "history": history
    }

from pydantic import BaseModel

class FollowUpRequest(BaseModel):
    patient_name: str
    vitals: dict = {}
    latest_lab_text: str = ""
    latest_chat_text: str = ""

@app.post("/auto_analyze_followup")
async def auto_analyze_followup(data: FollowUpRequest, db: Session = Depends(get_db)):
    """
    Automatically analyzes a patient's state based on Follow-up sections:
    1. Lab Reports
    2. Files & Documents
    3. Progress & Vitals
    4. Chat with Doctor
    Returns only the severity state (Low, Medium, High) to be sent to the doctor.
    """
    try:
        # 1. Simulate AI reading from the 4 sections
        # In a real scenario, we query the DB for the latest vitals, chat logs, and parsed OCR from files.
        raw_text = data.latest_lab_text + "\n" + data.latest_chat_text
        parsed_data = parse_cbc_report(raw_text)
        
        # Merge vitals into parsed data (e.g., Heart Rate mapped to Echo, etc.)
        for k, v in data.vitals.items():
            parsed_data[k] = v
            
        # 2. Run Prediction Model
        result = predict_severity(parsed_data)
        severity = result['Prediction'] # 'Low', 'Medium', or 'High'
        
        # 3. Save to History silently
        new_case = PatientCase(
            patient_name=data.patient_name,
            filename="Auto-Analyzed from Follow-up Sections",
            extracted_data=parsed_data,
            diagnosis=severity,
            risk_level=severity,
            confidence=result['Confidence'] * 100,
            recommendation="Auto-generated from Follow-up data."
        )
        db.add(new_case)
        db.commit()
        
        # Return ONLY the severity state as requested
        return {
            "success": True,
            "patient_name": data.patient_name,
            "severity_state": severity
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/")
def read_root():
    return {"message": "Down Syndrome AI API is running with Database support!"}

if __name__ == "__main__":
    print("Starting API Server on http://0.0.0.0:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
