from flask import Flask, g

import config

try:
    import dbconfig
except Exception:
    import os

    dbconfig = lambda: None
    dbconfig.db_host = os.environ.get('db_host', None)
    dbconfig.db_user = os.environ.get('db_user', None)
    dbconfig.db_password = os.environ.get('db_password', None)
    dbconfig.db = os.environ.get('db', None)
    dbconfig.db_charset = os.environ.get('db_charset', None)

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


@app.errorhandler(403)
def not_authorized(e):
    return render_template("403.html")


@app.route('/', defaults={'path': ''})
def main_page(path):
    # return render_template("product_list.html")
    hot_products = get_hot_products()
    return render_template("index.html", hot_products=hot_products)


from .account import *
from .admin import *
from .cart import *
from .categories import *
from .mutations import get_mutations
from .order import *
from .product import *
from .user_login import *
