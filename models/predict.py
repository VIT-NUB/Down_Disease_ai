import pandas as pd
import numpy as np
import pickle
import os


def predict_severity(patient_data):
    """
    Predicts the severity of Down Syndrome for a given patient.
    """
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ds_severity_model.pkl')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}.")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    features = ['Age', 'Hemoglobin', 'RBC_Count', 'WBC_Count', 'MCV',
                'TSH', 'T4', 'Echo_Abnormality_Score', 'Hearing_Loss_dB']

    defaults = {
        'Age': 10,
        'Hemoglobin': 12.0,
        'RBC_Count': 4.5,
        'WBC_Count': 7000,
        'MCV': 85.0,
        'TSH': 1.5,
        'T4': 1.2,
        'Echo_Abnormality_Score': 0,
        'Hearing_Loss_dB': 10
    }

    def correct_value(feature, val):
        if val is None:
            return None
        try:
            val = float(val)
        except ValueError:
            return None
        if feature == 'Hemoglobin' and val > 30:
            return val / 10.0
        if feature == 'WBC_Count' and val < 100:
            return val * 1000
        return val

    input_data = {}
    missing_features = []

    for feature in features:
        val = None
        for k, v in patient_data.items():
            if k.startswith(feature) or (feature == 'Hemoglobin' and 'Hb' in k):
                val = v
                break

        val = correct_value(feature, val)

        if val is None:
            missing_features.append(feature)
            input_data[feature] = defaults[feature]
        else:
            input_data[feature] = val

    df = pd.DataFrame([input_data])

    prediction = model.predict(df)[0]
    probabilities = model.predict_proba(df)[0]
    classes = model.classes_

    prob_dict = {cls: prob for cls, prob in zip(classes, probabilities)}
    confidence = prob_dict[prediction]

    penalty = len(missing_features) * 0.10
    confidence = max(0.1, confidence - penalty)

    return {
        'Prediction': prediction,
        'Confidence': confidence,
        'All_Probabilities': prob_dict,
        'Used_Features': input_data,
        'Missing_Features': missing_features
    }