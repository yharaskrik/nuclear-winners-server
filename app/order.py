from flask import render_template

from . import app
from . import get_db
from .payment_methods import get_payment_methods
from .shipping import get_shipping_methods
from .util import get_logged_in_user_id
from .views.user_login import requires_roles


@app.route("/order/", methods=['GET'])
@requires_roles("user")
def order_options():
    shipping = get_shipping_methods()
    payment = get_payment_methods()
    cart = get_cart()
    return render_template("order.html", shipping=shipping, payment=payment, cart=cart)


cart_sql = "SELECT PC.sku AS sku, PC.quantity AS quantity, P.name AS name, P.price AS price, price * quantity AS subtotal " \
           "FROM Cart C JOIN ProductInCart PC ON C.cartID = PC.cartID JOIN Product P ON PC.sku = P.sku " \
           "WHERE C.userID = %s"


def get_cart():
    user_id = get_logged_in_user_id()
    if user_id:
        with get_db().cursor() as cursor:
            cursor.execute(cart_sql, user_id)
            return cursor.fetchall()
    return
