FROM python:3.11-slim

# Install system dependencies including Tesseract OCR and its English language data
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

# Set Tesseract path explicitly so pytesseract can find it
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Railway sets PORT automatically, fallback to 8000
ENV PORT=8000

# Start the FastAPI server using shell evaluation for $PORT
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port $PORT"]
