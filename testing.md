
# IngestIQ: End-to-End Testing Guide

This guide provides a complete, step-by-step workflow for cleaning, running, and testing the entire IngestIQ pipeline. Following these steps will ensure a repeatable and verifiable test of all system components.

### Prerequisites

1.  **Docker Desktop** is installed and running.
2.  An **`.env` file** exists in the project root with your `OPENAI_API_KEY` and other credentials.
3.  All code changes from our debugging session have been saved.

---

### Step 1: Full System and Data Reset

This is the most critical step for a clean test. The `clean-data` command will stop all running containers, remove their volumes, and delete the `local_data` directory, ensuring no old data can interfere with the test.

In your terminal, run:
```bash
./run.sh clean-data
```
You will be asked for confirmation. Type `y` and press Enter.

### Step 2: Launch the Environment

This command will rebuild any necessary Docker images and start all services (API, Postgres, RabbitMQ, ChromaDB, Airflow) in the background.

```bash
./run.sh up
```
Give the services about a minute to initialize. You can check that all containers are running and healthy with `docker ps`.

### Step 3: Create Large and Varied Test Data

We will create a new set of test files for a client named `acme_corp`. This includes a large text file, a large multi-page DOCX file, and one intentionally corrupt file to test the system's fault tolerance.

**1. Create the Client Directory:**
```bash
mkdir -p local_data/acme_corp
```

**2. Create a Large Text File (`hr_manual.txt`):**
This command generates a 500-paragraph text file to test the chunking and embedding process.

```bash
echo "ACME Corp Official HR Manual (v4.2)" > local_data/acme_corp/hr_manual.txt
echo "======================================" >> local_data/acme_corp/hr_manual.txt
for i in {1..500}; do
  echo "Policy Section $i: All ACME Corp employees are expected to maintain the highest standards of professional conduct. The standard work day is from 9:00 AM to 5:00 PM with a required 60-minute unpaid lunch break. The company provides 20 days of paid time off (PTO) annually, accrued monthly. All hardware requests must be submitted via the IT portal." >> local_data/acme_corp/hr_manual.txt
done
echo "--- End of Manual ---" >> local_data/acme_corp/hr_manual.txt
```

**3. Create a Large DOCX File (`q3_earnings_report.docx`):**
We'll use a Python script to generate a valid, multi-page `.docx` file.

*   First, create the script:
    ```bash
    cat <<EOF > create_docx.py
    import docx
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_docx.py <output_path>")
        sys.exit(1)

    output_path = sys.argv[1]
    doc = docx.Document()
    doc.add_heading('ACME Corp Q3 Earnings Report', 0)
    doc.add_paragraph(
        'This report details the financial results for the third quarter. '
        'Revenue grew by 12% to $150M, driven by strong performance in the international market. '
        'Net profit for the quarter was $18M.'
    )
    for i in range(1, 101):
        doc.add_heading(f'Analysis of Market Segment {i}', level=1)
        p = doc.add_paragraph(
            f'Detailed analysis for segment {i}. Sales of the "RoadRunner" product line increased by 30% in this segment. '
            'We anticipate continued demand and are scaling up production to meet it.'
        )
        p.add_run(' All figures are unaudited.').italic = True
    doc.save(output_path)
    print(f"Successfully created large DOCX at: {output_path}")
    EOF
    ```
*   Now, run the script to generate the DOCX file:
    ```bash
    python create_docx.py local_data/acme_corp/q3_earnings_report.docx
    ```

**4. Create a Corrupt PDF File (`corrupt_file.pdf`):**
This file will fail during parsing, allowing us to verify that the pipeline logs the error correctly without crashing the entire job.
```bash
echo "This is not a valid PDF file." > local_data/acme_corp/corrupt_file.pdf
```

### Step 4: Ingest Data via the API

Now, send an API request to start the ingestion process for our new files.

```bash
curl -X POST "http://localhost:8001/api/v1/ingest" \
-H "Content-Type: application/json" \
-d '{
  "client_id": "acme_corp",
  "files": [
    { "path": "local_data/acme_corp/hr_manual.txt", "metadata": {"document_type": "HR", "version": "4.2"} },
    { "path": "local_data/acme_corp/q3_earnings_report.docx", "metadata": {"document_type": "Finance", "quarter": "Q3"} },
    { "path": "local_data/acme_corp/corrupt_file.pdf", "metadata": {"document_type": "Unknown"} }
  ]
}'
```

The API will return a JSON response containing a unique `job_id`. **Copy this `job_id`—you will need it in the next steps.**

### Step 5: Trigger and Monitor the Airflow DAG

1.  Open the **Airflow UI** in your web browser: `http://localhost:8080`.
2.  Log in with the username `admin` and password `admin`.
3.  On the main DAGs page, find `ingestion_pipeline` and click the toggle on the left to **turn it On**.
4.  Click the **Play button (▶️)** on the far right of the `ingestion_pipeline` row.
5.  A dialog box will appear. In the "Config (JSON)" text area, paste the `job_id` you copied:
    ```json
    { "job_id": "YOUR_JOB_ID_HERE" }
    ```
6.  Click **"Trigger"**.
7.  Click on the `ingestion_pipeline` name to go to the Grid View. You will see a new DAG run start. Observe the following:
    *   The `process_single_file_task` will fan out into 3 parallel tasks.
    *   The tasks for `hr_manual.txt` and `q3_earnings_report.docx` will succeed (turn solid green).
    *   The task for `corrupt_file.pdf` will fail (turn solid red).
    *   The final `finalize_job_status` task will run and succeed, and the entire DAG run will be marked as successful (light green border), proving its resilience.

### Step 6: Verify the Outcome

Now, we confirm the results using the API and our verification script.

1.  **Check Detailed Job Status:** Replace `YOUR_JOB_ID_HERE` with the ID you copied. The `jq` command formats the JSON for readability.
    ```bash
    curl -X GET "http://localhost:8001/api/v1/jobs/YOUR_JOB_ID_HERE" | jq
    ```
    *   **Expected Outcome:** The overall job `status` will be `COMPLETED_WITH_ERRORS`. In the `files` list, you will see two `COMPLETED` and one `FAILED`. In the `errors` list, you will see a detailed traceback for the failure of `corrupt_file.pdf`.

2.  **Verify Vector Database:** Check that the content from the two successful files was chunked and stored in ChromaDB.
    ```bash
    python scripts/verify_chroma.py acme_corp
    ```
    *   **Expected Outcome:** The script will report a number of vectors found and will print the first few chunks of text from the HR manual and the earnings report.

### Step 7: Query the Ingested Data (RAG Test)

This is the final test to ensure the RAG functionality works.

1.  **Query the HR Manual:**
    ```bash
    curl -N -X POST "http://localhost:8001/api/v1/query" \
    -H "Content-Type: application/json" \
    -d '{
      "client_id": "acme_corp",
      "query": "How many days of PTO do employees get?"
    }'
    ```
    *   **Expected Response:** A streamed answer similar to: `The company provides 20 days of paid time off (PTO) annually, accrued monthly [source: /opt/airflow/local_data/acme_corp/hr_manual.txt].`

2.  **Query the Financial Report:**
    ```bash
    curl -N -X POST "http://localhost:8001/api/v1/query" \
    -H "Content-Type: application/json" \
    -d '{
      "client_id": "acme_corp",
      "query": "What was the net profit in the third quarter?"
    }'
    ```
    *   **Expected Response:** A streamed answer similar to: `The net profit for the quarter was $18M [source: /opt/airflow/local_data/acme_corp/q3_earnings_report.docx].`

---
**Test Complete.** If all steps were successful, you have validated the entire IngestIQ pipeline, including its data processing capabilities and fault tolerance.
