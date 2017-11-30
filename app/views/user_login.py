from functools import wraps

import flask
from flask import render_template, url_for, abort, request, flash, redirect
from werkzeug.security import check_password_hash

from app.util import is_user_admin, is_logged_in, set_user_data, clear_user_data
from app.util import set_cart_id
from . import app, get_db
from .cart import transfer_session_cart_to_user_cart


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    next_link = "/"
    if "next" in request.args:
        next_link = request.args["next"]

    if flask.request.method == 'GET':
        return render_template("login.html", next=next_link)

    sql = "SELECT * FROM User WHERE username=%s;"

    data = flask.request.form

    with get_db().cursor() as cursor:
        cursor.execute(sql, data["username"])
        u = cursor.fetchone()
        if u:
            if not check_password_hash(u['pass'], data['password']):
                flash("Invalid username or password")
                return redirect(request.referrer)

            # Add the user data into the session
            set_user_data(u["id"], u["name"], u["username"], u['accountType'] == 1)
            check_and_cache_cart_id(u["id"])
            transfer_session_cart_to_user_cart()
            return flask.redirect(next_link)
    flash("Invalid username or password")
    return redirect(request.referrer)


def check_and_cache_cart_id(user_id):
    """Verifies that the user has a cart in the database and that the cartID is stored in the session"""
    sql = "SELECT cartID FROM Cart WHERE userID = %s"
    create_cart = "INSERT INTO Cart(userID) VALUES (%s)"
    cart_id = None
    try:
        with get_db().cursor() as cursor:
            row_count = cursor.execute(sql, user_id)
            row = cursor.fetchone()
            if not row_count:
                cursor.execute(create_cart, user_id)
                cart_id = cursor.lastrowid
                get_db().commit()
            else:
                cart_id = row["cartID"]
            set_cart_id(cart_id)
    except Exception as e:
        app.logger.error(e)


@app.route("/user/logout")
def logout():
    clear_user_data()
    return flask.redirect("/")


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
        return flask.redirect(url_for("login", next=request.path))
    return abort(403)


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            current_roles = get_current_user_roles()
            if not any([role in current_roles for role in roles]):
                return access_error_response()
            return f(*args, **kwargs)

        return wrapped

    return wrapper
