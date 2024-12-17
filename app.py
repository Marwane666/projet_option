from flask import Flask, render_template, redirect, url_for, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", title="Store")

# Routes du menu principal et autres pages
@app.route("/home")
def home():
    return redirect(url_for('index'))

@app.route("/about")
def about():
    return render_template("about-us.html", title="About Us")

@app.route("/timeline")
def timeline():
    return render_template("timeline.html", title="Timeline")

@app.route("/cart")
def cart():
    return render_template("view-cart.html", title="Your Cart")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html", title="Checkout")

@app.route("/invoice")
def invoice():
    return render_template("invoice.html", title="Invoice")

@app.route("/contact")
def contact():
    return render_template("contact-1.html", title="Contact Us")

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html", title="Wishlist")

@app.route("/shop/collection")
def shop_collection():
    return render_template("shop-collection-sub.html", title="Shop Collection")

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    # Vous récupérerez le produit via product_id
    return render_template("product-detail.html", product_id=product_id, title="Product Detail")

@app.route("/brands")
def brands():
    return render_template("brands.html", title="Brands")

@app.route("/contact-us")
def contact_us():
    return render_template("contact-us.html", title="Contact Us")

@app.route("/faq")
def faq():
    return render_template("faq.html", title="FAQ")

@app.route("/store")
def store():
    return render_template("store.html", title="Store")

@app.route("/payment")
def payment():
    return render_template("payment.html", title="Payment")

@app.route("/account")
def account():
    return render_template("account.html", title="My Account")

@app.route("/blog")
def blog():
    return render_template("blog.html", title="Blog")

@app.route("/products")
def products():
    return render_template("products.html", title="Products")

@app.route("/shop/now")
def shop_now():
    return render_template("shop-now.html", title="Shop Now")

# Routes pour les fonctionnalités supplémentaires (modales, offcanvas)
@app.route("/compare")
def compare_page():
    # Page ou fragment pour la comparaison
    return render_template("compare.html", title="Compare")

@app.route("/product/<int:product_id>/quick-view")
def quick_view(product_id):
    # Fragment pour affichage dans une modal
    return render_template("partials/quick_view.html", product_id=product_id, title="Quick View")

@app.route("/product/<int:product_id>/quick-add", methods=['POST'])
def quick_add(product_id):
    # Logique d’ajout rapide au panier (retour JSON)
    return jsonify({'status': 'success'})

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Logique d’authentification
        pass
    return render_template("login.html", title="Login")

@app.route("/search")
def search():
    query = request.args.get('q', '')
    return render_template("search.html", query=query, title="Search Results")

@app.route("/shopping-cart")
def shopping_cart():
    return render_template("shopping-cart.html", title="Your Cart")

if __name__ == '__main__':
    app.run(debug=True)
