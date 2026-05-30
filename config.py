import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY                     = os.environ.get('SECRET_KEY') or 'kisaan-sahyog-secret-2024'
    SQLALCHEMY_DATABASE_URI        = os.environ.get('DATABASE_URL') or 'sqlite:///kisaan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENWEATHER_API_KEY            = os.environ.get('OPENWEATHER_API_KEY')
    PLANTID_API_KEY                = os.environ.get('PLANTID_API_KEY')
    MANDI_API_KEY                  = os.environ.get('MANDI_API_KEY')
    GEMINI_API_KEY                 = os.environ.get('GEMINI_API_KEY')
    UPLOAD_FOLDER                  = 'static/uploads'
    MAX_CONTENT_LENGTH             = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME     = timedelta(days=7)

    # Fix session cookie for Render
    SESSION_COOKIE_SECURE          = False
    SESSION_COOKIE_HTTPONLY        = True
    SESSION_COOKIE_SAMESITE        = 'Lax'
    REMEMBER_COOKIE_SECURE         = False
    REMEMBER_COOKIE_HTTPONLY       = True
    REMEMBER_COOKIE_DURATION       = timedelta(days=7)

    # Mail
    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')