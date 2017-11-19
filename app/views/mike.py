from flask import jsonify, render_template

from . import get_db, app


@app.route('/account/<int:cid>')
def view_account(cid):
    sql = 'SELECT * FROM User WHERE id = %s'
    with get_db().cursor() as cursor:
        cursor.execute(sql, [cid])
        user = cursor.fetchone()
        if not user:
            return render_template('no_account.html')
        else:
            return render_template('account.html', user=user)


@app.route('/account/<int:cid>/orders')
def order_history(cid):
    sql = 'SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID, P.name, SP.quantity, (P.price*SP.quantity) AS total ' \
          'FROM Shipment AS S, Product AS P, ShippedProduct AS SP ' \
          'WHERE S.shipmentID = SP.shipmentID AND SP.sku = P.sku AND S.userID = %s'
    with get_db().cursor() as cursor:
        cursor.execute('SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID '
                       'FROM Shipment AS S WHERE S.userID = %s', cid)
        orders = cursor.fetchall()
        for order in orders:
            order['subtotal'] = 0
            cursor.execute('SELECT P.name, SP.quantity, (P.price*SP.quantity) AS total '
                           'FROM Product AS P, ShippedProduct AS SP '
                           'WHERE SP.sku = P.sku AND SP.shipmentID = %s', order['shipmentID'])
            order['products'] = cursor.fetchall()
            for product in order['products']:
                order['subtotal'] += product['total']
        return render_template('order_history.html', orders=orders)


@app.route('/cart')
def cart():
