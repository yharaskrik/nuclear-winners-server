from flask import render_template, request, flash, url_for, redirect

from config import TAX_RATE
from . import app
from . import get_db
from .payment_methods import get_payment_methods
from .shipping import get_shipping_methods, get_shipping_method_price
from .util import get_user_id
from .views.user_login import requires_roles


@app.route("/order/", methods=['GET'])
@requires_roles("user")
def order_options(data=None):
    if data is None:
        data = {"shippingMethod": "1"}
    shipping = get_shipping_methods()
    payment = get_payment_methods()
    cart = get_cart()

    total = 0
    total_weight = 0

    for item in cart:
        total += item["quantity"] * item["price"]
        weight = item["weight"]
        if weight:
            total_weight += item["quantity"] * weight

    return render_template("order.html", shipping=shipping, payment=payment, cart=cart, total=total,
                           weight=total_weight, data=data, tax=TAX_RATE)


@app.route("/order/", methods=['POST'])
@requires_roles("user")
def place_order():
    # Ensure everything is set.
    data = request.form
    print(str(data))
    valid = True
    if "paymentMethod" not in data or not data["paymentMethod"]:
        flash("Payment method is required")
        valid = False
    if "shippingMethod" not in data or not data["shippingMethod"]:
        valid = False
        flash("Shipping method is required")

    cart = get_cart()

    if not cart:
        valid = False
        flash("Nothing in your cart")

    if not valid:
        # Return the form with entered values
        return order_options(data)

    cart_id = cart[0]["cartID"]

    # Validate Product supply
    # TODO Add trevors validate inventory
    orderId = 0
    try:
        with get_db().cursor() as cursor:
            # Create the order
            cursor.execute(insert_order, (get_user_id(), data["shippingMethod"], data["paymentMethod"]))
            orderId = cursor.lastrowid

            total = 0
            for item in cart:
                # Add item to ordered product
                cursor.execute(insert_ordered_product, (orderId, item["sku"], item["quantity"], item["price"]))
                # Update inventory
                cursor.execute(update_inventory, (item["quantity"], item["sku"]))
                total += item['quantity'] * item["price"]

            shippingPrice = get_shipping_method_price(data["shippingMethod"])
            total += shippingPrice
            tax = int(round(total * TAX_RATE))
            cursor.execute(update_order_total, (total + tax, orderId))
            cursor.execute(clear_cart, cart_id)
            get_db().commit()

        flash("Order place successfully")

    except Exception as e:
        app.logger.error(e)
        flash("Unable to place order. Please try again")
        return order_options(data)
    return redirect(url_for("single_order", shipid=orderId))


insert_order = "INSERT INTO Shipment (status, userID, shippingMethodID, paymentMethodID, total) " \
               "VALUES (0, %s, %s, %s, 0)"

update_order_total = "UPDATE Shipment " \
                     "SET total = %s " \
                     "WHERE shipmentID = %s"

insert_ordered_product = "INSERT INTO ShippedProduct(shipmentID, sku, quantity, price) VALUES (%s, %s, %s, %s)"
clear_cart = "DELETE FROM ProductInCart WHERE cartID = %s"
update_inventory = "UPDATE Product SET inventory = inventory - %s WHERE sku = %s"

cart_sql = "SELECT PC.cartID AS cartID, PC.sku AS sku, PC.quantity AS quantity, P.name AS name, P.price AS price, P.weight AS weight, price * quantity AS subtotal " \
           "FROM Cart C JOIN ProductInCart PC ON C.cartID = PC.cartID JOIN Product P ON PC.sku = P.sku " \
           "WHERE C.userID = %s"


def get_cart():
    user_id = get_user_id()
    if user_id:
        with get_db().cursor() as cursor:
            cursor.execute(cart_sql, user_id)
            return cursor.fetchall()
    return


@app.route('/admin/reports/order/<int:shipid>')
@requires_roles("user")
def single_order(shipid):
    sql = 'SELECT Shipment.total AS shipmentTotal, P.sku, P.name, S.quantity, S.price * S.quantity AS total, User.name AS user ' \
          'FROM User, Product AS P, ShippedProduct AS S, Shipment ' \
          'WHERE User.id = Shipment.userID AND Shipment.shipmentID = S.shipmentID AND P.sku = S.sku AND S.shipmentID = %s'
    with get_db().cursor() as cursor:
        cursor.execute(sql, [shipid])
        data = cursor.fetchall()
        print(str(data))
        sum = data[0]["shipmentTotal"]
        return render_template('single_order.html', data=data, sum=sum, id=shipid)
