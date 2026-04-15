import os

from flask import Flask, g, render_template, request, redirect, session, flash

from helpers import resolve_image_path, split_products_for_sections
from model import Database
from subadmin_app import subadmin_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret123")
app.register_blueprint(subadmin_bp)


def get_db():
    if "db" not in g:
        g.db = Database()
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.cursor.close()
            db.db.close()
        except Exception:
            pass


@app.context_processor
def inject_template_helpers():
    return {"product_image_src": resolve_image_path}
# ---------------- ROOT ---------------- #
@app.route('/')
def index():
    return redirect('/login')


# ---------------- REGISTER ---------------- #
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        print("REGISTER HIT")  # debug

        get_db().register_user(request.form)
        return redirect('/login')

    return render_template('register.html')


# ---------------- LOGIN ---------------- #
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_db().login_user(email, password)

        if user:
            session['user_id'] = user['USER_ID']
            return redirect('/index')
        else:
            flash("Invalid credentials. Please try again.", "error")
            return redirect('/login')

    return render_template('login.html')
# ---------------- HOME ---------------- #
@app.route('/index')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_db().get_products()
    featured_products = products[:6]
    trending_products = products[3:9] if len(products) > 6 else products[:6]
    user = get_db().get_user_by_id(session['user_id'])

    return render_template(
        'index.html',
        featured_products=featured_products,
        trending_products=trending_products,
        user=user
    )


# ---------------- ABOUT-US ---------------- #
@app.route('/about-us')
def about_us():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('about-us.html')

# ---------------- SHOP ---------------- #
@app.route('/shop')
def shop():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_db().get_products()
    return render_template(
        'catalog.html',
        products=products,
        page_title='Shop',
        page_heading='All Jewellery Collection',
        page_description='Explore our complete collection of elegant jewellery pieces curated for every occasion.'
    )


# ---------------- WOMEN ---------------- #
@app.route('/women')
def women():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_db().get_products()
    women_products, _ = split_products_for_sections(products)
    return render_template(
        'catalog.html',
        products=women_products,
        page_title='Women',
        page_heading='Women Collection',
        page_description='Graceful everyday pieces and statement jewellery designed with a softer, refined look.'
    )


# ---------------- MEN ---------------- #
@app.route('/men')
def men():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_db().get_products()
    _, men_products = split_products_for_sections(products)
    return render_template(
        'catalog.html',
        products=men_products,
        page_title='Men',
        page_heading='Men Collection',
        page_description='Bold chains, bands, and modern accessories selected for a sharper, minimalist style.'
    )


# ---------------- USER ---------------- #
@app.route('/user')
def user():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user_profile = get_db().get_user_by_id(user_id)
    cart_items = get_db().get_cart(user_id)
    order_count = get_db().get_order_count(user_id)
    cart_total = sum(item['PRICE'] * item['QUANTITY'] for item in cart_items)

    return render_template(
        'user.html',
        user=user_profile,
        cart_items=cart_items[:3],
        cart_count=sum(item['QUANTITY'] for item in cart_items),
        cart_total=cart_total,
        order_count=order_count
    )


# ---------------- PRODUCT ---------------- #
@app.route('/product/<int:product_id>')
def product(product_id):
    if 'user_id' not in session:
        return redirect('/login')


    product = get_db().get_product(product_id)
    return render_template('product.html', product=product)



# ---------------- ADD TO CART ---------------- #
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1)
    next_page = request.form.get('next') or '/cart'

    if not product_id:
        return "Product ID is missing", 400

    try:
        product_id = int(product_id)
        quantity = max(1, int(quantity))
    except ValueError:
        return "Invalid product data", 400

    get_db().add_to_cart(user_id, product_id, quantity)
    flash("Item added to cart successfully.", "success")

    return redirect(next_page)


# ---------------- CART ---------------- #
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    cart_items = get_db().get_cart(user_id)


    total = sum(item['PRICE'] * item['QUANTITY'] for item in cart_items)

    return render_template('cart.html', cart=cart_items, total=total)


# ---------------- REMOVE FROM CART ---------------- #
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    user_id = session['user_id']
    get_db().cursor.execute(
        "DELETE FROM SHOPPING_CART WHERE USER_ID=%s AND PRODUCT_ID=%s",
        (user_id, product_id)
    )
    get_db().db.commit()


    return redirect('/cart')


# ---------------- CHECKOUT ---------------- #
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    cart_items = get_db().get_cart(user_id)

    total = sum(item['PRICE'] * item['QUANTITY'] for item in cart_items)

    if request.method == 'POST':
        address = request.form['address']
        payment_method = request.form['payment_method']

        # 1. Create Order
        order_id = get_db().create_order(user_id, total, payment_method)

        # 2. Add Order Items
        get_db().add_order_items(order_id, cart_items)

        # 3. Payment
        get_db().add_payment(order_id, total, payment_method)

        # 4. Shipping
        get_db().add_shipping(order_id, address)

        # 5. Clear Cart
        get_db().clear_cart(user_id)

        return redirect('/success')

    return render_template('checkout.html', cart=cart_items, total=total)



# ---------------- PLACE ORDER ---------------- #
@app.route('/place_order', methods=['POST'])
def place_order():
    user_id = session['user_id']
    payment_method = request.form['payment_method']

    cart_items = get_db().get_cart(user_id)
    total = sum(item['PRICE'] * item['QUANTITY'] for item in cart_items)

    order_id = get_db().create_order(user_id, total, payment_method)

    get_db().add_order_items(order_id, cart_items)
    get_db().add_payment(order_id, total, payment_method)
    get_db().add_shipping(order_id, "User Address")  # later dynamic

    get_db().clear_cart(user_id)

    return redirect('/success')



# ---------------- SUCCESS ---------------- #
@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('success.html')


# ---------------- LOGOUT ---------------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- RUN ---------------- #
if __name__ == '__main__':
    app.run(debug=os.getenv("FLASK_DEBUG", "true").lower() == "true")
