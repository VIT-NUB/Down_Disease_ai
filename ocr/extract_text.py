import cv2
import pytesseract
import os
import PyPDF2
import docx

import platform
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
        
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # remove noise
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # threshold
    _, thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    text = pytesseract.image_to_string(gray)
    return text

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    
    if ext in image_extensions:
        return extract_text_from_image(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

if __name__ == "__main__":
    image_path = r"datasets/reports_images/test.png"
    try:
        text = extract_text_from_image(image_path)
        print("\n===== EXTRACTED TEXT =====\n")
        print(text)
    except Exception as e:
        print(f"Error: {e}")