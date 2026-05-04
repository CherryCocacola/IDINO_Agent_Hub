FROM python:3.12-slim

WORKDIR /app

# System dependencies for document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 의존성 설치 후 numpy 다운그레이드 (Xeon E5 서버 x86-64-v2 비호환 대응)
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install "numpy<2.0.0" --force-reinstall --no-deps

COPY . .

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
