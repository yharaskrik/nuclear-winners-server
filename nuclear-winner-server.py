from flask import Flask
from views import *

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

app = Flask(__name__)
app.register_blueprint(views)

if __name__ == '__main__':
    app.run()
