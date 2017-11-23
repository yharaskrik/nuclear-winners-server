from flask import jsonify
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from . import views as app

# This might change when andrew switches the DB

# Look here for querying
# # https://github.com/PyMySQL/PyMySQL
#
# @app.route('/')
# def index():
#     # I created a customer table i the DB right now so yo guys could practice
#     # it only has one record with one column 'id'
#     with connection.cursor() as cursor:
#         cursor.execute('select * from customer')
#         result = cursor.fetchone()
#         print(result)
#         # This will return the parsed json from the DB
#         return jsonify(result)
