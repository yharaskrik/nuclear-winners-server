from flask import Blueprint, Flask

from app import app
from app import get_db

views = Blueprint('views', __name__, template_folder='templates')

from .andrew import *
from .jay import *
from .mike import *
