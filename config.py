# config.py

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for sessions (change this for real apps)
    SECRET_KEY = "restaurant_management_secret_123"

    # SQLite database
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "restaurant.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
