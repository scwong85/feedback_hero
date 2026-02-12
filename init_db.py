from app import app, db
from models import Business


def init_database():
    """Initialize database and create tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully")

        # Check if business exists
        business_count = Business.query.count()
        print(f"✓ Found {business_count} business account(s)")

        if business_count == 0:
            print("\n⚠️  No business account found. Creating default account...")
            default_business = Business(
                name="My Restaurant", email="admin@business.com"
            )
            default_business.set_password("admin123")
            db.session.add(default_business)
            db.session.commit()
            print("✓ Default account created: admin@business.com / admin123")


if __name__ == "__main__":
    init_database()
