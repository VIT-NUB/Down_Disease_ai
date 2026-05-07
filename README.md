# 🧬 Down Syndrome AI Diagnostic System (Down_AI)

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

## 📌 Project Overview
**Down_AI** is a fully automated, end-to-end medical pipeline designed to assist doctors in diagnosing and tracking the severity of Down Syndrome patients. 

The system allows patients or doctors to upload medical reports (Images, PDFs, Text documents). It automatically extracts the required medical vitals, handles incomplete data intelligently, analyzes the data using a Machine Learning model, and provides a severity risk score along with clinical recommendations. Furthermore, it tracks the patient's condition over time to monitor if they are improving or worsening.

---

## 🌟 Core Features

1. **Intelligent File Uploads (Images & Documents)**
   - Extracts data from **Images** (CBC, X-ray, Echo scans) using OCR (Tesseract & OpenCV).
   - Extracts data from **Text Documents** (PDFs, DOCX, TXT) using PyPDF2 and python-docx.
2. **Automated NLP Parsing**
   - Automatically understands and parses key parameters from raw unstructured text (e.g., Hemoglobin, WBC, TSH, Echo Score).
3. **Smart Data Validation & Missing Data Handling**
   - Discards completely illogical OCR readings (e.g., auto-correcting `Hemoglobin = 110` to `11.0`).
   - Penalizes model confidence if critical data is missing instead of blindly assuming healthy values.
   - Demands missing tests (like TSH or Echo) when necessary for a complete diagnosis.
4. **Machine Learning AI Model**
   - Uses a trained **Random Forest Classifier** to learn complex non-linear patterns (e.g., the dangerous interaction between High TSH and low Hb) instead of relying on simple rule-based logic.
5. **Time-Series Patient Tracking (History)**
   - Built-in SQLite database using SQLAlchemy.
   - Tracks a patient's historical uploads and calculates progress trends (**Improving 🟢, Worsening 🔴, Stable 🟡**).
6. **Flutter-Ready API**
   - A fully functional REST API built with FastAPI, ready to be consumed directly by a Flutter mobile application.

---

## 🛠️ Technology Stack & Libraries

### 1. Backend & API
* **FastAPI**: High-performance framework for building the REST API.
* **Uvicorn**: ASGI web server to run FastAPI.
* **SQLAlchemy**: ORM for database management.
* **SQLite**: Lightweight database to store patient cases.
* **python-multipart**: For handling file uploads in FastAPI.

### 2. OCR & Document Processing
* **OpenCV (`cv2`)**: For image pre-processing (noise reduction, thresholding) before OCR.
* **Pytesseract**: Optical Character Recognition to read text from medical images.
* **PyPDF2**: For extracting raw text from PDF medical reports.
* **python-docx**: For extracting text from Microsoft Word documents.

### 3. Machine Learning & Data Processing
* **Scikit-Learn**: Used for training the `RandomForestClassifier`.
* **Pandas**: Data manipulation and DataFrame structuring.
* **NumPy**: Numerical operations and array handling.
* **Pickle**: For saving and loading the trained ML model (`ds_severity_model.pkl`).

---

## 📊 The Dataset

The system relies on a dataset encompassing various clinical and laboratory features of patients. 

* **Type**: Tabular Data (CSV)
* **Features Included**:
  * `Age` (Years)
  * `Hemoglobin` (Blood)
  * `RBC_Count` (Blood)
  * `WBC_Count` (Blood)
  * `MCV` (Blood)
  * `TSH` (Thyroid Function)
  * `T4` (Thyroid Function)
  * `Echo_Abnormality_Score` (Heart Function - 0: Normal, 1: Mild, 2: Moderate, 3: Severe)
  * `Hearing_Loss_dB` (Audiology)
* **Target Variable**: `Severity` (Classified into: **Low**, **Medium**, **High**)

The ML model was trained on this dataset to discover hidden interactions between blood results and physical/organ abnormalities.

---

## 🌐 API Endpoints

The API is fully documented via Swagger UI. You can access the interactive UI at `http://localhost:8000/docs` when the server is running.

### 1. `GET /`
* **Description**: Health check endpoint.
* **Returns**: Welcome message ensuring the server is running.

### 2. `POST /predict`
* **Description**: The core prediction pipeline. Accepts medical files, extracts text, runs the AI model, saves to DB, and returns the diagnosis.
* **Parameters**:
  * `image_file` (Optional, File): Medical image.
  * `document_file` (Optional, File): Medical PDF/DOCX.
  * `patient_name` (Form String): Name of the patient.
* **Returns JSON**:
  * `success`: Boolean
  * `diagnosis` / `risk_level`: e.g., "High", "Medium", "Low", or "Incomplete".
  * `confidence_percentage`: Model confidence.
  * `recommendation`: Clinical action needed.
  * `chart_data`: Array of probabilities intended for Flutter UI rendering.

### 3. `GET /patient/{patient_name}/history`
* **Description**: Retrieves all historical assessments for a specific patient and calculates their clinical progress trend.
* **Returns JSON**:
  * `total_assessments`: Number of visits.
  * `current_status`: Latest Risk level.
  * `latest_trend`: "Improving 🟢", "Worsening 🔴", or "Stable 🟡".
  * `history`: Array of all previous visits and their results.

### 4. `GET /history`
* **Description**: Fetches all patient cases stored in the database.

---

## 🚀 How to Run the Project

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the API Server**
   ```bash
   python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the Documentation**
   Open your browser and navigate to:
   [http://localhost:8000/docs](http://localhost:8000/docs)

---
*Developed with ❤️ as a robust Graduation Project for Down Syndrome Assessment.*
