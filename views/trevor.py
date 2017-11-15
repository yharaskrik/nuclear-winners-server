#@app.route('/get/Product/<type:param>')
#def name(param)
from flask import jsonify

from views import views as app

@app.route('/get/product/<int:id>')
def something(id):
    return jsonify(id)

