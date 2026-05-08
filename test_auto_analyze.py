import sys
import os

# أضف مسار المشروع الرئيسي
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# أضف مسار مجلد الـ API عشان ملفات قاعدة البيانات تشتغل
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api'))

from api.app import app
from fastapi.testclient import TestClient
import json

client = TestClient(app)

# ده نموذج للداتا اللي المفروض الآب (Flutter) يبعتها في الخلفية
payload = {
    "patient_name": "Ali Ahmed",
    "vitals": {
        "Echo_Abnormality_Score": 2, # من قسم Progress & Vitals (مشكلة في القلب)
        "Hearing_Loss_dB": 45 # من قسم الفايلات (ضعف سمع)
    },
    "latest_lab_text": "WBC Count is 13000. Hemoglobin is 9.0.", # من قسم Lab Reports (كرات دم بيضاء عالية وهيموجلوبين قليل)
    "latest_chat_text": "The patient is constantly tired and TSH is 6.5" # من قسم الشات 
}

print("Sending Follow-up Data to AI for Background Analysis...")
print("-" * 50)
response = client.post("/auto_analyze_followup", json=payload)

print("AI Response to the Doctor Dashboard:")
print(json.dumps(response.json(), indent=2))
