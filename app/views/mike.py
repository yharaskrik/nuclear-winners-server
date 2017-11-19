from flask import jsonify

from views import views as app

@app.route('/mike')
def hola_amigo():
    obj = {}
    obj[0] = 'strings stuff'
    return jsonify(obj)
