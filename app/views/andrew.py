from flask import jsonify, request, render_template, Flask

from . import get_db, app

@app.route("/product/<int:pid>", methods=['GET'])
def do_something(pid):
    obj = {}
    with get_db().cursor() as cursor:
        cursor.execute("Select * from Products")
        result = cursor.fetchall()
        return jsonify(result)


@app.route("/product/add", methods=['post', 'get'])
def add_product():

    if request.method == 'GET':
        return render_template("add_product.html")


    """Creates a product from form data"""
    data = {request.form}
    f = request.files['image']
    if f is not None:
        data["image"] = True

    return jsonify(data)


