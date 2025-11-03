# IngestIQ

A multi-tenant, event-driven RAG (Retrieval-Augmented Generation) ingestion and querying pipeline.

## Overview

IngestIQ is a production-ready system designed for ingesting, processing, and querying documents using RAG technology. It supports multiple file formats, idempotent processing, and provides a robust API for both ingestion and querying.

## Architecture

The system is built with:

- **FastAPI**: REST API for ingestion and querying
- **Apache Airflow**: Workflow orchestration
- **PostgreSQL**: Metadata and job state storage
- **MongoDB**: Raw text caching
- **RabbitMQ**: Event-driven messaging
- **ChromaDB**: Vector storage for embeddings
- **OpenAI**: LLM and embeddings generation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (if running locally)
- uv package manager (recommended)

### Setup

1. Clone the repository

2. Create a `.env` file in the root directory with your configuration (see `.env.example` for reference)

3. Build and start all services:

```bash
docker-compose up -d --build
```

### Services

Once running, the following services will be available:

- **API**: http://localhost:8000 (docs at http://localhost:8000/docs)
- **Airflow UI**: http://localhost:8080 (username: `admin`, password: `admin`)
- **RabbitMQ Management**: http://localhost:15672 (credentials from `.env`)
- **PostgreSQL**: localhost:5432
- **MongoDB**: localhost:27017

### Health Checks

- API Health: `GET http://localhost:8000/health`

## Project Structure

```
IngestIQ/
├── airflow/           # Airflow DAGs, plugins, and logs
├── app/               # FastAPI application code
│   ├── api/          # API endpoints
│   ├── core/         # Core configuration and utilities
│   └── ingestion/    # Ingestion logic
├── local_data/       # Local database volumes
└── docker-compose.yml # Multi-container orchestration
```

## Development

This project uses `uv` for package management. See `pyproject.toml` for dependencies.

## License

[Your License Here]

