from flask import Flask, g

import config
import dbconfig

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass

app = Flask(__name__, static_url_path='/static')
app.config.from_object(config)


def connect_db():
    """Connects to the applicaiton database"""
    connection = pymysql.connect(host=dbconfig.db_host,
                                 user=dbconfig.db_user,
                                 password=dbconfig.db_password,
                                 db=dbconfig.db,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def get_db():
    """ Returns a database connection, creating a new one if one does not already exist for the current application
    context. """
    if not hasattr(g, 'db_connection'):
        g.db_connection = connect_db()
    return g.db_connection


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db_connection'):
        g.db_connection.close()


from app.views import views as views

app.register_blueprint(views)


@app.errorhandler(403)
def not_authorized(e):
    return render_template("403.html")


from .product import *

from .admin import *
from .categories import *


@app.route('/', defaults={'path': ''})
def main_page(path):
    # return render_template("product_list.html")
    hot_products = get_hot_products()
    return render_template("index.html", hot_products=hot_products)


from .order import *
