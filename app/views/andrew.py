from flask import jsonify, request, render_template, Flask

from . import get_db, app

@app.route("/products/", methods=['GET'])
def view_products():
    obj = {}
    with get_db().cursor() as cursor:
        cursor.execute("Select * from Product")
        result = cursor.fetchall()
        return render_template("product_list.html", products=result)


create_prod_sql = "INSERT INTO Product (name, description , price) VALUES (%s, %s, %s)"


@app.route("/product/add", methods=['post', 'get'])
def add_product():

    if request.method == 'GET':
        return render_template("add_product.html")

    """Creates a product from form data"""
    data = request.form
    f = request.files['image']

    with get_db().cursor() as cursor:
        cursor.execute(create_prod_sql, [data["name"], data["description"], data["price"]])

    return jsonify(data)

@app.route("/")
def home():
    return render_template("index.html")