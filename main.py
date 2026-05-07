import os
import sys

# Import our custom modules
from ocr.extract_text import extract_text_from_file
from ocr.parse_text import parse_cbc_report
from models.predict import predict_severity

def main():
    print("="*50)
    print(" Down Syndrome Patient Severity Analysis System")
    print("="*50)
    
    # Let the user choose their own image from the dataset
    print("\nAvailable images are in: datasets/reports_images/")
    image_name = input("Enter the exact name of the file you want to test (e.g. test.png or report.pdf): ")
    if not image_name.strip():
        image_name = "test.png" # Default fallback
        
    image_path = os.path.join("datasets", "reports_images", image_name.strip())
    
    print("\n[1] Starting Extraction...")
    if not os.path.exists(image_path):
        print(f"Error: Could not find image at {image_path}")
        return
        
    raw_text = extract_text_from_file(image_path)
    print(f"Successfully extracted text from file.")
    
    print("\n[2] Parsing Medical Data (NLP/Regex)...")
    parsed_data = parse_cbc_report(raw_text)
    
    print("Found the following lab results from the image:")
    for key, value in parsed_data.items():
        print(f"  - {key}: {value}")
        
    print("\n[3] Running AI Prediction Model...")
    # Pass only what OCR found, the model will track what's missing
    prediction_result = predict_severity(parsed_data)
    
    severity = prediction_result['Prediction']
    confidence = prediction_result['Confidence'] * 100
    missing = prediction_result['Missing_Features']
    
    critical_missing = [f for f in ['TSH', 'Echo_Abnormality_Score', 'Hearing_Loss_dB'] if f in missing]
    
    print("="*50)
    print(" "*15 + "FINAL DIAGNOSIS")
    print("="*50)
    
    if critical_missing:
        print("Status                 : INCOMPLETE ASSESSMENT")
        print(f"Model Confidence       : {confidence:.1f}%")
        print(f"Missing Data           : {', '.join(critical_missing)}")
        print("\nRecommendation:")
        print(f">> Please provide {', '.join(critical_missing)} for a confident and complete diagnosis.")
    else:
        print(f"Patient Severity Level : {severity.upper()}")
        print(f"Model Confidence       : {confidence:.1f}%")
        print("\nRecommendation:")
        if severity == 'High':
            print(">> URGENT: High risk detected. Immediate medical intervention and follow-up required.")
        elif severity == 'Medium':
            print(">> WARNING: Moderate risk. Close monitoring of Thyroid/Heart/Blood recommended.")
        else:
            print(">> NORMAL: Stable condition. Proceed with regular check-ups.")
    print("="*50)

if __name__ == "__main__":
    main()
