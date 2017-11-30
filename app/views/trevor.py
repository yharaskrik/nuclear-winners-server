# @app.route('/get/Product/<type:param>')
# def name(param)

from flask import request, render_template, flash, url_for, current_app
from werkzeug.security import generate_password_hash

from app.util import get_user_object
from . import get_db, app, requires_roles, redirect


# allows users to create an account
@app.route('/user/register', methods=['post', 'get'])
def register_user():
    if request.method == 'GET':
        return render_template("register_user.html", data={})

    data = request.form
    username = data['username']

    if not data.get("password"):
        flash("Passwords cannot be empty", "error")
        return render_template('register_user.html', data=data)

    # validates entered information
    if data['password'] != data['confirmpassword']:
        flash("Password does not match.", "error")
        return render_template('register_user.html', data=data)

    if not data['name'] or not data['username'] or not data['password'] or not data['address']:
        flash("All fields are required.", "error")
        return render_template('register_user.html', data=data)

    sql = 'INSERT INTO User(name,pass,address,accountType,username) VALUES(%s,%s,%s,0,%s)'

    try:
        with get_db().cursor() as cursor:
            cursor.execute(sql, (data['name'],
                                 generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=8),
                                 data['address'], data['username']))

            if data.get('robot', "") == 'robot':
                sql2 = 'SELECT * FROM User WHERE username = %s'
                cursor.execute(sql2, username)
                uid = cursor.fetchone()
                sql3 = 'INSERT INTO UserMutation(userID, mutationID) VALUES(%s,1)'
                cursor.execute(sql3, uid['id'])

            # Create a cart for this user
            cursor.execute('INSERT INTO Cart(userID) VALUES (%s)', cursor.lastrowid)
            get_db().commit()
        flash("Account created", "success")
        return redirect(url_for("login"))
    except Exception as e:
        current_app.logger.error(e)
        flash('This username already exists', "error")
        return render_template('register_user.html', data=data)


# allows admins to see a list of all customers
@app.route('/admin/customers')
@requires_roles("admin")
def list_customers():
    sql = 'SELECT * FROM User WHERE accountType = 0'
    with get_db().cursor() as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()
        return render_template('list_customers.html', data=data, user=get_user_object())
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
