import re

def parse_cbc_report(text):
    """
    Parses raw OCR text from a CBC report and extracts key medical values.
    Returns a dictionary of structured data.
    """
    structured_data = {}
    
    # Define regex patterns for different tests
    # Using case-insensitive search and allowing for variations in spacing
    patterns = {
        'Hemoglobin (Hb)': r'HEMOGLOBIN\s+([\d\.]+)\s*(?:gm%|g/dL)',
        'RBC Count': r'RBC COUNT\s+([\d\.]+)',
        'PCV (Packed Cell Volume)': r'PACKED CELL[^\d]*([\d\.]+)',
        'MCV': r'MCV[^\d]*([\d\.]+)\s*(?:fl|fL)',
        'MCH': r'MCH[^\d]*([\d\.]+)\s*(?:pg|pgm)',
        'MCHC': r'MCHC[^\d]*([\d\.L]+)\s*(?:g/dL|g/L)', # Handled L which might be OCR error for 1 or just range indicator
        'RDW-SD': r'R\.D\.W-SD[^\d]*([\d\.]+)',
        'RDW-CV': r'R\.D\.W-CV[^\d]*([\d\.]+)',
        'WBC Count': r'WBC\s*(\d+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean up the extracted value (e.g. if 'L' was misread in '31L.16')
            value = match.group(1).replace('L', '1') # Simple heuristic for common OCR error
            try:
                # Try to convert to float if it has a decimal, else int
                if '.' in value:
                    val = float(value)
                else:
                    val = int(value)
                
                # Heuristics for missing decimal points (common OCR errors)
                if key == 'Hemoglobin (Hb)' and val > 50:
                    val = val / 10.0
                elif key == 'MCHC' and val > 100:
                    val = val / 10.0
                    
                structured_data[key] = val
            except ValueError:
                structured_data[key] = value
                
    return structured_data

if __name__ == "__main__":
    import json
    import os
    import sys
    
    # Add parent directory to path so we can import ocr module correctly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ocr.extract_text import extract_text_from_image
    
    image_path = r"datasets/reports_images/test.png"
    print(f"Extracting text from {image_path}...")
    try:
        extracted_text = extract_text_from_image(image_path)
        print("Parsing extracted text...")
        result = parse_cbc_report(extracted_text)
        print("\n===== PARSED DATA =====")
        print(json.dumps(result, indent=4))
    except Exception as e:
        print(f"Error during execution: {e}")
