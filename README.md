# IngestIQ: Secure Enterprise RAG Pipeline

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Security](https://img.shields.io/badge/Security-SOC2%20Aligned-blue)

## 🏢 Executive Summary

IngestIQ is a high-assurance, multi-tenant Retrieval-Augmented Generation (RAG) platform. It is engineered to adhere to strict **SOC 2 Type II** controls regarding security, confidentiality, and processing integrity.

## 🔐 Compliance Architecture (AICPA Trust Services Criteria)

| Control | Implementation |
| :--- | :--- |
| **Confidentiality (C1.1)** | Strict tenant isolation. Users are cryptographically bound to a specific `client_id` via JWT. |
| **Logical Access (CC6.1)** | Role-Based Access Control (RBAC). No anonymous access allowed. |
| **Secrets Management (CC6.6)** | Zero hardcoded secrets. Configuration injected via environment variables. |
| **Audit Trails (CC7.2)** | Immutable `audit_logs` table records every ingestion and query event with user attribution. |

## 🚀 Secure Setup

1. **Configure Secrets:**

   ```bash
   cp .env.example .env
   # Edit .env to set secure passwords
   ```

2. **Launch & Initialize:**

   ```bash
   ./run.sh up
   ```

   *This will start the stack and auto-generate an initial admin user (`admin@ingestiq.com`).*

3. **Validate Security:**

   ```bash
   ./final_test.sh
   ```

   *Runs a full integration test including OAuth2 authentication flow.*

## 📡 API Reference

**Base URL:** `http://localhost:8001/api/v1`

* **Auth:** `POST /auth/token` (Get Bearer Token)
* **Ingest:** `POST /ingest` (Requires `Authorization: Bearer <token>`)
* **Query:** `POST /query` (Requires `Authorization: Bearer <token>`)

## 📜 License

Internal Restricted

