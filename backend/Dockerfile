FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Base tools + Microsoft ODBC 18 + Tesseract OCR (eng language only, keeps image small)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl gnupg2 apt-transport-https ca-certificates unixodbc \
      tesseract-ocr tesseract-ocr-eng \
      libgl1 libglib2.0-0 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
         > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

EXPOSE 8000

# Default command: API server. Override to run the extractor or dry-run.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
