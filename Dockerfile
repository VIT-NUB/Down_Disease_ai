FROM python:3.11-slim

# Install system dependencies including Tesseract OCR and image/PDF support
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set Tesseract path explicitly so pytesseract can find language data
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Start the FastAPI server.
# Railway provides PORT automatically. If PORT is missing, fallback to 8000.
CMD ["sh", "-c", "python -m uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]