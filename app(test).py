from flask import Flask, render_template, request, redirect, url_for
from search import search_clients, get_image_base64, load_clients
from multiple_json import add_client
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    term = request.args.get('q', '')
    results = search_clients(term)
    
    # Prepare images for web display
    for client in results:
        client['image_data'] = []
        for path in client.get("image ", []):
            img_data = get_image_base64(path)
            if img_data:
                client['image_data'].append(img_data)
    
    return render_template('index.html', results=results, search_term=term)

@app.route('/add_client', methods=['GET', 'POST'])
def add_client_route():
    if request.method == 'POST':
        name = request.form['name']
        number = request.form['number']
        fault = request.form['fault']
        images = request.form.getlist('images[]')
        
        # Filter out empty image paths
        images = [img for img in images if img.strip()]
        
        # Load existing clients
        clients = load_clients()
        
        # Add new client
        new_client = {
            "name": name,
            "number": number,
            "fault": fault,
            "image ": images
        }
        clients.append(new_client)
        
        # Save back to file
        with open("client1.json", 'w') as f:
            json.dump(clients, f)
            
        return redirect(url_for('index'))
    
    return render_template('add_client.html')
# Add this new route to app.py
@app.route('/delete_client/<int:client_index>', methods=['POST'])
def delete_client(client_index):
    try:
        clients = load_clients()
        if 0 <= client_index < len(clients):
            del clients[client_index]
            with open("client1.json", 'w') as f:
                json.dump(clients, f)
            return redirect(url_for('index'))
        else:
            return "Invalid client index", 400
    except Exception as e:
        return f"Error deleting client: {str(e)}", 500
if __name__ == '__main__':
    app.run(debug=True)