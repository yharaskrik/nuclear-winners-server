import io

from flask import request, render_template, flash, url_for, redirect, send_file, current_app
from pymysql import Error

from app import app, get_db
from app.user_login import requires_roles
from app.util import get_user_object
from .categories import fetch_categories

create_prod_sql_with_image = "INSERT INTO Product (name, description , price, weight, inventory, visible, category, image) " \
                             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
create_prod_sql_no_image = "INSERT INTO Product (name, description , price, weight, inventory, visible, category) VALUES (%s, %s, %s, %s, %s, %s, %s)"
update_prod_sql_no_image = "UPDATE Product SET name = %s, description=%s, price=%s, weight = %s, inventory = %s, visible = %s, category = %s WHERE sku = %s"
update_prod_sql_with_image = "UPDATE Product SET name = %s, description=%s, price=%s, weight = %s, inventory = %s, visible = %s, category = %s, image=%s WHERE sku = %s"

get_prod_sql = "SELECT sku, name, description, price, inventory, weight, visible, category FROM Product WHERE sku = %s"

list_prod_sql = "SELECT * FROM Product WHERE visible = 1"
filter_prod_sql = "SELECT * FROM Product WHERE Product.visible = 1 AND Product.name LIKE %s"


@app.route("/products/", methods=['GET'])
def view_products(cid=None):
    sql = list_prod_sql

    args = []
    search = ""
    if 'search' in request.args:
        sql = filter_prod_sql
        search = request.args["search"]
        args.append("%" + request.args["search"] + "%")

    if cid:
        sql += " and category = %s"
        args.append(cid)

    with get_db().cursor() as cursor:
        cursor.execute(sql, args)
        result = cursor.fetchall()

        user = get_user_object()
        if user:
            return render_template("product_list.html", products=result, search=search, cid=cid,
                                   user=user)
        else:
            return render_template("product_list.html", products=result, search=search, cid=cid)


@app.route("/products/category/<string:cid>", methods=['GET'])
def product_categories(cid=None):
    if cid == "all":
        return ajax_products()
    elif cid == "hot":
        return render_template("product_cards.html", products=get_hot_products())


    sql = list_prod_sql



    sql += " and category = %s"

    args = []
    args.append(int(cid))

    with get_db().cursor() as cursor:
        cursor.execute(sql, args)
        result = cursor.fetchall()
        return render_template("product_cards.html", products=result)


@app.route("/products/search/", methods=['GET'])
def ajax_products():
    with get_db().cursor() as cursor:

        if 'search' in request.args:
            cursor.execute(filter_prod_sql, '%' + request.args["search"] + '%')
        else:
            cursor.execute(list_prod_sql)

        result = cursor.fetchall()
        return render_template("product_cards.html", products=result, search=request.args.get("search", ""))


@app.route("/product/<sku>")
def view_product(sku):
    """Displays a products"""
    try:
        with get_db().cursor() as cursor:
            cursor.execute(get_prod_sql, int(sku))
            product = cursor.fetchone()
            return render_template("product_details.html", product=product, user=get_user_object())
    except Exception as e:
        app.log_exception(e)
    return render_template("error.html", msg="Unable to display the product", user=get_user_object())


@app.route("/product/<int:sku>/edit", methods=['post', 'get'])
@requires_roles('admin')
def edit_product(sku):
    """Prepares and edit product page with a get request by fetching the product details from the server"""
    # Setup the edit product page with auto filled values
    if request.method == 'GET':
        with get_db().cursor() as cursor:
            cursor.execute(get_prod_sql, sku)
            result = cursor.fetchone()
            if not result:
                return render_template("error.html", msg="Unable to retrieve product details")
            result["showInStore"] = "1" if result["visible"] == 1 else ''
            return render_template("edit_product.html", data=result, categories=fetch_categories(),
                                   user=get_user_object())

    # Validate and submit
    data = request.form
    args = prepare_product_insert_data(data)

    if not args:
        return render_template("edit_product.html", data=data, user=get_user_object())

    sql = update_prod_sql_no_image

    if request.files and 'image' in request.files:
        print(request.files)
        filename = request.files['image'].filename
        if filename:
            mime_type = request.files['image'].mimetype
            sql = update_prod_sql_with_image
            args.append(fix_image(request.files['image'].stream))

    args.append(sku)

    try:
        with get_db().cursor() as cursor:
            cursor.execute(sql, args)
            get_db().commit()
            flash("Updated product", "success")
            return redirect(url_for("view_product", sku=sku))
    except Exception as e:
        print(e)
    flash("Unable to Edit product", "error")
    return render_template("edit_product.html", data=data, user=get_user_object())


@app.route("/product/add", methods=['post', 'get'])
@requires_roles('admin')
def add_product():
    if request.method == 'GET':
        return render_template("add_product.html", data={}, categories=fetch_categories(), user=get_user_object())

    args = prepare_product_insert_data(request.form)

    if not args:
        return render_template("add_product.html", data=request.form, user=get_user_object())

    sql = create_prod_sql_no_image

    if request.files and 'image' in request.files:
        filename = request.files['image'].filename
        if filename:
            sql = create_prod_sql_with_image
            mime_type = request.files['image'].mimetype
            file = fix_image(request.files['image'].stream)
            args.append(file)
    try:
        with get_db().cursor() as cursor:
            rows = cursor.execute(sql, args)
            get_db().commit()
            if rows == 1:
                return redirect(url_for("view_product", sku=cursor.lastrowid))
    except Exception as e:
        print(e)
    flash("Unable to create product", "success")
    return render_template("add_product.html", data=request.form, user=get_user_object())


from PIL import Image


@app.route("/product/<int:sku>/image.png")
def product_picture(sku):
    """Retrieves a product image from the database and server it as an image file"""
    sql = "SELECT image FROM Product WHERE sku = %s"
    with get_db().cursor() as cursor:
        cursor.execute(sql, sku)
        return send_file(io.BytesIO(cursor.fetchone()["image"]), mimetype="image/png")


def fix_image(image_file):
    """
    See: https://stackoverflow.com/a/1386382/7459703
    :param image_file: The file stream containing the image.
    :return: The image bytes for the new photo
    """
    size = (300, 300)
    image = Image.open(image_file)
    image.thumbnail(size, Image.ANTIALIAS)
    background = Image.new('RGBA', size, (255, 255, 255, 0))
    background.paste(
        image, (int((size[0] - image.size[0]) / 2), int((size[1] - image.size[1]) / 2))
    )
    stream = io.BytesIO()
    background.save(stream, format="PNG")
    return stream.getvalue()


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
    args.append(data['category'])

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
        flash("Product name is required", "error")
        valid = False
    if not data['description']:
        flash("Description is required", "error")
        valid = False
    if not data['weight']:
        flash("Weight is required", "error")
        valid = False
    if not data['price']:
        flash("Price is required", "error")
        valid = False
    if not data['category']:
        valid = False
        flash("Category is required", "error")
    return valid


hot_products_sql = "SELECT P.sku, P.name, P.description, P.price, P.inventory, P.weight, P.visible, C.name AS catName, SUM(quantity) AS amountSold " \
                   "FROM ShippedProduct SP JOIN Product P ON SP.sku = P.sku JOIN Category C ON P.category = C.id " \
                   "WHERE P.visible = 1 " \
                   "GROUP BY P.name, P.price, P.sku, P.inventory, P.weight, P.category, P.visible, P.description, C.name " \
                   "ORDER BY SUM(quantity) DESC " \
                   "LIMIT 6;"


def get_hot_products():
    """Retrieves the hot products from the database. This is the products with the most quantity sales

    :returns And array containing the hot products
    """

    try:
        with get_db().cursor() as cursor:
            cursor.execute(hot_products_sql)
            products = cursor.fetchall()
            return products
    except Error as e:
        current_app.logger.error(e)
        return []
