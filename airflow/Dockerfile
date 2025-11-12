# Use the official Airflow image as our base, specifying Python 3.11
FROM apache/airflow:2.9.2-python3.11

# Switch to the root user to install system-level dependencies
USER root

# Install Tesseract for OCR, build tools, and other libraries needed by our Python packages.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libmagic1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to the non-root airflow user
USER airflow

# Install our project dependencies, BUT DO NOT RE-INSTALL SQLAlchemy.
# We will use the version that comes with the base image, which is guaranteed to be compatible.
RUN pip install --no-cache-dir \
    "pika>=1.3.2" \
    "psycopg2-binary>=2.9.9" \
    "pymongo>=4.7.3" \
    "chromadb==0.5.0" \
    "numpy<2.0" \
    "openai>=1.35.3" \
    "langchain-text-splitters>=0.2.0" \
    "pypdf>=4.2.0" \
    "pytesseract>=0.3.10" \
    "Pillow>=10.3.0" \
    "python-magic>=0.4.27" \
    "python-docx>=1.1.2" \
    "pydantic-settings>=2.3.4" \
    "python-dotenv>=1.0.1" \
    "tenacity>=8.4.1"
