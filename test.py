from flask import Flask, jsonify, render_template
from app.extensions import mongo

app = Flask(__name__)

# Exemple de route pour récupérer les produits
@app.route("/products", methods=["GET"])
def get_products():
    products = mongo.db.products.find()  # Récupère tous les produits
    product_list = [{"name": p["name"], "price": p["price"]} for p in products]
    return jsonify(product_list)

# Exemple de route pour insérer un produit
@app.route("/products/add", methods=["POST"])
def add_product():
    new_product = {
        "name": "Produit Exemple",
        "price": 20.99,
        "stock": 10
    }
    mongo.db.products.insert_one(new_product)
    return jsonify({"message": "Produit ajouté avec succès"})

@app.route("/store")
def store():
    products = list(mongo.db.products.find())
    return render_template("store.html", products=products)


@app.route("/test-db")
def test_db():
    try:
        mongo.db.command("ping")
        return "Connexion réussie avec MongoDB !"
    except Exception as e:
        return f"Erreur : {e}"
