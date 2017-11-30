from flask import render_template

from app.util import get_user_object
from . import app
from .views import user_login


@app.route("/admin")
@user_login.requires_roles("admin")
def admin():
    """Shows the admin page if the user is logged in and an admin"""
    return render_template("admin.html", user=get_user_object())
