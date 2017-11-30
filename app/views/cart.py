from flask import render_template, session, request, redirect, flash, current_app
from pymysql import Error

from app.util import is_logged_in, get_cart_id, get_user_object
from . import get_db, app as app


@app.route('/cart/')
def cart():
    """Displays the user's cart

    If the user is not logged in then it displays the current session cart, if the user is logged in then it displays
    the cart from the database.
    """
    if not is_logged_in():
        return view_session_cart()
    else:
        return view_user_cart()


@app.route('/cart/add/<int:pid>/')
def add_to_cart(pid):
    """Adds a product to the cart.

    As there are two types of carts the actually function used depends if the user is logged in or not.
    """
    # If there is no quantity specified by the call, it defaults to one
    quantity = int(request.args.get("quantity", 1))

    # Get the current inventory for the product as it is needed for both calls.
    inventory = get_inventory_for_product(pid)

    # If the user is not logged in, the session cart gets updated or created
    if not is_logged_in():
        add_product_to_session_cart(pid, quantity, inventory)
    else:
        if add_product_to_user_cart(pid, quantity, inventory):
            flash("Added product to cart", "success")

    return redirect(request.referrer)


@app.route('/cart/delete/<int:pid>/')
def delete_from_cart(pid):
    """Deletes a product from the cart"""
    if not is_logged_in():
        delete_from_session_cart(pid)
        success = True
    else:
        success = delete_from_user_cart(pid)
    if success:
        flash('Removed from cart', "success")
    else:
        flash("Unable to remove the product from the cart", "error")
    return redirect(request.referrer)


@app.route('/cart/update/<int:pid>/')
def update_cart(pid):
    if 'quantity' not in request.args:
        flash('Quantity not specified', "error")
        return redirect(request.referrer)

    quantity = int(request.args['quantity'])

    if not checked_inventory(quantity, pid):
        flash("Not enough product in stock", "error")
        return redirect(request.referrer)

    if not is_logged_in():
        update_session_cart(pid, quantity)
        flash("Updated the quantity in the cart", "success")
    else:
        if update_user_cart(pid, quantity):
            flash("Updated the quantity in the cart", "success")
        else:
            flash("Unable to update the cart", "error")
    return redirect(request.referrer)


def view_user_cart():
    """Retrieves and displays the user's cart from the database"""
    # call method to display the cart, using the database data
    with get_db().cursor() as cursor:
        cart_id = get_cart_id()
        cursor.execute('SELECT P.sku, P.name, P.price, PC.quantity, (P.price * PC.quantity) AS total '
                       'FROM ProductInCart AS PC, Product AS P WHERE '
                       'PC.sku = P.sku AND PC.cartID = %s', cart_id)
        cart_products = cursor.fetchall()
        if not cart_products:
            return render_template('no_cart.html')
        else:
            subtotal = 0
            # add up the subtotal
            for item in cart_products:
                subtotal += item['total']
            return render_template('cart.html', cart=cart_products, subtotal=subtotal, user=get_user_object())


def view_session_cart():
    """Retrieves and displays the session cart data"""
    session_cart = get_session_cart()
    # call method to display the cart, using the session cart data
    if not session_cart:
        return render_template('no_cart.html')
    else:
        ids = session_cart.keys()
        sql = "SELECT sku, name, price FROM Product WHERE sku IN (%s)" % ','.join(["%s"] * len(ids))
        with get_db().cursor() as cursor:
            cursor.execute(sql, tuple(ids))
            cart_products = cursor.fetchall()
            subtotal = 0
            for item in cart_products:
                item['quantity'] = session_cart[str(item['sku'])]
                item['total'] = item['price'] * item['quantity']
                subtotal += item['total']
        return render_template('cart.html', cart=cart_products, subtotal=subtotal, user=get_user_object())


def add_product_to_session_cart(sku, quantity, inventory):
    """ Adds a product to the session cart.

    This method adds a product to the session cart by checking if there is already a key with the string of the sku in
    the session cart. If the key exists, then quantity is added to that value. Otherwise a new key is added as the string
    of the sku and this key is set to quantity.

    :param sku: The sku of the product to add to the cart
    :param quantity: The quantity to add to the cart
    :param inventory: The current inventory for this item
    :return: None
    """
    sku_s = str(sku)
    session_cart = get_session_cart()
    new_quantity = session_cart.get(sku_s, 0) + quantity

    if new_quantity > inventory:
        flash('No more product in stock', "error")
    else:
        session_cart[sku_s] = new_quantity
        flash("Added product to cart", "success")
    return


def add_product_to_user_cart(sku, quantity, inventory):
    """Adds a product to the user's database cart.

    This function checks if the product sku is already in the user's cart. If it is then it adds the new amount as
    long as it doesn't exceed the current inventory. If the product is not already in the cart then it adds the product
    to the cart as long as it doesn't exceed the current inventory for that product.

    :param sku: The sku for the project to add to the cart
    :param quantity: The quantity to add to the cart.
    :param inventory: The current inventory of that product in the database
    :return:  None
    """
    cart_id = get_cart_id()
    # Check if they already have the item in their cart
    try:
        with get_db().cursor() as cursor:
            cursor.execute('SELECT PC.sku, PC.quantity FROM ProductInCart AS PC WHERE PC.cartID = %s AND sku = %s',
                           (cart_id, sku))
            product_in_cart = cursor.fetchone()

            # If they don't have the item in their cart, add it
            if not product_in_cart:
                if quantity > inventory:
                    flash('Not enough product in stock', "error")
                    return False

                cursor.execute('INSERT INTO ProductInCart(cartID, sku, quantity) '
                               'VALUES (%s, %s, %s);',
                               (cart_id, sku, quantity))

            # If they do have the item in their cart, update the amount
            else:
                new_quantity = quantity + product_in_cart["quantity"]
                if new_quantity > inventory:
                    flash('Not enough product in stock', "error")
                    return
                cursor.execute('UPDATE ProductInCart SET quantity = quantity + %s '
                               'WHERE cartID = %s AND sku = %s',
                               (quantity, cart_id, sku))
            get_db().commit()
            return True

    except Error as e:
        current_app.logger.error(e)
        flash("Unable to add product to cart", "error")
        return False


def get_inventory_for_product(sku):
    """Gets and returns the inventory for a product.

    Defaults to 0 if the product was not in the inventory.

    :arg sku: The product sku to get the inventory for.

    :returns The inventory of the product or 0 if the product was not found.
    """
    try:
        with get_db().cursor() as cursor:
            cursor.execute('SELECT inventory FROM Product WHERE sku = %s', sku)
            row = cursor.fetchone()
            if row:
                return row["inventory"]
            return 0
    except Exception as e:
        current_app.logger.error(e)
        return 0


def delete_from_user_cart(sku):
    """Deletes a product from the user's database cart

    :returns True if the delete succeeded, False if it failed.
    """
    cart_id = get_cart_id()
    try:
        with get_db().cursor() as cursor:
            cursor.execute('DELETE FROM ProductInCart '
                           'WHERE sku = %s AND cartID = %s', (sku, cart_id))
            get_db().commit()
            return True
    except Exception as e:
        current_app.logger.error(e)
        return False


def delete_from_session_cart(sku):
    """Deletes a product from the session cart by popping the sku from the cart"""
    get_session_cart().pop(str(sku), None)


def checked_inventory(quantity, sku):
    """Checks if the current inventory for a product is less than the desired quantity

    :param quantity: The quantity to check
    :param sku: The product id to check the inventory against

    :returns True if the inventory is sufficient, False if the quantity is too large.
    """
    inventory = get_inventory_for_product(sku)
    return inventory > quantity


def update_user_cart(sku, quantity):
    """Updates the quantity of a product in the user's cart.

    This function simply updates the product in a user's cart. This does not check if the product is already in the cart.

    :param sku: The sku of the product to update
    :param quantity: The new quantity of the product in the cart. This should not be more then the current inventory.
    :return: True if the update succeeded, False otherwise
    """
    cart_id = get_cart_id()
    try:
        with get_db().cursor() as cursor:
            cursor.execute('SELECT quantity FROM ProductInCart WHERE cartID = %s AND sku = %s', (cart_id, sku))
            product = cursor.fetchone()

            # Add instead
            if not product:
                return add_product_to_user_cart(sku, quantity, get_inventory_for_product(sku))

            if product["quantity"] == quantity:
                # Already what we need
                return True

            cursor.execute('UPDATE ProductInCart SET quantity = %s '
                           'WHERE sku = %s AND cartID = %s',
                           (quantity, sku, cart_id))
            get_db().commit()
            return True
    except Error as e:
        current_app.logger.error(e)
        return False


def update_session_cart(sku, quantity):
    """Updates the quantity of a product in the cart.

    This directly sets the inventory in the session cart by using the string of the sku as a key. This assumes that the
    inventory condition has already been checked.

    :param sku: The product to update the quantity for
    :param quantity: The quantity to set the product to
    """
    get_session_cart()[str(sku)] = quantity
    return


def validate_inventory(cart_id, sku=None, qty=None):
    sql = 'SELECT quantity, inventory FROM ProductInCart C, Product P WHERE C.sku = P.sku AND C.cartID = %s'
    with get_db().cursor() as cursor:
        if sku is None:
            cursor.execute(sql, cart_id)
        else:
            sql += ' AND P.sku = %s'
            cursor.execute(sql, (cart_id, sku))
        products = cursor.fetchall()
        for product in products:
            if qty is None:
                if product['quantity'] > product['inventory']:
                    return False
            else:
                if qty > product['inventory']:
                    return False
    return True


def get_session_cart():
    """ Retrieves the session cart, create one if it does not exist"""
    if "cart" not in session:
        session["cart"] = {}
    return session["cart"]


def transfer_session_cart_to_user_cart():
    """Check if the user has a session cart, if so transfers the products into the user's database cart"""
    session_cart = get_session_cart()

    if not session_cart:
        current_app.logger.debug("No session cart to transfer")
        return

    for sku in session_cart:
        if not sku == "total":
            add_product_to_user_cart(sku, session_cart[sku], get_inventory_for_product(sku))

    # Remove the cart
    session.pop("cart")
    current_app.logger.debug("Transferred session cart")
