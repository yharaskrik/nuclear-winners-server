from flask import jsonify
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
