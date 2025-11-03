#!/bin/bash
# Install only packages that Airflow doesn't have to avoid conflicts
# Use --no-deps and install dependencies separately to avoid overriding Airflow's packages
PIP_TARGET=/opt/airflow/custom_packages
mkdir -p $PIP_TARGET

# Install only our specific packages, let Airflow handle common dependencies
pip install --target $PIP_TARGET --no-deps --no-cache-dir chromadb || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir openai || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir langchain-text-splitters || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir pypdf || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir python-docx || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir pytesseract || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir python-magic || true
pip install --target $PIP_TARGET --no-deps --no-cache-dir pymongo || true

# Now install only the missing dependencies that our packages need
# Use --ignore-installed to install only if not already in Airflow's env
pip install --target $PIP_TARGET --no-cache-dir --ignore-installed \
    numpy \
    pydantic \
    httpx \
    anyio \
    h11 \
    httpcore \
    idna \
    sniffio \
    certifi \
    charset-normalizer \
    urllib3 \
    || true

