from flask import render_template

from app.util import get_user_object
from . import app, get_db
from .views import user_login


@app.route("/admin")
@user_login.requires_roles("admin")
def admin():
    """Shows the admin page if the user is logged in and an admin"""
    return render_template("admin.html", user=get_user_object())


@app.route("/admin/products/")
@user_login.requires_roles("admin")
def admin_list_products():
    sql = "SELECT Product.name, sku, visible, weight, inventory, price, description, Category.name AS cat_name " \
          "FROM Product JOIN Category ON Product.category = Category.id"
    products = []
    with get_db().cursor() as cursor:
        cursor.execute(sql)
        products = cursor.fetchall()
    return render_template("admin_product_list.html", products=products)
