import pandas as pd
import numpy as np
import os

def generate_synthetic_data(num_samples=1000):
    """
    Generates synthetic medical data for Down Syndrome patients
    to train the severity classification model.
    """
    np.random.seed(42)
    
    # Generate base patient data
    data = {
        'Patient_ID': range(1, num_samples + 1),
        'Age': np.random.randint(1, 60, num_samples),
        
        # CBC Data (similar to OCR output)
        'Hemoglobin': np.random.normal(12, 2, num_samples), # Normal 11-16
        'RBC_Count': np.random.normal(4.5, 0.5, num_samples),
        'WBC_Count': np.random.normal(7000, 2000, num_samples),
        'MCV': np.random.normal(85, 10, num_samples),
        
        # Thyroid Data
        'TSH': np.random.lognormal(mean=1.5, sigma=0.8, size=num_samples), # Higher risk of hypothyroidism
        'T4': np.random.normal(1.2, 0.3, num_samples),
        
        # Echo & Heart Data (Score 0: Normal, 1: Mild, 2: Moderate, 3: Severe)
        'Echo_Abnormality_Score': np.random.choice([0, 1, 2, 3], num_samples, p=[0.4, 0.3, 0.2, 0.1]),
        
        # Hearing Test Data (dB Loss)
        'Hearing_Loss_dB': np.random.normal(25, 15, num_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Ensure no negative values where inappropriate
    df['WBC_Count'] = df['WBC_Count'].abs()
    df['Hearing_Loss_dB'] = df['Hearing_Loss_dB'].abs()
    
    # Calculate Severity (Target Variable) based on medical thresholds
    severity = []
    for _, row in df.iterrows():
        risk_score = 0
        
        # Thyroid risk
        if row['TSH'] > 5.0 or row['TSH'] < 0.4:
            risk_score += 1
            
        # Heart risk (Very critical for DS)
        if row['Echo_Abnormality_Score'] == 2:
            risk_score += 2
        elif row['Echo_Abnormality_Score'] == 3:
            risk_score += 3
            
        # Hematology risk (Leukemia risk etc)
        if row['WBC_Count'] > 12000 or row['WBC_Count'] < 4000:
            risk_score += 1
        if row['Hemoglobin'] < 10:
            risk_score += 1
            
        # Hearing risk
        if row['Hearing_Loss_dB'] > 40:
            risk_score += 1
            
        # Determine Severity
        if risk_score >= 4:
            severity.append('High')
        elif risk_score >= 2:
            severity.append('Medium')
        else:
            severity.append('Low')
            
    df['Severity'] = severity
    
    # Create datasets directory if it doesn't exist
    os.makedirs(r'd:\PRGraduation\Down_AI\datasets', exist_ok=True)
    
    # Save to CSV
    output_path = r'd:\PRGraduation\Down_AI\datasets\patient_data.csv'
    df.to_csv(output_path, index=False)
    print(f"Synthetic dataset generated and saved to {output_path}")
    print(f"Severity Distribution:\n{df['Severity'].value_counts()}")

if __name__ == "__main__":
    generate_synthetic_data()
