from flask import Blueprint

from app import app, get_db

views = Blueprint('views', __name__)

from .jay import *
from .user_login import *
from .mike import *
from .trevor import *
from .cart import *
