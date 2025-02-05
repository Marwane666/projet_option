from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from datetime import datetime
import json
from predict_persona import PersonaPredictor, save_persona_to_markdown
# Initialize Flask app
app = Flask(__name__)

# MongoDB configuration
mongo_client = MongoClient("mongodb+srv://simaxben:simax30581@cluster0.66tg3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # Update with your MongoDB URI
db = mongo_client['user_data']

# Load product data from JSON
def load_products():
    with open("static/data/products.json", "r") as f:
        return json.load(f)

@app.route('/')
def acceuil():
    return render_template('acceuil.html')

@app.route('/catalog')
def catalog():
    products = load_products()
    return render_template('catalog.html', products=products)

@app.route('/discount')
def discount():
    return render_template('discount.html')


@app.route('/tutos')
def tutos():
    return render_template('tutos.html')

@app.route('/product/<product_id>')
def product_page(product_id):
    products = load_products()
    product = products.get(product_id)
    if not product:
        return "Product not found", 404
    return render_template('product.html', product=product)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        db.contact_messages.insert_one({
            "name": name,
            "email": email,
            "message": message,
            "timestamp": datetime.now()
        })
        return redirect(url_for('acceuil'))
    return render_template('contact.html')

collected_user_data = {}

@app.route('/record-interaction', methods=['POST'])
def record_interaction():
    data = request.get_json()
    interaction = data.get("interaction")  # Text of the button or link
    page = data.get("page", "unknown")  # Page where the interaction occurred
    user = data.get("user", "anonymous")  # User identifier (if available)
    timestamp = datetime.now()

    # In-memory collection
    if user not in collected_user_data:
        collected_user_data[user] = []
    collected_user_data[user].append({
        "interaction": interaction,
        "page": page,
        "user": user,
        "timestamp": timestamp
    })

    # Automatically predict persona if we have 3
    if len(collected_user_data[user]) == 3:
        predictor = PersonaPredictor()
        events_str = str(collected_user_data[user])
        response = predictor.predict_persona(events_str)
        save_persona_to_markdown(user, str(response))
        # You can reset collected_user_data[user] if desired
        # collected_user_data[user] = []

    # Save the interaction to MongoDB
    db.interactions.insert_one({
        "interaction": interaction,
        "page": page,
        "user": user,
        "timestamp": timestamp
    })

    return jsonify({"message": f"Interaction '{interaction}' recorded."})


@app.route('/record-navigation', methods=['POST'])
def record_navigation():
    data = request.get_json()
    page = data.get("page")
    user = data.get("user", "anonymous")
    timestamp = datetime.now()

    db.navigation.insert_one({
        "page": page,
        "user": user,
        "timestamp": timestamp
    })

    return jsonify({"message": f"Navigation to '{page}' recorded."})

"""  TO ADD IN SCRIPT JS IF WE NEED TO RECORD TIME SPENT """
@app.route('/record-time', methods=['POST'])
def record_time():
    data = request.get_json()
    page = data.get("page")
    user = data.get("user", "anonymous")
    time_spent = data.get("time_spent", 0)

    db.time_spent.insert_one({
        "page": page,
        "user": user,
        "time_spent": time_spent,
        "timestamp": datetime.now()
    })

    return jsonify({"message": f"Time spent on '{page}' recorded."})


@app.route('/record-mouse-movements', methods=['POST'])
def record_mouse_movements():
    data = request.get_json()
    movements = data.get('movements', [])
    page = data.get('page', 'unknown')
    user = data.get('user', 'anonymous')

    if movements:
        db.mouse_movements.insert_many([
            {**movement, "page": page, "user": user, "timestamp": datetime.now()}
            for movement in movements
        ])

    return jsonify({"message": f"{len(movements)} movements recorded."})

@app.route('/predict-persona/<user_id>', methods=['GET'])
def predict_user_persona(user_id):
    # Gather the last three events for the user
    events_cursor = db.interactions.find({"user": user_id}).sort("timestamp", -1).limit(3)
    three_events = list(events_cursor)
    # Convert to string for the predictor
    events_str = str(three_events)
    
    persona_predictor = PersonaPredictor()
    persona_response = persona_predictor.predict_persona(events_str)

    # Save to a markdown file
    save_persona_to_markdown(user_id, str(persona_response))
    return jsonify({"user_id": user_id, "persona": str(persona_response)})

if __name__ == '__main__':
    app.run(debug=True)
