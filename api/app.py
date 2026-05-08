from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import shutil
import os
import sys
from sqlalchemy.orm import Session # type: ignore

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.extract_text import extract_text_from_file
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

@app.post("/predict")
async def predict_patient_status(
    image_file: Optional[UploadFile] = File(None, description="Upload medical images (PNG, JPG, etc.)"),
    document_file: Optional[UploadFile] = File(None, description="Upload medical documents (PDF, DOCX, TXT)"),
    patient_name: str = Form("Unknown"),
    db: Session = Depends(get_db)
):
    """
    Receives an image and/or a document, automatically extracts text,
    predicts severity, generates recommendation, and saves case to database.
    """
    if not image_file and not document_file:
        return {"success": False, "error": "Please upload at least one file (image or document)."}
        
    raw_text = ""
    temp_files = []
    filenames = []
        
    try:
        from ocr.extract_text import extract_text_from_file
        
        # 1. Save and extract from image if provided
        if image_file:
            temp_img_path = f"temp_img_{image_file.filename}"
            with open(temp_img_path, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
            temp_files.append(temp_img_path)
            filenames.append(image_file.filename)
            raw_text += extract_text_from_file(temp_img_path) + "\n"
            
        # 2. Save and extract from document if provided
        if document_file:
            temp_doc_path = f"temp_doc_{document_file.filename}"
            with open(temp_doc_path, "wb") as buffer:
                shutil.copyfileobj(document_file.file, buffer)
            temp_files.append(temp_doc_path)
            filenames.append(document_file.filename)
            raw_text += extract_text_from_file(temp_doc_path) + "\n"
        
        # 3. Parse Data (Fully Automated)
        parsed_data = parse_cbc_report(raw_text)
        
        # 4. Run Prediction Model (passing only what OCR found)
        result = predict_severity(parsed_data)
        severity = result['Prediction']
        confidence = result['Confidence'] * 100
        missing = result['Missing_Features']
        
        # 5. Generate Recommendation and Risk Level based on completeness
        critical_missing = [f for f in ['TSH', 'Echo_Abnormality_Score', 'Hearing_Loss_dB'] if f in missing]
        
        if critical_missing:
            severity = "Incomplete"
            recommendation = f"Assessment Incomplete. Missing Data: {', '.join(critical_missing)}. Please provide Thyroid and Echo/Hearing panels for a confident diagnosis."
        else:
            if severity == 'High':
                recommendation = "URGENT: High risk detected. Immediate medical intervention and follow-up required."
            elif severity == 'Medium':
                recommendation = "WARNING: Moderate risk. Close monitoring of Thyroid/Heart/Blood recommended."
            else:
                recommendation = "NORMAL: Stable condition. Proceed with regular check-ups."
            
        # 6. Format response for Flutter Charts
        chart_data = [
            {"status": k, "percentage": round(v * 100, 2)} 
            for k, v in result['All_Probabilities'].items()
        ]
        
        # 7. Save to Database
        new_case = PatientCase(
            patient_name=patient_name,
            filename=" | ".join(filenames),
            extracted_data=parsed_data,
            diagnosis=severity,
            risk_level=severity,
            confidence=confidence,
            recommendation=recommendation
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        
        return {
            "success": True,
            "id": new_case.id,
            "diagnosis": severity,
            "risk_level": severity,
            "confidence_percentage": round(confidence, 2),
            "recommendation": recommendation,
            "chart_data": chart_data,
            "extracted_features": result['Used_Features'],
            "message": "Prediction successful and saved to database"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

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
