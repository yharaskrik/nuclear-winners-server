from flask import render_template, redirect, request

from app import requires_roles, user_login
from app.util import get_user_object
from . import app, get_db


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


@app.route('/admin/customers')
@requires_roles("admin")
def list_customers():
    sql = 'SELECT * FROM User'

    total_sold_sql = 'SELECT userID, SUM(quantity*price) AS total FROM Shipment JOIN ShippedProduct ON Shipment.shipmentID = ShippedProduct.shipmentID ' \
    'GROUP BY Shipment.userID'

    with get_db().cursor() as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.execute(total_sold_sql)
        total_sold = cursor.fetchall()
        totals = dict()
        for p in data:
            totals[p["id"]] = 0

        print(totals)

        for t in total_sold:
            totals[t["userID"]] = int(t["total"])

        print(totals)
        return render_template('list_customers.html', data=data, user=get_user_object(), totals=totals)
    return 'picnic'


@app.route('/admin/reports')
@requires_roles("admin")
def list_reports():
    sql = 'SELECT U.id, U.name, U.address, S.shipmentID, methodName, PaymentMethod.name AS payment, S.total ' \
          'FROM User AS U, Shipment AS S, ShippingMethod, PaymentMethod ' \
          'WHERE U.id = S.userID AND S.shippingMethodID = ShippingMethod.methodID AND S.paymentMethodID = PaymentMethod.methodID AND S.status = %s ORDER BY S.shipmentID'

    with get_db().cursor() as cursor:
        cursor.execute(sql, [0])
        shipments = cursor.fetchall()
        cursor.execute(sql, [1])
        finishedshipments = cursor.fetchall()
        total = 0
        orders = 0
        for order in shipments:
            orders += 1
            if order['total']:
                total += order['total']
        finishedtotal = 0
        finishedorders = 0
        for order in finishedshipments:
            finishedorders += 1
            if order['total']:
                finishedtotal += order['total']
        return render_template('list_reports.html', data=shipments, data2=finishedshipments, totalsum=total,
                               totalorders=orders, finishedsum=finishedtotal, finishedorders=finishedorders,
                               user=get_user_object())


@app.route('/admin/send/<int:shipid>/')
@requires_roles('admin')
def send_order(shipid):
    sql = 'UPDATE Shipment SET status = 1 WHERE shipmentID = %s'
    with get_db().cursor() as cursor:
        cursor.execute(sql, shipid)
        get_db().commit()
    return redirect(request.referrer)