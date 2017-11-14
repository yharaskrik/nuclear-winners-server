from views import app

@app.route("/product/<int:id>", methods=['GET'])
def do_something(pid):
    return pid