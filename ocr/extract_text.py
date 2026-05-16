import io
import PyPDF2
from PIL import Image
import pytesseract
from docx import Document


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
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)

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