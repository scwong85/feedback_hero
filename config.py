import os
from datetime import timedelta


class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Database configuration - Use instance folder for SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "instance", "feedback.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Business configuration
    BUSINESS_NAME = os.environ.get("BUSINESS_NAME") or "My Restaurant"

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Feedback rate limiting (prevent spam)
    FEEDBACK_COOLDOWN_MINUTES = 5
