import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def train_severity_model():
    # Load dataset
    data_path = r'd:\PRGraduation\Down_AI\datasets\patient_data.csv'
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # Select features (Exclude Patient_ID)
    features = ['Age', 'Hemoglobin', 'RBC_Count', 'WBC_Count', 'MCV', 
                'TSH', 'T4', 'Echo_Abnormality_Score', 'Hearing_Loss_dB']
    
    X = df[features]
    y = df['Severity']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Initialize and train the Random Forest Classifier
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    os.makedirs(r'd:\PRGraduation\Down_AI\models', exist_ok=True)
    model_path = r'd:\PRGraduation\Down_AI\models\ds_severity_model.pkl'
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"\nModel saved successfully to {model_path}")

if __name__ == "__main__":
    train_severity_model()
