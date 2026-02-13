import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Database configuration - Render compatible
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # PostgreSQL on Render
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Local SQLite development
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(basedir, "instance", "feedback.db")
        instance_dir = os.path.join(basedir, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BUSINESS_NAME = os.environ.get("BUSINESS_NAME") or "My Restaurant"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    FEEDBACK_COOLDOWN_MINUTES = 5
