from flask import jsonify, render_template

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from . import views as app

# This might change when andrew switches the DB
connection = pymysql.connect(host='72.249.48.95',
                             user='geaxyckp_nuclear_winter',
                             password='.EoP0Ea#i&,{',
                             db='geaxyckp_nuclear_winter',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

# Look here for querying
# https://github.com/PyMySQL/PyMySQL

@app.route('/')
def index():
    # I created a customer table i the DB right now so yo guys could practice
    # it only has one record with one column 'id'
    cur = connection.cursor()
    st = 'select * from %s'
    st = st.format('customer')
    print(st)
    cur.execute('')

        # This will return the parsed json from the DB
    return render_template('index.html')
