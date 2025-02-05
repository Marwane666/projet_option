from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
from datetime import datetime
import json
from bson import ObjectId
import time
import random
from predict_persona import PersonaPredictor, save_persona_to_markdown

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# MongoDB configuration
mongo_client = MongoClient("mongodb+srv://simaxhah:simax30581@cluster0.ub2v4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client['user_data']

def load_products():
    with open("static/data/products.json", "r") as f:
        return json.load(f)

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = f'user_{int(time.time())}_{random.randint(1000, 9999)}'
    return session['user_id']

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
    interaction = data.get("interaction")
    page = data.get("page", "unknown")
    user = data.get("user", "anonymous")
    timestamp = datetime.now()

    if user not in collected_user_data:
        collected_user_data[user] = []
    collected_user_data[user].append({
        "interaction": interaction,
        "page": page,
        "user": user,
        "timestamp": timestamp
    })

    if len(collected_user_data[user]) == 3:
        predictor = PersonaPredictor()
        events_str = str(collected_user_data[user])
        response = predictor.predict_persona(events_str)
        save_persona_to_markdown(user, str(response))

    db.interactions.insert_one({
        "interaction": interaction,
        "page": page,
        "user": user,
        "timestamp": timestamp,
        "scroll_position": data.get("scrollPosition", 0)
    })
    return jsonify({"message": "Interaction recorded."})

@app.route('/record-navigation', methods=['POST'])
def record_navigation():
    data = request.get_json()
    db.navigation.insert_one({
        "page": data.get("page"),
        "user": data.get("user", "anonymous"),
        "timestamp": datetime.now()
    })
    return jsonify({"message": "Navigation recorded."})

@app.route('/record-time', methods=['POST'])
def record_time():
    data = request.get_json()
    db.time_spent.insert_one({
        "page": data.get("page"),
        "user": data.get("user", "anonymous"),
        "time_spent": data.get("time_spent", 0),
        "scroll_position": data.get("scrollPosition", 0),
        "timestamp": datetime.now()
    })
    return jsonify({"message": "Time spent recorded."})

@app.route('/record-mouse-movements', methods=['POST'])
def record_mouse_movements():
    data = request.get_json()
    movements = data.get('movements', [])
    page = data.get('page', 'unknown')
    user = data.get('user', 'anonymous')
    scroll_percentage = data.get('scrollPercentage', 0)
    dwell_time = data.get('dwellTime', {})
    scroll_activity = data.get('scrollActivity', {})

    if movements:
        db.mouse_movements.insert_one({
            "movements": movements,
            "page": page,
            "user": user,
            "scroll_percentage": scroll_percentage,
            "dwell_time": dwell_time,
            "scroll_activity": scroll_activity,
            "timestamp": datetime.now()
        })

    return jsonify({"message": f"{len(movements)} movements recorded."})

@app.route('/record-session-data', methods=['POST'])
def record_session_data():
    data = request.get_json()
    session_id = data.get('sessionId')

    # Update existing session or create new one
    db.user_sessions.update_one(
        {'sessionId': session_id},
        {
            '$set': {
                'lastUpdate': datetime.now(),
                'endTime': data.get('endTime'),
                'isFinal': data.get('isFinal', False)
            },
            '$push': {
                'mouseMovements': {'$each': data.get('mouseMovements', [])},
                'scrollData.scrollRanges': {'$each': data.get('scrollData', {}).get('scrollRanges', [])}
            },
            '$inc': {
                'scrollData.totalScrolls': data.get('scrollData', {}).get('totalScrolls', 0)
            },
            '$setOnInsert': {
                'user': data.get('user'),
                'page': data.get('page'),
                'startTime': data.get('startTime'),
                'createdAt': datetime.now()
            }
        },
        upsert=True
    )

    return jsonify({"message": "Session data recorded"})

@app.route('/heatmap')
def heatmap_view():
    # Get unique users
    users = db.user_sessions.distinct('user')
    return render_template('heatmap.html', users=users)

@app.route('/get-user-pages/<user>')
def get_user_pages(user):
    # Get unique pages for the user
    pages = db.user_sessions.distinct('page', {'user': user})
    return jsonify(pages)

@app.route('/get-user-sessions/<user>/<path:page>')
def get_user_sessions(user, page):
    try:
        # Debug print
        print(f"\n=== Looking for sessions ===")
        print(f"User: {user}")
        print(f"Page: {page}")

        # Get all sessions for the user and page
        sessions = list(db.user_sessions.find({
            'user': user,
            'page': '/' + page if not page.startswith('/') else page
        }))

        # Debug print
        print(f"\nFound {len(sessions)} sessions")
        for session in sessions:
            print("\nSession data:")
            print(f"ID: {session.get('_id')}")
            print(f"Timestamp: {session.get('timestamp')}")
            print(f"Page: {session.get('page')}")
            print(f"Movements count: {len(session.get('movements', []))}")
            print("Raw session:", session)

        # Format sessions for response
        formatted_sessions = []
        for session in sessions:
            formatted_session = {
                '_id': str(session['_id']),
                'displayTime': session.get('timestamp', session.get('startTime', 'No timestamp')),
                'page': session.get('page', 'Unknown page'),
                'movements_count': len(session.get('movements', []))
            }
            formatted_sessions.append(formatted_session)

        # Debug print
        print("\nFormatted sessions:", formatted_sessions)
        
        return jsonify(formatted_sessions)

    except Exception as e:
        print(f"\nError in get_user_sessions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-movement-data', methods=['POST'])
def get_movement_data():
    data = request.get_json()
    page = data.get('page')
    date_start = datetime.fromisoformat(data.get('dateStart'))
    date_end = datetime.fromisoformat(data.get('dateEnd'))

    # Query sessions for the specified page and date range
    sessions = db.user_sessions.find({
        'page': page,
        'startTime': {
            '$gte': date_start,
            '$lte': date_end
        }
    })

    total_sessions = 0
    all_movements = []
    all_dwell_times = {}

    # Aggregate data from all matching sessions
    for session in sessions:
        total_sessions += 1
        all_movements.extend(session.get('mouseMovements', []))
        
        # Combine dwell times from all sessions
        for zone, time in session.get('dwellTimes', {}).items():
            all_dwell_times[zone] = all_dwell_times.get(zone, 0) + time

    # Calculate statistics
    most_active_zones = sorted(all_dwell_times.items(), key=lambda x: x[1], reverse=True)[:5]
    avg_dwell_time = sum(all_dwell_times.values()) / len(all_dwell_times) if all_dwell_times else 0

    return jsonify({
        'movements': all_movements,
        'totalSessions': total_sessions,
        'mostActiveZones': [f"Zone {zone}" for zone, _ in most_active_zones],
        'averageDwellTime': avg_dwell_time / 1000,  # Convert to seconds
        'totalInteractions': len(all_movements)
    })

@app.route('/get-session-data/<session_id>')
def get_session_data(session_id):
    from bson import ObjectId, json_util
    import json

    try:
        session = db.user_sessions.find_one({'_id': ObjectId(session_id)})
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Process mouse movements
        if 'movements' in session:
            processed_movements = []
            for m in session['movements']:
                processed_movements.append({
                    'x': int(m['x'].get('$numberInt', m['x'])),
                    'y': int(m['y'].get('$numberInt', m['y'])),
                    'timestamp': m['timestamp']
                })
            session['mouseMovements'] = processed_movements

        # Convert timestamp
        if 'timestamp' in session and '$date' in session['timestamp']:
            timestamp = datetime.fromtimestamp(int(session['timestamp']['$date']['$numberLong'])/1000)
            session['timestamp'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Process scroll data
        if 'scroll_activity' in session:
            scroll_data = session['scroll_activity']
            session['scrollData'] = {
                'totalScrolls': int(scroll_data.get('totalScrolls', {}).get('$numberInt', 0)),
                'scrollRanges': scroll_data.get('scrollRanges', [])
            }

        # Clean up the response
        session['_id'] = str(session['_id'])
        
        return jsonify(session)

    except Exception as e:
        print(f"Error processing session data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/cart')
def view_cart():
    user_id = get_user_id()
    cart_items = list(db.cart.find({'user_id': user_id}))
    
    # Convert ObjectId to string for each item
    for item in cart_items:
        item['_id'] = str(item['_id'])
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        user_id = get_user_id()
        
        cart_item = {
            'user_id': user_id,
            'product_id': data['product_id'],
            'name': data['name'],
            'price': float(data['price']),
            'quantity': int(data['quantity']),
            'total': float(data['price']) * int(data['quantity']),
            'added_at': datetime.now()
        }
        
        # Insert into cart collection
        db.cart.insert_one(cart_item)
        
        # Update session cart count
        cart_count = db.cart.count_documents({'user_id': user_id})
        session['cart_count'] = cart_count
        
        return jsonify({
            'success': True,
            'cart_count': cart_count
        })
    except Exception as e:
        print(f"Error adding to cart: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    user_id = get_user_id()
    
    item = db.cart.find_one({'_id': ObjectId(data['itemId']), 'user_id': user_id})
    if item:
        db.cart.update_one(
            {'_id': ObjectId(data['itemId'])},
            {'$set': {
                'quantity': data['quantity'],
                'total': item['price'] * data['quantity']
            }}
        )
    
    return jsonify({'success': True})

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    user_id = get_user_id()
    
    db.cart.delete_one({'_id': ObjectId(data['itemId']), 'user_id': user_id})
    return jsonify({'success': True})

@app.route('/checkout', methods=['GET'])
def checkout():
    user_id = get_user_id()
    cart_items = list(db.cart.find({'user_id': user_id}))
    
    if not cart_items:
        flash('Your cart is empty')
        return redirect(url_for('view_cart'))
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/process-order', methods=['POST'])
def process_order():
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        # Get cart items
        cart_items = list(db.cart.find({'user_id': user_id}))
        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'})

        total = sum(item['price'] * item['quantity'] for item in cart_items)
        
        # Create order
        order = {
            'user_id': user_id,
            'items': cart_items,
            'total': total,
            'shipping_info': {
                'name': f"{data['firstName']} {data['lastName']}",
                'email': data['email'],
                'address': data['address'],
                'country': data['country'],
                'city': data['city'],
                'zip': data['zip']
            },
            'payment_info': {
                'card_name': data['cardName'],
                'card_number': '****' + data['cardNumber'][-4:],  # Store only last 4 digits
                'expiration': data['expiration']
            },
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        # Save order
        result = db.orders.insert_one(order)
        
        if result.inserted_id:
            # Clear cart after successful order
            db.cart.delete_many({'user_id': user_id})
            session['cart_count'] = 0
            
            return jsonify({
                'success': True,
                'order_id': str(result.inserted_id)
            })
        
        return jsonify({
            'success': False,
            'error': 'Failed to create order'
        })

    except Exception as e:
        print(f"Error processing order: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/order-confirmation/<order_id>')
def order_confirmation(order_id):
    try:
        order = db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            flash('Order not found')
            return redirect(url_for('view_cart'))
            
        return render_template('order_confirmation.html', order=order)
    except Exception as e:
        flash('Error retrieving order')
        return redirect(url_for('view_cart'))

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
