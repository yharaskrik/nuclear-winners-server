from flask import session, render_template, request, flash, current_app, url_for, redirect
from pymysql import Error
from werkzeug.security import generate_password_hash

from app.user_login import requires_roles
from . import get_db, app
from .mutations import get_user_mutations, get_mutations, set_mutations
from .util import get_user_id, get_user_object

update_account_sql = "UPDATE User SET address = %s, faction = %s WHERE id = %s"


@app.route('/account/')
@requires_roles("user")
def view_account():
    # getting user information
    sql = 'SELECT * FROM User WHERE id = %s'
    with get_db().cursor() as cursor:
        cursor.execute(sql, session['user_id'])
        user = cursor.fetchone()

        cursor.execute(
            'SELECT * FROM UserMutation INNER JOIN Mutation ON UserMutation.mutationID = Mutation.id WHERE userID = %s',
            get_user_id())

        mutatiions = cursor.fetchall()
        return render_template('account.html', user=user, mutations=mutatiions)


@app.route('/account/orders/')
@requires_roles("user")
def order_history():
    # get information on the orderids related to the user
    with get_db().cursor() as cursor:
        cursor.execute('SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID, S.total, PM.name AS paymentMethodName, '
                       'ShippingMethod.methodName AS shippingMethodName, ShippingMethod.price AS shippingPrice '
                       'FROM Shipment AS S JOIN ShippingMethod ON S.shippingMethodID = ShippingMethod.methodID'
                       ' JOIN PaymentMethod AS PM ON S.paymentMethodID = PM.methodID WHERE S.userID = %s', session['user_id'])
        orders = cursor.fetchall()
        # loop through, getting all the products in each of the orders
        for order in orders:
            cursor.execute('SELECT P.name, SP.quantity, (P.price*SP.quantity) AS total '
                           'FROM Product AS P, ShippedProduct AS SP '
                           'WHERE SP.sku = P.sku AND SP.shipmentID = %s', order['shipmentID'])
            order['products'] = cursor.fetchall()
            # add the total prices together to make a subtotal
            total = 0
            for p in order['products']:
                total += p['total']
            order['subtotal'] = total
        return render_template('order_history.html', orders=orders, user=get_user_object())


@app.route('/account/edit/', methods=['GET', 'POST'])
@requires_roles("user")
def edit_account():
    # getting user information
    sql = 'SELECT * FROM User WHERE id = %s'
    user_mutations = get_user_mutations()
    mutations = get_mutations()
    user = get_user_object()
    if request.method == 'GET':
        return render_template("edit_user.html", data=user, user_mutations=user_mutations, mutations=mutations)

    address = request.form.get("address")
    faction = request.form.get("address")
    robot = request.form.get("robot", "")
    mutations = request.form.getlist("mutations")

    if not address:
        flash("Address is required", "error")
        return render_template("edit_user.html", data=user, user_mutations=user_mutations, mutations=mutations)

    if robot == "robot":
        mutations.append("1")

    try:
        with get_db().cursor() as cursor:
            # Update account
            cursor.execute(update_account_sql, (address, faction, get_user_id()))

            # update mutations
            set_mutations(get_user_id(), mutations)

            get_db().commit()

    except Error as e:
        flash("Unable to update account details", "error")
        current_app.logger.error(e)
    return redirect(url_for("view_account"))


@app.route('/user/register', methods=['post', 'get'])
def register_user():
    mutations = get_mutations()

    if request.method == 'GET':
        return render_template("register_user.html", data=dict(), mutations=mutations)

    data = request.form
    username = data['username']

    current_app.logger.debug(data)

    if not data.get("password"):
        flash("Passwords cannot be empty", "error")
        return render_template('register_user.html', data=data, mutations=mutations)

    # validates entered information
    if data['password'] != data['confirmpassword']:
        flash("Password does not match.", "error")
        return render_template('register_user.html', data=data, mutations=mutations)

    if not data['name'] or not data['username'] or not data['password'] or not data['address']:
        flash("All fields are required.", "error")
        return render_template('register_user.html', data=data, mutations=mutations)

    sql = 'INSERT INTO User(name,pass,address,accountType,username, faction) VALUES(%s,%s,%s,0,%s, %s)'

    try:
        with get_db().cursor() as cursor:
            cursor.execute(sql, (data['name'],
                                 generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=8),
                                 data['address'], data['username'], data.get("faction")))
            user_id = cursor.lastrowid
            print("Staring mutations")
            mutation_ids = request.form.getlist('mutations')
            if data.get('robot', "") == 'robot':
                mutation_ids.append("1")


            if mutation_ids:
                print("Calling mutations")
                set_mutations(user_id, mutation_ids)

            # Create a cart for this user
            print("Creating cart")
            cursor.execute('INSERT INTO Cart(userID) VALUES (%s)', user_id)

            print("Committing user account")
            get_db().commit()

        flash("Account created", "success")
        return redirect(url_for("login"))
    except Exception as e:
        current_app.logger.error(e)
        flash('Unable to create your account. Please try again with a different user name', "error")
        return render_template('register_user.html', data=data, mutations=mutations)


