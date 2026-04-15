import os

from flask import Blueprint, Flask, flash, redirect, render_template, request, session, url_for

from helpers import resolve_image_path
from model import Database


subadmin_bp = Blueprint("subadmin", __name__, url_prefix="/subadmin")
db = Database()


def is_subadmin_logged_in():
    return "subadmin_id" in session


@subadmin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        subadmin = db.login_subadmin(
            request.form["email"],
            request.form["password"]
        )

        if subadmin:
            session["subadmin_id"] = subadmin["SUBADMIN_ID"]
            return redirect(url_for("subadmin.dashboard"))

        flash("Invalid subadmin credentials. Please try again.", "error")
        return redirect(url_for("subadmin.login"))

    return render_template("subadmin_login.html")


@subadmin_bp.route("/dashboard")
def dashboard():
    if not is_subadmin_logged_in():
        return redirect(url_for("subadmin.login"))

    subadmin = db.get_subadmin_by_id(session["subadmin_id"])
    products = db.get_products()

    return render_template(
        "subadmin_dashboard.html",
        subadmin=subadmin,
        product_count=len(products),
        low_stock_count=sum(
            1 for product in products if product["STOCK_QUANTITY"] <= 5
        ),
        recent_products=products[:4]
    )


@subadmin_bp.route("/products")
def products():
    if not is_subadmin_logged_in():
        return redirect(url_for("subadmin.login"))

    return render_template(
        "subadmin_products.html",
        products=db.get_products()
    )


@subadmin_bp.route("/products/add", methods=["GET", "POST"])
def add_product():
    if not is_subadmin_logged_in():
        return redirect(url_for("subadmin.login"))

    if request.method == "POST":
        if db.create_product(request.form):
            flash("Product added successfully.", "success")
            return redirect(url_for("subadmin.products"))

        flash("Unable to add product. Please check the values and try again.", "error")
        return redirect(url_for("subadmin.add_product"))

    return render_template(
        "subadmin_product_form.html",
        form_title="Add Product",
        submit_label="Add Product",
        product=None
    )


@subadmin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    if not is_subadmin_logged_in():
        return redirect(url_for("subadmin.login"))

    product = db.get_product(product_id)

    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("subadmin.products"))

    if request.method == "POST":
        if db.update_product(product_id, request.form):
            flash("Product updated successfully.", "success")
            return redirect(url_for("subadmin.products"))

        flash("Unable to update product. Please try again.", "error")
        return redirect(url_for("subadmin.edit_product", product_id=product_id))

    return render_template(
        "subadmin_product_form.html",
        form_title="Edit Product",
        submit_label="Save Changes",
        product=product
    )


@subadmin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    if not is_subadmin_logged_in():
        return redirect(url_for("subadmin.login"))

    if db.delete_product(product_id):
        flash("Product deleted successfully.", "success")
    else:
        flash("Unable to delete product. It may be linked to existing records.", "error")

    return redirect(url_for("subadmin.products"))


@subadmin_bp.route("/logout")
def logout():
    session.pop("subadmin_id", None)
    return redirect(url_for("subadmin.login"))


def create_standalone_app():
    standalone_app = Flask(__name__)
    standalone_app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret123")
    standalone_app.register_blueprint(subadmin_bp)

    @standalone_app.context_processor
    def inject_template_helpers():
        return {"product_image_src": resolve_image_path}

    @standalone_app.route("/")
    def index():
        return redirect(url_for("subadmin.login"))

    return standalone_app


if __name__ == "__main__":
    standalone_app = create_standalone_app()
    standalone_app.run(
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
        port=int(os.getenv("SUBADMIN_PORT", "5001"))
    )
