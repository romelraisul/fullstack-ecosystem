import os
import requests
import json
from datetime import datetime
from typing import List
from pdfminer.high_level import extract_text
import docx

API_URL = "http://localhost:8000/index"

def parse_pdf(file_path: str) -> str:
    return extract_text(file_path)

def parse_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for param in doc.paragraphs])

def ingest_file(file_path: str):
    file_ext = file_path.split('.')[-1].lower()
    content = ""
    
    try:
        if file_ext == "pdf":
            content = parse_pdf(file_path)
        elif file_ext == "docx":
            content = parse_docx(file_path)
        elif file_ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            print(f"Skipping unsupported file type: {file_ext}")
            return

        doc_id = os.path.basename(file_path)
        payload = {
            "document_id": doc_id,
            "content": content,
            "metadata": {
                "author": "System",
                "created_at": datetime.now().isoformat(),
                "file_type": file_ext,
                "tags": ["automated-ingestion"]
            }
        }
        
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"Successfully indexed: {doc_id}")
        else:
            print(f"Failed to index {doc_id}: {response.text}")
            
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def batch_ingest(directory: str):
    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            ingest_file(full_path)

if __name__ == "__main__":
    # Example usage
    data_dir = r"G:\My Drive\Documents" # Adjust as needed
    if os.path.exists(data_dir):
        batch_ingest(data_dir)
    else:
        print(f"Directory not found: {data_dir}")
