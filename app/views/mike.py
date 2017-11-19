from flask import jsonify, render_template, session

from . import get_db, app


@app.route('/account')
def view_account():
    sql = 'SELECT * FROM User WHERE id = %s'
    with get_db().cursor() as cursor:
        if not session['logged_in']:
            return render_template('no_account.html')
        else:
            cursor.execute(sql, session['user_id'])
            user = cursor.fetchone()
            return render_template('account.html', user=user)


@app.route('/account/orders')
def order_history():
    if not session['logged_in']:
        return render_template('no_account.html')
    else:
        sql = 'SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID, P.name, SP.quantity, (P.price*SP.quantity) AS total ' \
                'FROM Shipment AS S, Product AS P, ShippedProduct AS SP ' \
                'WHERE S.shipmentID = SP.shipmentID AND SP.sku = P.sku AND S.userID = %s'
        with get_db().cursor() as cursor:
            cursor.execute('SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID '
                       'FROM Shipment AS S WHERE S.userID = %s', session['user_id'])
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
    if not session['logged_in']:
        return render_template('no_account.html')
    else:
        return render_template('cart.html')
