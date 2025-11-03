# Stage 1: The Builder
# Use a full Python image to ensure build tools are available
FROM python:3.11-bookworm AS builder

# Install uv, our package manager
RUN pip install uv

# Set up a virtual environment in the final destination path
RUN python3 -m venv /opt/venv

# Copy dependency files
WORKDIR /app
COPY pyproject.toml ./

# Install dependencies into the virtual environment using uv
# This ensures all packages, including native extensions, are compiled here.
RUN uv pip install --system --no-cache -r pyproject.toml --python /opt/venv/bin/python

# Stage 2: The Final Production Image
# Use a slim image for a smaller footprint
FROM python:3.11-slim-bookworm

# Create a non-root user for security
RUN groupadd --system appgroup && useradd --system --gid appgroup --shell /bin/bash appuser

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application source code
WORKDIR /app
COPY ./app ./app

# Set ownership for the non-root user
RUN chown -R appuser:appgroup /app

# Activate the virtual environment by adding it to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Switch to the non-root user
USER appuser

# Default command to run the application (can be overridden in docker-compose)
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]

