from flask import Blueprint

from app import app, get_db

views = Blueprint('views', __name__)

from .andrew import *
from .jay import *
from .user_login import *
