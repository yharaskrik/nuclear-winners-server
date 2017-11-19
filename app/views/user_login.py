import flask
from flask import render_template, session

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
