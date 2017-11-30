from flask import session, render_template, request, flash, current_app, url_for, redirect
from pymysql import Error

from app import get_db, requires_roles, get_user_object
from app.mutations import get_user_mutations, get_mutations, set_mutations
from app.views import app
from .util import get_user_id

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
        for mutation in mutatiions:
            print(mutation)
        return render_template('account.html', user=user, mutations=mutatiions)


@app.route('/account/orders/')
@requires_roles("user")
def order_history():
    # get information on the orderids related to the user
    with get_db().cursor() as cursor:
        cursor.execute('SELECT S.shipmentID, S.status, S.shippingMethodID, S.paymentMethodID, S.total '
                       'FROM Shipment AS S WHERE S.userID = %s', session['user_id'])
        orders = cursor.fetchall()
        # loop through, getting all the products in each of the orders
        for order in orders:
            cursor.execute('SELECT P.name, SP.quantity, (P.price*SP.quantity) AS total '
                           'FROM Product AS P, ShippedProduct AS SP '
                           'WHERE SP.sku = P.sku AND SP.shipmentID = %s', order['shipmentID'])
            order['products'] = cursor.fetchall()
            # add the total prices together to make a subtotal
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
