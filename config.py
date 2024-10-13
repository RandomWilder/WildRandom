import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///raffle_platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '123456'  # Change this to a random secret key