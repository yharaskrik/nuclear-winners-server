# @app.route('/get/Product/<type:param>')
# def name(param)
from flask import jsonify, request, render_template, session
from . import get_db, app


#allows users to create an account
@app.route('/user/register', methods=['post','get'])
def register_user():
    if request.method == 'GET':
        return render_template("register_user.html",data={})
    data = request.form
    #validates entered information
    if data['username'] != data['confirmusername']:
        return render_template('register_user.html',data=data,errormsg='Username does not match.')
    if  data['password'] != data['confirmpassword']:
        return render_template('register_user.html',data=data,errormsg='Password does not match.')
    if not data['name'] or not data['username'] or not data['password'] or not data['address']:
        return render_template('register_user.html', data=data,errormsg='All fields are required.')
    sql = 'INSERT INTO User(name,pass,address,accountType,username) VALUES(%s,%s,%s,0,%s)'
    try:
        with get_db().cursor() as cursor:
            cursor.execute(sql,[data['name'],data['password'],data['address'],data['username']])
            if not 'cart' in session:
                cursor.execute('INSERT INTO Cart(userID) VALUES (%s)', cursor.lastrowid)
        return render_template('login.html')
        #return redirect(url_for('/login'))
    except Exception as e:
        print(e)
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

