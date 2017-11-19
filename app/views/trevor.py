# @app.route('/get/Product/<type:param>')
# def name(param)
from flask import jsonify, request, render_template
from . import get_db, app


#allows users to create an account
@app.route('/user/register', methods=['post','get'])
def register_user():
    if request.method == 'GET':
        return render_template("register_user.html",data={})
    data = request.form
    #validates entered information
    if  data['password'] != data['confirmpassword']:
        return render_template('register_user.html',data=data,errormsg='Password does not match.')
    if not data['name'] or not data['username'] or not data['password'] or not data['address']:
        return render_template('register_user.html', data=data,errormsg='All fields are required.')
    sql = 'INSERT INTO User(name,pass,address,accountType,username) VALUES(%s,%s,%s,0,%s)'
    try:
        with get_db().cursor() as cursor:
            cursor.execute(sql,[data['name'],data['password'],data['address'],data['username']])
        return 'success'
        #return redirect(url_for('/login'))
    except Exception:
        return render_template('register_user.html',data=data,errormsg='This username already exists')

#allows admins to see a list of all customers
@app.route('/admin/customers')
def list_customers():
    sql = 'SELECT * FROM User WHERE accountType = 0'
    with get_db().cursor() as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()
        return render_template('list_customers.html', data=data)
    return 'picnic'

@app.route('/admin/reports')
def list_reports():
    sql = 'SELECT U.id, U.name, U.address, S.shipmentID, methodName, PaymentMethod.name AS payment, S.total '\
    'FROM User AS U, Shipment AS S, ShippingMethod, PaymentMethod '\
    'WHERE U.id = S.userID AND S.shippingMethodID = ShippingMethod.methodID AND S.paymentMethodID = PaymentMethod.methodID AND S.status = %s'


    with get_db().cursor() as cursor:
        cursor.execute(sql,[1])
        shipments = cursor.fetchall()
        cursor.execute(sql,[2])
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
        return render_template('list_reports.html', data=shipments,data2=finishedshipments,totalsum=total,totalorders=orders,finishedsum=finishedtotal,finishedorders=finishedorders)

@app.route('/admin/reports/order/<int:shipid>')
def single_order(shipid):
    sql = 'SELECT P.sku, P.name, S.quantity, SUM(P.price * S.quantity) AS total, User.name AS user '\
    'FROM User, Product AS P, ShippedProduct AS S, Shipment '\
    'WHERE User.id = Shipment.userID AND Shipment.shipmentID = S.shipmentID AND P.sku = S.sku AND S.shipmentID = %s'
    with get_db().cursor() as cursor:
        cursor.execute(sql,[shipid])
        data = cursor.fetchall()
        sum = 0
        for product in data:
            sum += product['total']
        return render_template('single_order.html', data=data,sum=sum,id=shipid)



