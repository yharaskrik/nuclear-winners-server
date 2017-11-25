from flask import jsonify, render_template, session

from . import get_db, app


@app.route('/cart')
def cart():
    if not session['logged_in']:
        if not session['cart']:
            return render_template('no_account.html')

            #call method to display the cart, using the session cart data
    else:
        #call method to display the cart, using the database data
        with get_db().cursor() as cursor:
            cursor.execute('SELECT CartID FROM Cart WHERE Cart.UserID = %s', session['user_id'])
            cart_id = cursor.fetchone()
            cursor.execute('SELECT * FROM ProductInCart WHERE ProductInCart.cartID = %s', cart_id)
            cart = cursor.fetchall()
        return render_template('cart.html', cart = cart)