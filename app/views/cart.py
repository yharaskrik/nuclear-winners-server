from flask import render_template, session, request, redirect, flash

from . import get_db, app, requires_roles


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
    with get_db().cursor() as cursor:
        cursor.execute('SELECT inventory FROM Product WHERE sku = %s',pid)
        u = cursor.fetchone()
    # If there is no quantity specified by the call, it defaults to one
    quantity = 1
    if quantity in request.args:
        quantity = int(request.args['quantity'])
    # If the user is not logged in, the session cart gets updated or created
    if not session['logged_in']:
        if 'cart' not in session:
            session['cart'] = {}
        if str(pid) not in session['cart']:
            if quantity > u['inventory']:
                flash('No more product in stock')
                return redirect(request.referrer)
            session['cart'][str(pid)] = quantity
        else:
            if session['cart'][str(pid)] + quantity > u['inventory']:
                flash('No more product in stock')
                return redirect(request.referrer)
            session['cart'][str(pid)] += quantity
    else:
        # Check if they already have the item in their cart
        with get_db().cursor() as cursor:
            print(session['user_id'])
            cursor.execute('SELECT sku , C.cartID FROM ProductInCart AS PC, Cart AS C '
                           'WHERE C.cartID = PC.cartID AND C.userID = %s AND sku = %s', (session['user_id'], pid))
            products_in_cart = cursor.fetchall()
            print(str(products_in_cart))
            # If they don't have the item in their cart, add it
            if not products_in_cart:
                if quantity > u['inventory']:
                    flash('No more product in stock')
                    return redirect(request.referrer)
                i = cursor.execute('INSERT INTO ProductInCart(cartID, sku, quantity) '
                                   'VALUES ((SELECT cartID FROM Cart WHERE userID = %s), %s, %s);',
                                   (session['user_id'], pid, quantity))
                print(cursor._last_executed)
                print("Rows updated: " + str(i))
            # If they do have the item in their cart, update the amount
            else:
                if not validate_inventory(products_in_cart['cartId'],pid,quantity):
                    flash('No more product in stock')
                    return redirect(request.referrer)
                cursor.execute('UPDATE ProductInCart SET quantity = quantity + %s '
                               'WHERE cartID = (SELECT cartID FROM Cart WHERE userID = %s) AND sku = %s',
                               (quantity, session['user_id'], pid))
            get_db().commit()
    flash('Added to cart')
    return redirect(request.referrer)


@app.route('/cart/delete/<int:pid>/')
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


@app.route('/cart/update/<int:pid>/')
def update_cart(pid):
    if 'quantity' not in request.args:
        flash('Quantity not specified')
        return redirect(request.referrer)

    quantity = int(request.args['quantity'])
    if not session['logged_in']:
        with get_db().cursor() as cursor:
            cursor.execute('SELECT inventory FROM Product WHERE sku = %s', pid)
            u = cursor.fetchone()
            if quantity > u['inventory']:
                flash('No more product in stock')
                return redirect(request.referrer)
            session['cart'][str(pid)] = quantity
            flash('Updated')
        return redirect(request.referrer)
    else:
        with get_db().cursor() as cursor:
            cursor.execute('SELECT cartID FROM Cart WHERE userID = %s', (session['user_id']))
            u = cursor.fetchone()
            if not validate_inventory(u['cartID'], pid, quantity):
                flash('No more product in stock')
                return redirect(request.referrer)
            cursor.execute('UPDATE ProductInCart SET quantity = %s '
                           'WHERE sku = %s AND cartID = (SELECT cartID FROM Cart WHERE userID = %s)',
                           (quantity, pid, session['user_id']))
            get_db().commit()
            flash('Updated')
            return redirect(request.referrer)


def validate_inventory(cartId, sku=None, qty=None):
    sql = 'SELECT quantity, inventory FROM ProductInCart C, Product P WHERE C.sku = P.sku AND C.cartID = %s'
    with get_db().cursor() as cursor:
        if sku is None:
            cursor.execute(sql, cartId)
        else:
            sql += ' AND P.sku = %s'
            cursor.execute(sql, (cartId, sku))
        products = cursor.fetchall()
        for product in products:
            if qty is None:
                if product['quantity'] > product['inventory']:
                    return False
            else:
                if qty > product['inventory']:
                    return False
    return True
