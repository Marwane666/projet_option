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
    try:
        with open("static/data/products.json", "r", encoding='utf-8') as f:
            products = json.load(f)
            print(f"Loaded {len(products)} products successfully")
            return products
    except FileNotFoundError:
        print("Products file not found at static/data/products.json")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing products JSON: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error loading products: {e}")
        return {}

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = f'user_{int(time.time())}_{random.randint(1000, 9999)}'
    return session['user_id']

@app.route('/')
def acceuil():
    products = load_products()  # Load products from JSON
    return render_template('acceuil.html', products=products)

@app.route('/product/<product_id>')
def get_product(product_id):
    products = load_products()
    product = products.get(product_id)
    if not product:
        flash('Product not found')
        return redirect(url_for('catalog'))
    return render_template('product.html', product=product, product_id=product_id)

@app.route('/catalog')
def catalog():
    try:
        products = load_products()
        if not products:
            flash("No products available at the moment")
            return render_template('catalog.html', products={})
        return render_template('catalog.html', products=products)
    except Exception as e:
        print(f"Error in catalog route: {e}")
        return render_template('error.html', error_message="Failed to load product catalog"), 500

@app.route('/discount')
def discount():
    return render_template('discount.html')

@app.route('/tutos')
def tutos():
    return render_template('tutos.html')

def get_all_user_data(user_id):
    """Collect all available data for a user"""
    # Get all sessions for the user
    sessions = list(db.user_sessions.find({'user': user_id}))
    
    # Get all cart activities
    cart_activities = list(db.cart.find({'user_id': user_id}))
    
    # Get all orders
    orders = list(db.orders.find({'user_id': user_id}))
    
    return {
        'sessions': sessions,
        'cart_activities': cart_activities,
        'orders': orders
    }

def calculate_session_duration(session):
    """Calculate the duration of a single session in seconds"""
    try:
        if 'startTime' in session and 'endTime' in session:
            start = datetime.fromisoformat(session['startTime'])
            end = datetime.fromisoformat(session['endTime'])
            return (end - start).total_seconds()
        elif 'startTime' in session and 'lastUpdate' in session:
            # For active sessions, use lastUpdate instead of endTime
            start = datetime.fromisoformat(session['startTime'])
            last_update = session['lastUpdate']
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update)
            return (last_update - start).total_seconds()
    except Exception as e:
        print(f"Error calculating session duration: {e}")
    return 0

def check_user_data_duration(user_id):
    """Check if user has accumulated enough interaction time"""
    # Get all sessions for the user
    sessions = list(db.user_sessions.find({'user': user_id}))
    total_duration = 0
    
    # Calculate total duration from all sessions
    for session in sessions:
        session_duration = calculate_session_duration(session)
        
        # Validate duration is reasonable (less than 1 hour per session)
        if 0 <= session_duration <= 3600:  # 3600 seconds = 1 hour
            total_duration += session_duration
            
        # Add time for interactions within the session
        interactions_count = len(session.get('interactions', []))
        total_duration += interactions_count * 2  # Add 2 seconds per interaction
        
        # Add time for mouse movements
        movements_count = len(session.get('mouseMovements', []))
        total_duration += movements_count * 0.1  # Add 0.1 second per mouse movement
        
        # Add time for scroll events
        scroll_count = session.get('scrollData', {}).get('totalScrolls', 0)
        total_duration += scroll_count * 0.5  # Add 0.5 second per scroll

    # Get cart activities
    cart_activities = list(db.cart.find({'user_id': user_id}))
    cart_duration = len(cart_activities) * 5  # 5 seconds per cart activity
    
    # Get total active time
    total_active_time = total_duration + cart_duration
    
    print(f"User {user_id} total active time: {total_active_time} seconds")
    return total_active_time >= 20

def has_existing_persona(user_id):
    """Check if user already has a persona prediction"""
    return db.personas.find_one({'user_id': user_id}) is not None

def trigger_persona_prediction(user_id):
    """Trigger persona prediction if conditions are met"""
    if not has_existing_persona(user_id):
        has_enough_time = check_user_data_duration(user_id)
        if has_enough_time:
            # Get user data but limit the amount
            user_data = get_all_user_data(user_id)
            
            # Create a summarized user profile
            user_profile = {
                'user_id': user_id,
                'session_stats': {
                    'total_sessions': len(user_data['sessions']),
                    'avg_duration': sum(calculate_session_duration(s) for s in user_data['sessions']) / max(len(user_data['sessions']), 1),
                    'total_interactions': sum(len(s.get('interactions', [])) for s in user_data['sessions']),
                    'total_movements': sum(len(s.get('mouseMovements', [])) for s in user_data['sessions']),
                    'total_scrolls': sum(s.get('scrollData', {}).get('totalScrolls', 0) for s in user_data['sessions'])
                },
                'cart_stats': {
                    'total_items': len(user_data['cart_activities']),
                    'product_categories': list(set(item.get('category', 'unknown') for item in user_data['cart_activities']))
                },
                'order_stats': {
                    'total_orders': len(user_data['orders']),
                    'total_spent': sum(order.get('total', 0) for order in user_data['orders'])
                }
            }
            
            # Predict persona with summarized data
            persona_predictor = PersonaPredictor()
            persona = persona_predictor.predict_persona(str(user_profile))
            
            # Save to MongoDB
            db.personas.insert_one({
                'user_id': user_id,
                'persona': str(persona),
                'timestamp': datetime.now(),
                'profile_snapshot': user_profile
            })
            
            return str(persona)
    return None

@app.route('/record-session-data', methods=['POST'])
def record_session_data():
    data = request.get_json()
    session_id = data.get('sessionId')
    user_id = get_user_id()

    # First, check if session exists
    existing_session = db.user_sessions.find_one({'sessionId': session_id})
    
    if existing_session:
        # Update existing session
        update_data = {
            'lastUpdate': datetime.now(),
            'endTime': data.get('endTime'),
            'isFinal': data.get('isFinal', False)
        }
        
        # Prepare arrays for update
        new_movements = data.get('mouseMovements', [])
        new_scroll_ranges = data.get('scrollData', {}).get('scrollRanges', [])
        new_interactions = data.get('interactions', [])
        
        # Update document with new data
        db.user_sessions.update_one(
            {'sessionId': session_id},
            {
                '$set': update_data,
                '$addToSet': {
                    'mouseMovements': {'$each': new_movements},
                    'scrollData.scrollRanges': {'$each': new_scroll_ranges},
                    'interactions': {'$each': new_interactions}
                },
                '$inc': {
                    'scrollData.totalScrolls': data.get('scrollData', {}).get('totalScrolls', 0)
                }
            }
        )
    else:
        # Create new session document
        new_session = {
            'sessionId': session_id,
            'user': user_id,
            'page': data.get('page'),
            'startTime': data.get('startTime'),
            'createdAt': datetime.now(),
            'lastUpdate': datetime.now(),
            'mouseMovements': data.get('mouseMovements', []),
            'scrollData': {
                'totalScrolls': data.get('scrollData', {}).get('totalScrolls', 0),
                'scrollRanges': data.get('scrollData', {}).get('scrollRanges', [])
            },
            'interactions': data.get('interactions', [])
        }
        db.user_sessions.insert_one(new_session)

    # Check if we should predict persona
    persona = trigger_persona_prediction(user_id)
    
    response_data = {"message": "Session data recorded"}
    if persona:
        response_data["persona"] = persona
    
    return jsonify(response_data)

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
        # Handle root path specially
        if page == 'root':
            page = '/'
        else:
            page = '/' + page if not page.startswith('/') else page

        # Get all sessions for the user and page
        sessions = list(db.user_sessions.find({
            'user': user,
            'page': page
        }))

        # Format sessions for response
        formatted_sessions = []
        for session in sessions:
            formatted_session = {
                '_id': str(session['_id']),
                'displayTime': session.get('startTime', 'No timestamp'),
                'page': session.get('page', 'Unknown page'),
                'movements_count': len(session.get('mouseMovements', [])),
                'timestamp': session.get('startTime')
            }
            formatted_sessions.append(formatted_session)
        
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
        user_id = get_user_id()  # Use unified user ID
        
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
