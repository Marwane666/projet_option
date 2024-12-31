from flask import Blueprint, render_template, jsonify, request
from app.extensions import mongo
from datetime import datetime


main = Blueprint('main', __name__)

@main.route("/")
def index():
    return render_template("index.html", title="Home")

@main.route("/1")
def index1():
    return render_template("index1.html", title="Home")

@main.route("/store")
def store():
    return render_template("store.html", title="Store")

@main.route("/heatmap")
def heatmap():
    return render_template("heatmap.html", title="heatmap")
@main.route("/heatmap1")
def heatmap1():
    return render_template("heatmap1.html", title="heatmap1")
@main.route("/heatmap2")
def heatmap2():
    return render_template("heatmap2.html", title="heatmap2")
@main.route("/heatmap3")
def heatmap3():
    return render_template("heatmap3.html", title="heatmap3")

@main.route("/test-db")
def test_db():
    try:
        from app.extensions import mongo
        mongo.db.command("ping")
        return "Connexion réussie avec MongoDB !"
    except Exception as e:
        return f"Erreur : {e}"


@main.route("/shop/now")
def shop_now():
    return render_template("shop-now.html", title="Shop Now")
    
    
@main.route("/record-interaction", methods=["POST"])
def record_interaction():
    """
    Enregistre une interaction utilisateur (clic sur un bouton, etc.)
    """
    data = request.get_json()
    interaction = data.get("interaction")
    page = data.get("page", "unknown")
    user = data.get("user", "anonymous")
    timestamp = datetime.now()

    # Enregistre les données dans MongoDB
    mongo.db.interactions.insert_one({
        "type": "interaction",
        "interaction": interaction,
        "page": page,
        "user": user,
        "timestamp": timestamp
    })

    return jsonify({"message": f"Interaction '{interaction}' enregistrée."})


@main.route("/record-navigation", methods=["POST"])
def record_navigation():
    """
    Enregistre une navigation de l'utilisateur (changement de page)
    """
    data = request.get_json()
    page = data.get("page")
    user = data.get("user", "anonymous")
    timestamp = datetime.now()

    # Enregistre les données dans MongoDB
    mongo.db.navigation.insert_one({
        "type": "navigation",
        "page": page,
        "user": user,
        "timestamp": timestamp
    })

    return jsonify({"message": f"Navigation vers '{page}' enregistrée."})


@main.route("/record-time", methods=["POST"])
def record_time():
    """
    Enregistre le temps passé sur une page par l'utilisateur
    """
    data = request.get_json()
    page = data.get("page")
    user = data.get("user", "anonymous")
    time_spent = data.get("time_spent", 0)
    timestamp = datetime.now()

    # Enregistre les données dans MongoDB
    mongo.db.time_spent.insert_one({
        "type": "time_spent",
        "page": page,
        "user": user,
        "time_spent": time_spent,
        "timestamp": timestamp
    })

    return jsonify({"message": f"Temps de {time_spent} secondes sur '{page}' enregistré."})


@main.route('/record-mouse-movements', methods=['POST'])
def record_mouse_movements():
    """
    Enregistre les mouvements de souris dans MongoDB
    """
    data = request.get_json()
    movements = data.get('movements', [])
    page = data.get('page', 'unknown')
    user = data.get('user', 'anonymous')

    # Insérer dans MongoDB
    if movements:
        mongo.db.mouse_movements.insert_many([
            {
                "x": movement["x"],
                "y": movement["y"],
                "timestamp": movement["timestamp"],
                "page": page,
                "user": user,
            }
            for movement in movements
        ])

    return jsonify({"message": f"{len(movements)} mouvements enregistrés."})

@main.route('/get-mouse-movements', methods=['GET'])
def get_mouse_movements():
    """
    Récupère les mouvements stockés dans MongoDB
    """
    page = request.args.get('page', 'unknown')
    user = request.args.get('user', 'anonymous')

    # Rechercher les mouvements dans MongoDB
    movements = list(mongo.db.mouse_movements.find(
        {"page": page, "user": user},
        {"_id": 0, "x": 1, "y": 1, "timestamp": 1}
    ))

    return jsonify(movements)

