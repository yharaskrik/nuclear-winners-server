from flask import Blueprint
views = Blueprint('views', __name__)

from .jay import *
from .andrew import *