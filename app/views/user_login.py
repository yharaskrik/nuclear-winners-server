import flask
from flask import render_template, session, url_for, abort, request
from werkzeug.security import check_password_hash, generate_password_hash

from . import app, get_db


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template("login.html")

    sql = "SELECT * FROM User WHERE username=%s;"

    data = flask.request.form

    with get_db().cursor() as cursor:
        cursor.execute(sql, data["username"])
        u = cursor.fetchone()
        if u:
            if not check_password_hash(u['pass'], data['password']):
                return render_template("login.html", errormsg="Invalid username or password")
            session["user_id"] = u["id"]
            session["user_name"] = u["name"]
            session["user_username"] = u["username"]
            session["user_admin"] = u['accountType'] == 1
            session["logged_in"] = True
            return flask.redirect("/")
    return render_template("login.html", errormsg="Invalid username or password")


@app.route("/user/logout")
def logout():
    del (session["user_id"])
    del (session["user_name"])
    del (session["user_username"])
    session['user_admin'] = False
    session["logged_in"] = False
    return flask.redirect("/")


from app.util import is_user_admin, is_logged_in

from functools import wraps


def get_current_user_roles():
    roles = []
    if is_user_admin():
        roles.append('admin')
        print("Session is logged in as admin")
    if is_logged_in():
        roles.append('user')
        print("Session is logged in as a user")
    else:
        print("Session is not logged in")
    return roles


# http://flask.pocoo.org/snippets/98/
def access_error_response():
    if not is_logged_in():
        flask.flash("You are required to login to view this page")
        return flask.redirect(url_for("views.login", next=request.endpoint))
    return abort(403)


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            current_roles = get_current_user_roles()
            if not all([role in current_roles for role in roles]):
                return access_error_response()
            return f(*args, **kwargs)

        return wrapped

    return wrapper
