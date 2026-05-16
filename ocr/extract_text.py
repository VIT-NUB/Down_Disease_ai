import io
import PyPDF2
from PIL import Image, ImageFilter, ImageOps
import os
import platform
import pytesseract
from docx import Document
if platform.system() == "Windows":
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Improve scanned medical report images before OCR.
    """
    # Convert to RGB first
    image = image.convert("RGB")

    # Convert to grayscale
    image = ImageOps.grayscale(image)

    # Resize image to improve OCR accuracy
    width, height = image.size
    scale_factor = 2
    image = image.resize((width * scale_factor, height * scale_factor))

    # Increase contrast automatically
    image = ImageOps.autocontrast(image)

    # Denoise slightly
    image = image.filter(ImageFilter.MedianFilter(size=3))

    # Sharpen text
    image = image.filter(ImageFilter.SHARPEN)

    # Convert to black/white threshold
    image = image.point(lambda x: 0 if x < 160 else 255, "1")

    return image


def extract_text_from_image_bytes(file_bytes: bytes) -> str:
    """
    Extract text from image bytes using preprocessing + Tesseract OCR.
    """
    image = Image.open(io.BytesIO(file_bytes))

    processed_image = preprocess_image_for_ocr(image)

    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 4",
        "--oem 3 --psm 11"
    ]

    best_text = ""

    for config in configs:
        try:
            text = pytesseract.image_to_string(processed_image, config=config)
            if len(text.strip()) > len(best_text.strip()):
                best_text = text
        except Exception as e:
            print(f"OCR config failed ({config}): {str(e)}")

    return best_text.strip()


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from uploaded medical files.

    Supported:
    - PDF
    - Images: PNG, JPG, JPEG, TIFF, BMP
    - TXT
    - DOCX
    """
    filename_lower = filename.lower()
    text = ""

    try:
        if filename_lower.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            text = extract_text_from_image_bytes(file_bytes)

        elif filename_lower.endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="ignore")

        elif filename_lower.endswith(".docx"):
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([p.text for p in doc.paragraphs])

        else:
            raise ValueError(f"Unsupported file extension: {filename}")

    except Exception as e:
        print(f"Error extracting text from {filename}: {str(e)}")

    return text.strip()


def extract_text_from_image(file_path: str) -> str:
    """
    Backward compatibility for old local tests.
    """
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        return extract_text_from_file(file_bytes, file_path)

    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return ""