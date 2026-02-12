from flask import Flask
from flask_login import LoginManager
from models import db, Business
from config import Config
from auth import auth_bp
from feedback_routes import feedback_bp
from dashboard_routes import dashboard_bp
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return Business.query.get(int(user_id))


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(dashboard_bp)


# Initialize database
def init_db():
    """Initialize database and create default user"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")

        # Create default business account if none exists
        if Business.query.count() == 0:
            default_business = Business(
                name=app.config["BUSINESS_NAME"], email="admin@business.com"
            )
            default_business.set_password("admin123")
            db.session.add(default_business)
            db.session.commit()
            print("\n" + "=" * 50)
            print("✓ Default business account created")
            print("=" * 50)
            print(f"  Business Name: {app.config['BUSINESS_NAME']}")
            print(f"  Email: admin@business.com")
            print(f"  Password: admin123")
            print("=" * 50)
            print("⚠️  IMPORTANT: Change this password immediately!")
            print("   Go to: /dashboard/settings after logging in")
            print("=" * 50 + "\n")
        else:
            print(f"✓ Found existing business account(s)")


# Initialize database when app starts
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
