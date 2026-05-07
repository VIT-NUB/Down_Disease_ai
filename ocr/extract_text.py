import cv2
import pytesseract
import os
import PyPDF2
import docx

if os.name == 'nt':
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

    text = pytesseract.image_to_string(thresh)
    return text

def extract_text_from_pdf(pdf_path):
        text = ""
        with open(pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                                    text += page.extract_text()
                            return text

def extract_text_from_docx(docx_path):
        doc = docx.Document(docx_path)
        text = ""
        for para in doc.paragraphs:
                    text += para.text + "\n"
                return text

def extract_text(file_path):
        ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                return extract_text_from_image(file_path)
elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
elif ext == '.docx':
        return extract_text_from_docx(file_path)
else:
        raise ValueError(f"Unsupported file format: {ext}")
