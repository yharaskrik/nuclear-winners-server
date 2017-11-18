from flask import Flask, g

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass

app = Flask("name")


def connect_db():
    """Connects to the applicaiton database"""
    connection = pymysql.connect(host='72.249.48.95',
                                 user='geaxyckp_nuclear_winter',
                                 password='.EoP0Ea#i&,{',
                                 db='geaxyckp_nuclear_winter',
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