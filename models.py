from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    phone         = db.Column(db.String(15), nullable=True)
    state         = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Password reset fields
    reset_token         = db.Column(db.String(100), nullable=True)
    reset_token_expiry  = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        from datetime import timedelta
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def is_reset_token_valid(self, token):
        return (
            self.reset_token == token and
            self.reset_token_expiry is not None and
            datetime.utcnow() < self.reset_token_expiry
        )

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self):
        return f'<User {self.email}>'