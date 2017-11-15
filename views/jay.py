from . import views as app

@app.route('/')
def index():
    return 'Hello World!'
