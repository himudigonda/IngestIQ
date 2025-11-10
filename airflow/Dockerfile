# Use the official Airflow image as our base
FROM apache/airflow:2.9.2

# Switch to the root user to install system-level dependencies
USER root

# Install Tesseract for OCR, which is needed by the worker for image parsing.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the project's dependency definition file
COPY pyproject.toml ./pyproject.toml

# THIS IS THE CORRECTED FIX: Assign ownership to the 'airflow' user and 'root' group.
RUN chown airflow:root /opt/airflow/pyproject.toml

# Switch back to the non-root airflow user for security
USER airflow

# Install 'uv', our fast package manager
RUN pip install uv

# Switch to root to install packages, then back to airflow
USER root
# Use uv to install all dependencies from pyproject.toml into the main Python environment.
# This will now work because pyproject.toml explicitly defines the package location.
RUN uv pip install --system --no-cache .
USER airflow
