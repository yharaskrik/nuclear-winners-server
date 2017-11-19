from flask import jsonify, request, render_template, Flask

from . import get_db, app

@app.route("/products/", methods=['GET'])
def view_products():
    obj = {}
    with get_db().cursor() as cursor:
        cursor.execute("Select * from Product")
        result = cursor.fetchall()
        return render_template("product_list.html", products=result)


