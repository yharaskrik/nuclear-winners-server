from flask import session

from app import get_db


def set_user_data(user_id, user_name, user_username, user_is_admin):
    """Adds the user data into the session"""
    session["user_id"] = user_id
    session["user_name"] = user_name
    session["user_username"] = user_username
    session["user_admin"] = user_is_admin
    session["logged_in"] = True


def clear_user_data():
    """Clears the user data from the session"""
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_username", None)
    session.pop("user_admin", None)
    session.pop("cart_id", None)
    session["logged_in"] = False


def is_user_admin():
    """Returns if the current user is an admin by checking the logged in session variable"""
    return session.get('user_admin', False)


def is_logged_in():
    """Returns if the current user is logged in by checking the session variables"""
    return session.get("logged_in", False)


def get_user_id():
    """Returns the current user's id from the session or null if the user is not logged in"""
    if is_logged_in():
        return session.get("user_id")
    return


def set_cart_id(cart_id):
    """Sets the session cart id"""
    session["cart_id"] = cart_id


def get_cart_id():
    """Returns the session cart id or none if it is not set"""
    if is_logged_in():
        return session.get("cart_id")


def clear_cart_id():
    session.pop("cart_id", None)


def get_user_object():
    sql = 'SELECT * FROM User WHERE id = %s'
    with get_db().cursor() as cursor:
        cursor.execute(sql, session['user_id'])
        user = cursor.fetchone()
        print(user)
        return user
    return None