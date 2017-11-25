import flask
from flask import render_template, session, url_for, abort

from . import app, get_db


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template("login.html")

    sql = "SELECT * FROM User WHERE username=%s and pass=%s;"

    data = flask.request.form

    with get_db().cursor() as cursor:
        cursor.execute(sql, (data["username"], data["password"]))
        u = cursor.fetchone()
        if u:
            session["user_id"] = u["id"]
            session["user_name"] = u["name"]
            session["user_username"] = u["username"]
            session["user_admin"] = u['accountType'] == 1
            session["logged_in"] = True
            return flask.redirect("/")
    return render_template("login.html", errormsg="Invalid username or password")

@app.route("/user/logout")
def logout():
    del(session["user_id"])
    del(session["user_name"])
    del(session["user_username"])
    session['user_admin'] = False
    session["logged_in"] = False
    return flask.redirect("/")

from app.util import is_user_admin, is_logged_in

from functools import wraps


def get_current_user_role():
    if is_user_admin():
        return 'admin'

    if is_logged_in():
        return "user"

    return ''


# http://flask.pocoo.org/snippets/98/
def access_error_response():
    if not is_logged_in():
        flask.flash("You are required to login to view this page")
        return flask.redirect(url_for("views.login"))

    return abort(403)


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_role() not in roles:
                return access_error_response()
            return f(*args, **kwargs)
        return wrapped
    return wrapper
