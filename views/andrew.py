from flask import jsonify, request, render_template

from . import views as app

@app.route("/product/<int:id>", methods=['GET'])
def do_something(pid):

    obj = {}

    obj["this thing"] = pid

    return jsonify(obj)


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


