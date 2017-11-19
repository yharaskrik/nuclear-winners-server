import io

import flask
from flask import request, render_template, jsonify, flash, url_for, redirect, session, send_file

from app import app, get_db

create_prod_sql_with_image = "INSERT INTO Product (name, description , price, weight, inventory, visible, image) VALUES (%s, %s, %s, %s, %s, %s, %s)"
create_prod_sql_no_image = "INSERT INTO Product (name, description , price, weight, inventory, visible) VALUES (%s, %s, %s, %s, %s, %s)"
update_prod_sql_no_image = "UPDATE Product SET name = %s, description=%s, price=%s, weight = %s, inventory = %s, visible = %s WHERE sku = %s"
update_prod_sql_with_image = "UPDATE Product SET name = %s, description=%s, price=%s, weight = %s, inventory = %s, visible = %s, image=%s WHERE sku = %s"
get_prod_sql = "SELECT sku, name, description, price, inventory, weight, visible FROM Product WHERE sku = %s"


@app.route("/product/<int:pid>")
def view_product(pid):
    """Displays a products"""
    try:
        with get_db().cursor() as cursor:
            cursor.execute(get_prod_sql, int(pid))
            product = cursor.fetchone()
            return render_template("product_details.html", product=product)
    except Exception as e:
        app.log_exception(e)
    return render_template("error.html", msg="Unable to display the product")


@app.route("/product/<int:sku>/edit", methods=['post', 'get'])
def edit_product(sku):
    """Prepares and edit product page with a get request by fetching the product details from the server"""

    # Verify the current user is an admin
    if "user_admin" not in session or not session["user_admin"]:
        return render_template("error.html", msg="You are not authorized to view this page")

    # Setup the edit product page with auto filled values
    if request.method == 'GET':
        with get_db().cursor() as cursor:
            cursor.execute(get_prod_sql, sku)
            result = cursor.fetchone()
            if not result:
                return render_template("error.html", msg="Unable to retrieve product details")
            result["showInStore"] = "1" if result["visible"] == 1 else ''
            return render_template("edit_product.html", data=result)

    # Validate and submit
    data = request.form
    args = prepare_product_insert_data(data)

    if not args:
        return render_template("edit_product.html", data=data)

    sql = update_prod_sql_no_image

    if request.files and 'image' in request.files:
        sql = update_prod_sql_with_image
        filename = request.files['image'].filename
        mime_type = request.files['image'].mimetype
        file = request.files['image'].stream.read()
        args.append(file)

    args.append(sku)

    try:
        with get_db().cursor() as cursor:
            cursor.execute(sql, args)
            flash("Updated product")
            return redirect(url_for("view_product", pid=sku))
    except Exception as e:
        print(e)
    flash("Unable to Edit product")
    return render_template("edit_product.html", data=data)


@app.route("/product/add", methods=['post', 'get'])
def add_product():
    # Verify the current user is an admin
    if not "user_admin" in session or not session["user_admin"]:
        return render_template("error.html", msg="You are not authorized to view this page")

    if request.method == 'GET':
        return render_template("add_product.html", data={})

    args = prepare_product_insert_data(request.form)

    if not args:
        return render_template("add_product.html", data=request.form)

    sql = create_prod_sql_no_image

    if request.files and 'image' in request.files:
        sql = create_prod_sql_with_image
        filename = request.files['image'].filename
        mime_type = request.files['image'].mimetype
        file = request.files['image'].stream.read()
        args.append(file)
    try:
        with get_db().cursor() as cursor:
            rows = cursor.execute(sql, args)
            if rows == 1:
                return redirect(url_for("view_product", pid=cursor.lastrowid))
    except Exception as e:
        print(e)
    flash("Unable to create product")
    return render_template("add_product.html", data=request.form)


@app.route("/product/<int:sku>/image.jpg")
def get_product_picture(sku):
    """Retrieves a product image from the database and server it as an image file"""
    sql = "SELECT image FROM Product WHERE sku = %s"
    with get_db().cursor() as cursor:
        cursor.execute(sql, sku)
        return send_file(io.BytesIO(cursor.fetchone()["image"]), mimetype="image/jpeg")


def product_visibility_from_checkbox(data):
    visible = 0
    if "showInStore" in data and data["showInStore"] == '1':
        visible = 1
    return visible


def prepare_product_insert_data(data):
    """Prepares an array of data to insert in the order:
    name
    description
    price
    weight
    inventory - set to 0 if not set
    visible

    Or will return False if the data is invalid.
    """

    valid = validate_product(data)

    inventory = 0
    if data['inventory']:
        inventory = int(data['inventory'])

    visible = product_visibility_from_checkbox(data)

    for key in data:
        print(key + ": " + str(data[key]))

    if not valid:
        return False

    args = []
    args.append(data['name'])
    args.append(data['description'])
    args.append(int(data['price']))
    args.append(float(data['weight']))
    args.append(inventory)
    args.append(visible)

    if app.debug:
        print(args)
    return args


def validate_product(data):
    """Validates an edit or added product and returns true or false.
    This checks if all of name, description, weight, and price are not null or empty.
    """
    valid = True
    # validate the form
    if not data['name']:
        flash("Product name is required")
        valid = False
    if not data['description']:
        flash("Description is required")
        valid = False
    if not data['weight']:
        flash("Weight is required")
        valid = False
    if not data['price']:
        flash("Price is required")
        valid = False
    return valid
