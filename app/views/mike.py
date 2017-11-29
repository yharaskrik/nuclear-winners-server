from flask import jsonify, render_template, session
from app.util import is_logged_in
from .user_login import requires_roles
from . import get_db, app


@app.route('/account')
@requires_roles('user')
def view_account():
    # getting user information
    sql = 'SELECT * FROM User WHERE id = %s'
    with get_db().cursor() as cursor:
        # if there is no user information from the session, go to no account page
        if not session['logged_in']:
            return render_template('no_account.html')
        # if there is user information, go to the account page
        else:
            cursor.execute(sql, session['user_id'])
            user = cursor.fetchone()

            cursor.execute(
                'SELECT * FROM UserMutation INNER JOIN Mutation ON UserMutation.mutationID = Mutation.id WHERE userID = %s',
                session['user_id'])
            mutatiions = cursor.fetchall()
            for mutation in mutatiions:
                print(mutation)
            print(user)
            return render_template('account.html', user=user, mutations=mutatiions)


@app.route('/account/orders')
@requires_roles('user')
def order_history():
    # otherwise find information on user's orders
    # get information on the orderids related to the user
    with get_db().cursor() as cursor:
        cursor.execute(
            'SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID, S.total, SM.methodName, PM.name '
            'FROM Shipment AS S, ShippingMethod AS SM, PaymentMethod AS PM '
            'WHERE S.shippingMethodID = SM.methodID AND PM.methodID = S.paymentMEthodID AND S.userID = %s',
            session['user_id'])
        orders = cursor.fetchall()
        # loop through, getting all the products in each of the orders
        for order in orders:
            cursor.execute('SELECT P.name, SP.quantity '
                           'FROM Product AS P, ShippedProduct AS SP '
                           'WHERE SP.sku = P.sku AND SP.shipmentID = %s', order['shipmentID'])
            order['products'] = cursor.fetchall()
            # add the total prices together to make a subtotal

        return render_template('order_history.html', orders=orders)


@app.route('/account/edit')
@requires_roles('user')
def account_edit():
    with get_db().cursor() as cursor:
        pass
