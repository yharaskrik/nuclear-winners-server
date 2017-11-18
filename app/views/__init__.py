from flask import Blueprint, Flask

from app import app
from app import get_db

views = Blueprint('views', __name__)

from .andrew import *
from .jay import *

