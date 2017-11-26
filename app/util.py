from flask import session


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
