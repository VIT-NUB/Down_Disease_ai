import pandas as pd
import numpy as np
import pickle
import os


def predict_severity(patient_data):
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ds_severity_model.pkl')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}.")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    features = ['Age', 'Hemoglobin', 'RBC_Count', 'WBC_Count', 'MCV', 'TSH', 'T4', 'Echo_Abnormality_Score', 'Hearing_Loss_dB']
    defaults = {'Age': 10, 'Hemoglobin': 12.0, 'RBC_Count': 4.5, 'WBC_Count': 7000, 'MCV': 85.0, 'TSH': 1.5, 'T4': 1.2, 'Echo_Abnormality_Score': 0, 'Hearing_Loss_dB': 10}
    input_data = {}
    missing_features = []
    for feature in features:
        val = None
        for k, v in patient_data.items():
            if k.startswith(feature) or (feature == 'Hemoglobin' and 'Hb' in k):
                val = v
                break
        if val is not None:
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = None
        if val is not None and feature == 'Hemoglobin' and val > 30:
            val = val / 10.0
        if val is not None and feature == 'WBC_Count' and val < 100:
            val = val * 1000
        if val is None:
            missing_features.append(feature)
            input_data[feature] = defaults[feature]
        else:
            input_data[feature] = val
    df = pd.DataFrame([input_data])
    prediction = model.predict(df)[0]
    probabilities = model.predict_proba(df)[0]
    prob_dict = {c: p for c, p in zip(model.classes_, probabilities)}
    confidence = max(0.1, prob_dict[prediction] - len(missing_features) * 0.10)
    return {'Prediction': prediction, 'Confidence': confidence, 'All_Probabilities': prob_dict, 'Used_Features': input_data, 'Missing_Features': missing_features}
