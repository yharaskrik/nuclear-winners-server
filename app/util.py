from flask import session


def set_user_data(user_id, user_name, user_username, user_is_admin):
    """Adds the user data into the session"""
    session["user_id"] = user_id
    session["user_name"] = user_name
    session["user_username"] = user_username
    session["user_admin"] = user_is_admin
    session["logged_in"] = True


def is_user_admin():
    """Returns if the current user is an admin by checking the logged in session variable"""
    return 'user_admin' in session and session['user_admin']


def is_logged_in():
    """Returns if the current user is logged in by checking the session variables"""
    return 'logged_in' in session and session["logged_in"]


def get_user_id():
    """Returns the current user's id from the session or null if the user is not logged in"""
    if is_logged_in():
        return session["user_id"]
    return ""


def set_cart_id(cart_id):
    """Sets the session cart id"""
    session["cart_id"] = cart_id


def get_cart_id():
    """Returns the session cart id or none if it is not set"""
    if is_logged_in() and "cart_id" in session and session["cart_id"]:
        return session["cart_id"]
    return None


def clear_cart_id():
    session.pop("cart_id", None)
