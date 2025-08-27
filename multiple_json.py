import json
import os

def add_client(name, phone, fault, technician, images):
    return {
        "name": name,
        "number": phone,
        "fault": fault,
        "technician": technician,
        "image ": [img for img in images if img.strip()]
    }