FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by pytesseract + opencv
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
        libglib2.0-0 \
            libsm6 \
                libxrender1 \
                    libxext6 \
                        libgl1-mesa-glx \
                            && rm -rf /var/lib/apt/lists/*

                            # Copy requirements first for better Docker layer caching
                            COPY requirements.txt .
                            RUN pip install --no-cache-dir -r requirements.txt

                            # Copy the entire project
                            COPY . .

                            # Railway dynamically assigns PORT - use it
                            EXPOSE 8000

                            # Run the FastAPI app from the api/ folder
                            CMD ["sh", "-c", "cd api && uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
                            
