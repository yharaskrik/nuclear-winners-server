from flask import jsonify, render_template, session, request, redirect, flash

from . import get_db, app


@app.route('/cart')
def cart():
    if not session['logged_in']:
        if 'cart' not in session:
            session['cart'] = {}
        # call method to display the cart, using the session cart data
        if not session['cart']:
            return render_template('no_cart.html')
        else:
            ids = session['cart'].keys()
            sql = "SELECT sku, name, price FROM Product WHERE sku IN (%s)" % ','.join(["%s"] * len(ids))
            with get_db().cursor() as cursor:
                cursor.execute(sql, tuple(ids))
                cart = cursor.fetchall()
                subtotal = 0
                for item in cart:
                    item['quantity'] = session['cart'][str(item['sku'])]
                    item['total'] = item['price'] * item['quantity']
                    subtotal += item['total']
        return render_template('cart.html', cart=cart, subtotal=subtotal)
    else:
        # call method to display the cart, using the database data
        with get_db().cursor() as cursor:
            cursor.execute('SELECT cartID FROM Cart WHERE Cart.userID = %s', session['user_id'])
            cart_id = cursor.fetchone()['cartID']
            cursor.execute('SELECT P.sku, P.name, P.price, PC.quantity, (P.price * PC.quantity) AS total '
                           'FROM ProductInCart AS PC, Product AS P WHERE '
                           'PC.sku = P.sku AND PC.cartID = %s', cart_id)
            cart = cursor.fetchall()
            if not cart:
                return render_template('no_cart.html')
            else:
                subtotal = 0
                # add up the subtotal
                for item in cart:
                    subtotal += item['total']
                return render_template('cart.html', cart=cart, subtotal=subtotal)


@app.route('/cart/add/<int:pid>/')
def add_to_cart(pid):
    # If there is no quantity specified by the call, it defaults to one
    quantity = 1
    if quantity in request.args:
        quantity = int(request.args['quantity'])
    # If the user is not logged in, the session cart gets updated or created
    if not session['logged_in']:
        if 'cart' not in session:
            session['cart'] = {}
        if str(pid) not in session['cart']:
            session['cart'][str(pid)] = quantity
        else:
            session['cart'][str(pid)] += quantity
    else:
        # Check if they already have the item in their cart
        with get_db().cursor() as cursor:
            cursor.execute('SELECT sku FROM ProductInCart AS PC, Cart AS C '
                           'WHERE C.cartID = PC.cartID AND C.userID = %s AND sku = %s', (session['user_id'], pid))
            products_in_cart = cursor.fetchall()
            # If they don't have the item in their cart, add it
            if not products_in_cart:
                cursor.execute('INSERT INTO ProductInCart(cartID, sku, quantity) '
                               'VALUES ((SELECT cartID FROM Cart WHERE userID = %s), %s, %s)',
                               (session['user_id'], pid, quantity))
            # If they do have the item in their cart, update the amount
            else:
                cursor.execute('UPDATE ProductInCart SET quantity = quantity + %s '
                               'WHERE cartID = (SELECT cartID FROM Cart WHERE userID = %s) AND sku = %s',
                               (quantity, session['user_id'], pid))
            get_db().commit()
    flash('Added to cart')
    return redirect(request.referrer)


@app.route('/cart/delete/<int:pid>')
def delete_from_cart(pid):
    if not session['logged_in']:
        session['cart'].pop(str(pid), None)
    else:
        with get_db().cursor() as cursor:
            cursor.execute('DELETE FROM ProductInCart '
                           'WHERE sku = %s AND cartID = (SELECT cartID FROM Cart WHERE userID = %s)',
                           (pid, session['user_id']))
            get_db().commit()
    flash('Removed from cart')
    return redirect(request.referrer)
