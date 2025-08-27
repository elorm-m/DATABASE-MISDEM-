import json
from PIL import Image
import io
import base64
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
def load_clients():
    with open(BASE_DIR / "client1.json", "r") as f:
        return json.load(f)

def search_clients(term):
    clients = load_clients()
    term = term.strip().lower()
    
    return [
        c for c in clients
        if term in c["name"].lower() 
        or term in c["number"] 
        or term in c["fault"].lower()
        or term in c.get("technician", "").lower()  

    ]

def get_image_base64(filename):
    try:
        path = os.path.join('static', 'uploads', filename)
        img = Image.open(path)
        img.thumbnail((200, 200))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error processing image {filename}: {str(e)}")
        return None
    

# Add these functions to search.py
def load_service_submissions():
    with open(BASE_DIR / "service_submissions.json", "r") as f:
        return json.load(f)

def search_service_history(term):
    services = load_service_submissions()
    term = term.strip().lower()
    
    results = []
    for service in services:
        # Check all possible fields with fallbacks for old field names
        if (term in service.get('client_name', '').lower() or
            term in service.get('client_contact', '').lower() or
            term in service.get('device_name', service.get('machine_name', '')).lower() or
            term in service.get('device_issue', service.get('machine_issue', '')).lower() or
            term in service.get('collector_name', service.get('receiver_name', '')).lower() or
            term in service.get('collector_contact', service.get('receiver_contact', '')).lower()):
            
            # Normalize the service record
            normalized = {
                'client_name': service.get('client_name', ''),
                'client_contact': service.get('client_contact', ''),
                'device_name': service.get('device_name', service.get('machine_name', '')),
                'device_issue': service.get('device_issue', service.get('machine_issue', '')),
                'collector_name': service.get('collector_name', service.get('receiver_name', '')),
                'collector_contact': service.get('collector_contact', service.get('receiver_contact', '')),
                'collection_date': service.get('collection_date', service.get('date', '')),
                'status': service.get('status', 'Collected'),
                'submission_date': service.get('submission_date', '')
            }
            results.append(normalized)
    
    return results

def get_all_service_history():
    services = load_service_submissions()
    return [{
        'client_name': service.get('client_name', ''),
        'client_contact': service.get('client_contact', ''),
        'device_name': service.get('device_name', service.get('machine_name', '')),
        'device_issue': service.get('device_issue', service.get('machine_issue', '')),
        'collector_name': service.get('collector_name', service.get('receiver_name', '')),
        'collector_contact': service.get('collector_contact', service.get('receiver_contact', '')),
        'collection_date': service.get('collection_date', service.get('date', '')),
        'status': service.get('status', 'Collected'),
        'submission_date': service.get('submission_date', '')
    } for service in services]