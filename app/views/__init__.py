from flask import Blueprint

views = Blueprint('views', __name__)

from .user_login import *
from .mike import *
from .trevor import *
from .cart import *
