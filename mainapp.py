from flask import Flask, render_template, request, redirect, url_for, jsonify, flash 
from datetime import datetime
from pathlib import Path
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from bson.objectid import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  # load .env file

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "supersecret")  # required for flash()

    # Configuration
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    BASE_DIR = Path(__file__).resolve().parent

    # Connect to MongoDB
    mongo_client = MongoClient(
        os.getenv("MONGO_URI"),
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    db = mongo_client.get_database()  # database from URI
    clients_collection = db.clients
    services_collection = db.services

    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def process_and_save_image(file, identifier):
        """Process and save an uploaded image with proper format handling"""
        try:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{identifier}_{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            img = Image.open(file.stream)
            if ext in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(save_path)
            return unique_filename
        except Exception as e:
            print(f"Error processing image {filename}: {str(e)}")
            return None

    @app.route('/')
    def index():
        clients = list(clients_collection.find())
        for client in clients:
            client["_id"] = str(client["_id"])  # ✅ Convert ObjectId to str
        return render_template('index.html', results=clients)

    @app.route('/search')
    def search():
        term = request.args.get('q', '').strip()
        results = list(clients_collection.find({
            "$or": [
                {"client_name": {"$regex": term, "$options": "i"}},
                {"phone_number": {"$regex": term, "$options": "i"}},
                {"fault_description": {"$regex": term, "$options": "i"}},
                {"assigned_technician": {"$regex": term, "$options": "i"}}
            ]
        }))
        for r in results:
            r["_id"] = str(r["_id"])  # ✅ Convert ObjectId to str
        return render_template('index.html', results=results, search_term=term)

    @app.route('/add_client', methods=['GET', 'POST'])
    def add_client():
        if request.method == 'POST':
            try:
                client_name = request.form.get("client_name")
                phone_number = request.form.get("phone_number")
                fault_description = request.form.get("fault_description")
                assigned_technician = request.form.get("assigned_technician")

                # Insert into MongoDB
                client = {
                    "client_name": client_name,
                    "phone_number": phone_number,
                    "fault_description": fault_description,
                    "assigned_technician": assigned_technician,
                    "created_at": datetime.utcnow(),
                    "image": []  # keep structure consistent
                }
                clients_collection.insert_one(client)

                return jsonify({"success": True, "message": "Client added successfully"})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        else:
            return render_template('add_client.html')

    @app.route('/delete/<record_id>', methods=['GET'])
    def delete_record(record_id):
        try:
            # ✅ Validate ObjectId
            try:
                object_id = ObjectId(record_id)
            except InvalidId:
                flash("Invalid record ID", "danger")
                return redirect(url_for('client_history'))

            # Try delete in clients first
            result = clients_collection.delete_one({"_id": object_id})
            if result.deleted_count == 0:
                services_collection.delete_one({"_id": object_id})

            flash("Record deleted successfully!", "success")
        except Exception as e:
            flash(f"Error deleting record: {str(e)}", "danger")
        
        return redirect(url_for('client_history'))
    
    @app.route('/clients', methods=['GET'])
    def get_clients():
        try:
            clients = []
            for client in clients_collection.find():
                client["_id"] = str(client["_id"])
                clients.append(client)

            return jsonify({"success": True, "clients": clients}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/search_history')
    def search_history():
        term = request.args.get('q', '').strip()
        
        clients = list(clients_collection.find({
            "$or": [
                {"client_name": {"$regex": term, "$options": "i"}},
                {"phone_number": {"$regex": term, "$options": "i"}}
            ]
        }))

        services = list(services_collection.find({
            "$or": [
                {"client_name": {"$regex": term, "$options": "i"}},
                {"collector_name": {"$regex": term, "$options": "i"}}
            ]
        }))

        history = []
        for client in clients:
            history.append({
                'type': 'client_record',
                'id': str(client['_id']),
                'date': client.get('created_at', ''),
                'name': client.get('client_name', ''),
                'data': client,
                'images': client.get('image', []),
                'contact': client.get('phone_number', '')
            })

        for service in services:
            history.append({
                'type': 'service_record',
                'id': str(service['_id']),
                'date': service.get('collection_date', ''),
                'name': service.get('client_name', ''),
                'data': service,
                'images': service.get('images', []),
                'contact': service.get('collector_contact', ''),
                'collector': service.get('collector_name', '')
            })
        
        return render_template('client_history.html', history=history, search_term=term)

    @app.route('/client_history')
    def client_history():
        clients = list(clients_collection.find())
        services = list(services_collection.find())
        
        history = []
        for client in clients:
            history.append({
                'type': 'client_record',
                'id': str(client['_id']),
                'date': client.get('created_at', ''),
                'name': client.get('client_name', ''),
                'data': client,
                'images': client.get('image', []),
                'contact': client.get('phone_number', '')
            })

        for service in services:
            history.append({
                'type': 'service_record',
                'id': str(service['_id']),
                'date': service.get('collection_date', ''),
                'name': service.get('client_name', ''),
                'data': service,
                'images': service.get('images', []),
                'contact': service.get('collector_contact', ''),
                'collector': service.get('collector_name', '')
            })

        return render_template('client_history.html', history=history)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
