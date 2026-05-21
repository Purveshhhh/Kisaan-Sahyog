import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kisaan-sahyog-secret-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///kisaan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    PLANTID_API_KEY = os.environ.get('PLANTID_API_KEY')
    MANDI_API_KEY = os.environ.get('MANDI_API_KEY')
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Mail settings
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')