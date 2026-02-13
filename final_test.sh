#!/bin/bash

# ==============================================================================
# IngestIQ - Definitive End-to-End Test Script
#
# This script performs a full, realistic test of the IngestIQ pipeline,
# from data creation to the final RAG query.
# ==============================================================================

set -euo pipefail

# --- Configuration & Colors ---
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RESET='\033[0m'
log() { printf "\n${COLOR_BLUE}====== %s ======${COLOR_RESET}\n" "${1:-}"; }

# --- MAIN TEST LOGIC ---

# 1. RESET THE ENVIRONMENT
log "STEP 1: PERFORMING A FULL ENVIRONMENT RESET"
# The 'reset' command will clean data/logs, rebuild images, and start services.
./run.sh reset
echo "Waiting 60 seconds for all services to initialize..."
sleep 60

# 2. CREATE REALISTIC TEST DATA FOR "Quantum Dynamics Inc."
log "STEP 2: GENERATING REALISTIC TEST FILES FOR CLIENT 'quantum_dynamics'"
CLIENT_ID="quantum_dynamics"
DATA_DIR="local_data/$CLIENT_ID"
mkdir -p "$DATA_DIR"

# --- Document 1: HR Policy Manual (Text File) ---
HR_FILE="$DATA_DIR/QD_HR_Manual_2025.txt"
log "Creating HR Manual: $HR_FILE"
cat <<EOF > "$HR_FILE"
Quantum Dynamics Inc. - Global Human Resources Policy Guide
Effective Date: 2025-01-01

SECTION 1: CODE OF CONDUCT
All employees are expected to uphold the highest standards of integrity, professionalism, and respect in all interactions. Harassment or discrimination of any kind is not tolerated.

$(for i in {1..50}; do echo "1.$i: All communications, whether internal or external, must be professional and courteous. Confidential information must not be shared outside the company without explicit authorization."; done)

SECTION 2: WORK HOURS AND ATTENDANCE
The standard work week is 40 hours. Core business hours are from 10:00 AM to 4:00 PM in the employee's local time zone. Flexible start and end times are encouraged.

$(for i in {1..50}; do echo "2.$i: Employees are expected to be available and responsive during core hours. Any planned absences must be recorded in the HR portal at least 24 hours in advance, where possible."; done)

SECTION 3: PAID TIME OFF (PTO)
Full-time employees accrue 25 days of PTO annually. A maximum of 5 days of unused PTO may be carried over to the subsequent calendar year.

$(for i in {1..50}; do echo "3.$i: PTO requests must be submitted through the HR portal and approved by the employee's direct manager. Requests for periods longer than 5 consecutive days should be made at least one month in advance."; done)

SECTION 4: REMOTE WORK
Quantum Dynamics is a remote-first company. Employees may work from any location where they have a secure and reliable internet connection, provided it is within an approved country of operation.

$(for i in {1..50}; do echo "4.$i: Employees are responsible for maintaining a safe and productive home office environment. The company provides a one-time stipend of \$1000 for home office setup."; done)

SECTION 5: SECURITY
All employees must complete mandatory annual security training. Company-issued devices must be encrypted and protected with a strong, unique password.

$(for i in {1..50}; do echo "5.$i: Any suspected security incidents must be reported immediately to the IT Security team via the dedicated security hotline or email address."; done)
--- END OF DOCUMENT ---
EOF

# --- Document 2: Quarterly Financial Report (DOCX File) ---
FINANCE_FILE="$DATA_DIR/QD_Q3_2025_Financials.docx"
log "Creating Financial Report: $FINANCE_FILE"
# This reuses your existing script to generate a well-formatted DOCX
uv run scripts/create_docx.py "$FINANCE_FILE"

# --- Document 3: Technical Whitepaper (Text File) ---
TECH_FILE="$DATA_DIR/QEC_Whitepaper.txt"
log "Creating Technical Whitepaper: $TECH_FILE"
cat <<EOF > "$TECH_FILE"
Quantum Entanglement Communication (QEC): A Paradigm Shift in Secure Data Transfer
Authors: Dr. Evelyn Reed, Dr. Kenji Tanaka

ABSTRACT
This paper introduces Quantum Dynamics' proprietary framework for Quantum Entanglement Communication (QEC), a technology that enables instantaneous, unhackable data transfer across any distance.

$(for i in {1..50}; do echo "Abstract.$i: Our methodology leverages stabilized micro-wormholes to maintain quantum coherence over extended periods, overcoming the decoherence problem that has plagued previous attempts in the field."; done)

1. INTRODUCTION
The limitations of classical data transmission methods are well-documented. Latency and security are constant concerns. QEC promises to eliminate both.

$(for i in {1..50}; do echo "1.$i: By encoding data onto a pair of entangled particles, any measurement (observation) of one particle instantly affects the other, regardless of separation. This provides a foundation for a truly tamper-proof communication channel."; done)

2. METHODOLOGY: THE 'CHIMERA' STABILIZATION FIELD
Our core innovation is the Chimera Stabilization Field, which generates a localized temporal distortion to protect the entangled pair from environmental interference.

$(for i in {1..50}; do echo "2.$i: The field is generated by a series of hyper-dimensional resonators tuned to the quantum frequency of the particle pair. This process requires significant computational power but ensures 99.999% coherence for up to 72 hours."; done)

3. RESULTS
Initial tests have shown successful data transmission between our labs in Geneva and Tokyo with zero latency and zero data loss. The transmitted data included a 4K video stream and a 1TB genomic dataset.

$(for i in {1..50}; do echo "3.$i: The quantum channel remained stable throughout the test period. Attempts to intercept the data stream resulted in immediate decoherence of the targeted particle, alerting both sender and receiver to the intrusion attempt without exposing any data."; done)

4. CONCLUSION
QEC represents the future of secure communications. Further research will focus on miniaturizing the Chimera Field generator for commercial and consumer applications.

$(for i in {1..50}; do echo "4.$i: Quantum Dynamics is actively seeking strategic partners to accelerate the development and deployment of this revolutionary technology."; done)
--- END OF DOCUMENT ---
EOF

# --- Document 4: Project Meeting Minutes (Text File) ---
MEETING_FILE="$DATA_DIR/Project_FusionDrive_Minutes_2025-11-10.txt"
log "Creating Meeting Minutes: $MEETING_FILE"
cat <<EOF > "$MEETING_FILE"
Meeting Minutes: Project FusionDrive Steering Committee
Date: 2025-11-10

Attendees: Dr. Reed (Lead), Mr. Chen (Engineering), Ms. Davis (Marketing), Dr. Tanaka (R&D)

Agenda Item 1: Review of Q3 Milestones
- Mr. Chen reported that the engineering team has successfully completed the prototype of the mark II energy core. Efficiency is up 15% from the mark I.

$(for i in {1..125}; do echo "Discussion Point 1.$i: The team debated the merits of using a dilithium crystal matrix versus a standard plasma conduit. Dr. Reed insisted that while more expensive, the crystal matrix provides superior stability and is essential for meeting our long-term performance targets."; done)

Agenda Item 2: Q4 Roadmap and Budget Allocation
- Ms. Davis presented the marketing plan for the FusionDrive launch, requesting an additional \$2M budget for a global digital campaign.

$(for i in {1..125}; do echo "Discussion Point 2.$i: The committee reviewed the budget request. Mr. Chen noted that a portion of his engineering budget could be re-allocated if the decision is made to proceed with the more cost-effective plasma conduit, but this carries performance risks. It was decided to approve the marketing budget on a provisional basis."; done)

Action Items:
- AI-1: Dr. Tanaka to provide final analysis on crystal matrix vs. plasma conduit by 2025-11-17. (Owner: K. Tanaka)
- AI-2: Mr. Chen to prepare revised engineering cost projections for both options. (Owner: B. Chen)
--- END OF DOCUMENT ---
EOF

# --- Document 5: Corrupt PDF to Test Failure Handling ---
CORRUPT_FILE="$DATA_DIR/corrupt_security_audit.pdf"
log "Creating Corrupt PDF: $CORRUPT_FILE"
echo "This is not a valid PDF file and is designed to fail." > "$CORRUPT_FILE"

# 3. AUTHENTICATE (SOC 2 Requirement)
log "STEP 3: AUTHENTICATING VIA OAUTH2"
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/v1/auth/token" \
  -F "username=admin@ingestiq.com" \
  -F "password=admin123")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r .access_token)
if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    echo -e "${COLOR_RED}Authentication Failed. Aborting.${COLOR_RESET}"
    exit 1
fi
echo "Authenticated successfully. Token acquired."

# 4. INGEST WITH TOKEN
log "STEP 4: SENDING INGESTION REQUEST TO THE API"
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/v1/ingest" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d "{
  \"client_id\": \"$CLIENT_ID\",
  \"files\": [
    { \"path\": \"$HR_FILE\", \"metadata\": {\"doc_type\": \"HR Policy\"} },
    { \"path\": \"$FINANCE_FILE\", \"metadata\": {\"doc_type\": \"Financial Report\"} },
    { \"path\": \"$TECH_FILE\", \"metadata\": {\"doc_type\": \"Whitepaper\"} },
    { \"path\": \"$MEETING_FILE\", \"metadata\": {\"doc_type\": \"Meeting Minutes\"} },
    { \"path\": \"$CORRUPT_FILE\", \"metadata\": {\"doc_type\": \"Audit\"} }
  ]
}")

JOB_ID=$(echo "$RESPONSE" | jq -r .job_id)
if [ -z "$JOB_ID" ] || [ "$JOB_ID" == "null" ]; then
    echo "${COLOR_RED}Failed to create ingestion job. Aborting.${COLOR_RESET}"
    exit 1
fi
echo "Ingestion job created successfully with ID: $JOB_ID"

# 4. TRIGGER THE AIRFLOW DAG
log "STEP 4: TRIGGERING THE AIRFLOW DAG VIA COMMAND LINE"
# Ensure DAG is unpaused (fallback)
docker compose exec -T airflow-webserver airflow dags unpause ingestion_pipeline || true
docker compose exec -T airflow-webserver airflow dags trigger ingestion_pipeline --conf "{\"job_id\": \"$JOB_ID\"}"
echo "DAG triggered. Waiting 90 seconds for the pipeline to complete..."
sleep 90

# 5. VERIFY THE OUTCOME
log "STEP 5: VERIFYING THE FINAL JOB STATUS VIA API"
curl -s -X GET "http://localhost:8001/api/v1/jobs/$JOB_ID" \
-H "Authorization: Bearer $ACCESS_TOKEN" | jq

log "STEP 6: VERIFYING THAT VECTORS WERE STORED IN CHROMA"
uv run scripts/verify_chroma.py "$CLIENT_ID"

# 6. PERFORM REALISTIC RAG QUERIES
log "STEP 7: PERFORMING REALISTIC RAG QUERIES"
echo -e "${COLOR_YELLOW}\nQuery 1: How many days of unused PTO can be carried over to the next year?${COLOR_RESET}"
curl -N -s -X POST "http://localhost:8001/api/v1/query" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d "{
  \"client_id\": \"$CLIENT_ID\",
  \"query\": \"How many days of unused PTO can be carried over to the next year?\"
}"

echo -e "\n\n${COLOR_YELLOW}Query 2: What does QEC stand for?${COLOR_RESET}"
curl -N -s -X POST "http://localhost:8001/api/v1/query" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d "{
  \"client_id\": \"$CLIENT_ID\",
  \"query\": \"What does QEC stand for?\"
}"

echo -e "\n\n${COLOR_YELLOW}Query 3: What was the decision regarding the marketing budget for FusionDrive?${COLOR_RESET}"
curl -N -s -X POST "http://localhost:8001/api/v1/query" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d "{
  \"client_id\": \"$CLIENT_ID\",
  \"query\": \"What was the decision regarding the marketing budget for FusionDrive?\"
}"
echo

log "--- DEFINITIVE TEST COMPLETE ---"
