import pandas as pd
import numpy as np
import pickle
import os

def predict_severity(patient_data):
        """
            Predicts the severity of Down Syndrome for a given patient.

                patient_data: dictionary containing patient features:
                    'Age', 'Hemoglobin', 'RBC_Count', 'WBC_Count', 'MCV',
                        'TSH', 'T4', 'Echo_Abnormality_Score', 'Hearing_Loss_dB'
                            """
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ds_severity_model.pkl')

    if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found at {model_path}. Please train the model first.")

    with open(model_path, 'rb') as f:
                model = pickle.load(f)

    # Ensure the input dictionary is converted into a DataFrame with the right order
    features = ['Age', 'Hemoglobin', 'RBC_Count', 'WBC_Count', 'MCV', 'TSH', 'T4', 'Echo_Abnormality_Score', 'Hearing_Loss_dB']

    # Fill missing values with healthy defaults if not provided
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

    # Sanity limits for auto-correction (e.g. OCR read 110 instead of 11.0)
    def correct_value(feature, val):
                if val is None:
                                return None
                            try:
                                            val = float(val)
except ValueError:
            return None

        if feature == 'Hemoglobin' and val > 30:
                        return val / 10.0  # 110 -> 11.0
        if feature == 'WBC_Count' and val < 100:
                        return val * 1000 # 7 -> 7000
        return val

    # Construct final input data
    input_data = {}
    missing_features = []

    for feature in features:
                # Standardize keys (e.g. from OCR 'Hemoglobin (Hb)' -> 'Hemoglobin')
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

    # Predict
    prediction = model.predict(df)[0]
    probabilities = model.predict_proba(df)[0]
    classes = model.classes_

    # Find confidence
    prob_dict = {cls: prob for cls, prob in zip(classes, probabilities)}
    confidence = prob_dict[prediction]

    # Penalize confidence realistically based on missing data
    # 10% penalty for each missing feature
    penalty = len(missing_features) * 0.10
    confidence = max(0.1, confidence - penalty)

    return {
                'Prediction': prediction,
                'Confidence': confidence,
                'All_Probabilities': prob_dict,
                'Used_Features': input_data,
                'Missing_Features': missing_features
    }

if __name__ == "__main__":
        # Test prediction
        sample_patient = {
                    'Age': 5,
                    'Hemoglobin': 9.5, # Low
                    'RBC_Count': 3.9,
                    'WBC_Count': 13000, # High
                    'Echo_Abnormality_Score': 2, # Moderate heart issue
                    'TSH': 6.0 # High TSH
        }

    print("Testing Prediction on Patient with Multiple Risks...")
    result = predict_severity(sample_patient)
    print(f"Severity Prediction: {result['Prediction']}")
    print(f"Confidence: {result['Confidence']:.2f}")

    print(\"\nTesting Prediction on Healthy Patient...\")
              healthy_patient = {
                      'Hemoglobin': 13.0,
                              'WBC_Count': 6000,
                                      'Echo_Abnormality_Score': 0,
                                              'TSH': 1.5
                                                  }
                                                      res_healthy = predict_severity(healthy_patient)
                                                          print(f"Severity Prediction: {res_healthy['Prediction']}")
                                                              print(f"Confidence: {res_healthy['Confidence']:.2f}")
                                                              
