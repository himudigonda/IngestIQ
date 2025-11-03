#!/bin/bash
# Install dependencies as airflow user
pip install --user --no-cache-dir chromadb openai langchain-text-splitters pypdf python-docx pytesseract Pillow python-magic pymongo || true

