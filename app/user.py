import flask_login
from flask_login import LoginManager
from app import get_db


class User(flask_login.UserMixin):
    pass


