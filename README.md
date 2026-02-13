# IngestIQ: Enterprise-Grade, SOC 2 Compliant RAG Platform

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Security](https://img.shields.io/badge/Security-SOC2%20Type%20II%20Aligned-blue)
![Platform](https://img.shields.io/badge/Platform-Multi--Tenant-orange)

IngestIQ is a robust, high-assurance Retrieval-Augmented Generation (RAG) platform designed for organizations that require strict data security, tenant isolation, and auditability. It transforms raw documents (PDF, DOCX, TXT, Images) into searchable, context-aware intelligence while adhering to enterprise compliance standards.

---

## 🏢 Executive Summary

In a landscape where data privacy is paramount, IngestIQ provides more than just "chat with your docs." It provides a **security-first framework** where identity is cryptographically bound to data, every action is logged for forensics, and processing is handled by an event-driven, production-grade orchestration engine.

### Core Value Propositions:
*   **Absolute Multi-Tenancy**: Data isolation is enforced at the API, Database, and Vector levels. User "A" cannot, by design, see or query data from Client "B".
*   **SOC 2 Compliance by Design**: Built from the ground up to support Trust Services Criteria (TSC) for Security, Confidentiality, and Processing Integrity.
*   **Enterprise Reliability**: Uses Apache Airflow for robust workflow management, Celery/LocalExecutor for task handling, and RabbitMQ for messaging.

---

## �️ SOC 2 Compliance Matrix

This platform implements the following technical controls to satisfy audit requirements:

| Control Area | SOC 2 TSC | Implementation Detail |
| :--- | :--- | :--- |
| **Identity & Access** | CC6.1 | Mandatory **OAuth2 Password Flow** with JWT. No anonymous endpoints. |
| **Confidentiality** | C1.1 | **Tenant Isolation Logic**: `client_id` is extracted from the authenticated JWT and used as a hard filter for all DB and Vector queries. |
| **Audit Trails** | CC7.2 | Every sensitive operation (Ingestion request, DAG trigger, RAG Query) is recorded in an immutable `audit_logs` table with timestamp and user ID. |
| **Secrets Management** | CC6.6 | All credentials (DB, OpenAI, RabbitMQ) are managed via environment variables. Zero hardcoded secrets in the codebase. |
| **Data Resilience** | CC8.1 | Airflow handles retries and error state management, ensuring that ingestion failures are documented and recoverable. |

---

## 🏗️ System Architecture

### Local Development Stack:
*   **FastAPI**: The high-performance "Gatekeeper" API.
*   **Apache Airflow (2.9.2)**: Orchestrates the ingestion pipeline.
*   **ChromaDB**: High-speed vector database for semantic search.
*   **PostgreSQL**: Secure storage for user metadata, job statuses, and audit logs.
*   **RabbitMQ**: Message broker ensuring reliable communication between the API and the pipeline.
*   **OpenAI**: Powering embeddings (`text-embedding-3-large`) and generative responses.

### Data Flow Lifecycle:
1.  **Authentication**: User logs in and receives a JWT containing their `client_id`.
2.  **Ingestion Request**: User uploads files via standard API.
3.  **Queueing**: A job message is published to RabbitMQ.
4.  **Orchestration**: Airflow picks up the message, creates a DAG run, and manages the lifecycle.
5.  **Processing**: The worker cleans text, performs OCR (if needed), chunks data, and generates embeddings.
6.  **Vector Storage**: Chunks are stored in ChromaDB, tagged with the `client_id`.
7.  **Secure Query**: Users query the RAG endpoint. The API enforces a `where` filter on the `client_id` within ChromaDB, ensuring no cross-tenant leakage.

---

## 🚀 Getting Started

### Prerequisites
*   **Docker Desktop**: (Mac/Linux/Windows)
*   **Python 3.11+**: If you wish to run scripts locally.
*   **OpenAI API Key**: Required for RAG functionality.

### 1. Configure the Environment
Copy the example configuration and add your internal secrets:
```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY and other credentials
```

### 2. Launch the Platform
We provide a comprehensive utility script (`run.sh`) to manage the stack:
```bash
chmod +x run.sh final_test.sh
./run.sh up
```
*This command builds the images, starts the containers, and initializes the security layer (creating the initial admin user).*

### 3. Verify the Deployment
Run the definitive end-to-end test to validate that all compliance controls and processing steps are functional:
```bash
./final_test.sh
```
*The test script will generate documents, authenticate, ingest them, and verify the RAG response.*

---

## 📡 API Reference

### **Authentication**
`POST /api/v1/auth/token`
*   **Input**: `username` (email), `password`
*   **Output**: JWT `access_token`

### **Document Ingestion**
`POST /api/v1/ingest`
*   **Header**: `Authorization: Bearer <token>`
*   **Payload**: List of file paths and metadata.
*   **Action**: Validates user tenant and triggers Airflow pipeline.

### **RAG Querying**
`POST /api/v1/query`
*   **Header**: `Authorization: Bearer <token>`
*   **Payload**: `{ "query": "What is our PTO policy?", "client_id": "optional" }`
*   **Action**: Performs semantic search restricted to user's tenant and generates AI response.

---

## 📂 Project Structure

```bash
IngestIQ/
├── airflow/           # Airflow-specific Dockerfile, DAGs, and logs
│   ├── dags/          # The core Ingestion Pipeline DAG
│   └── Dockerfile     # Unified Airflow image with app dependencies
├── app/               # Main FastAPI Application
│   ├── api/          # Identity, Auth, Ingest, and Query endpoints
│   ├── core/         # Security logic, Database models, and Config
│   └── ingestion/    # Document parsers and processing logic
├── scripts/           # Administrative utilities (Admin creation, verification)
├── docker-compose.yml # Enterprise orchestration config
├── run.sh            # Main control script for the environment
└── final_test.sh     # Compliance & Integration verification script
```

---

## 🛠️ Developer Operations

### Resetting the Environment
If you need to purge all data (DBs, Vectors, Logs) and start fresh:
```bash
./run.sh reset
```

### Viewing Logs
For real-time pipeline monitoring:
```bash
./run.sh logs
```

### Accessing Dashboards
*   **API Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)
*   **Airflow UI**: [http://localhost:8080](http://localhost:8080) (Default: `admin` / `admin`)
*   **RabbitMQ Console**: [http://localhost:15672](http://localhost:15672)

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Disclaimer**: This platform is designed to facilitate SOC 2 compliance but does not guarantee it. Compliance requires comprehensive organizational policies and independent auditing.
