from app import app, db
from models import Business

with app.app_context():
    business = Business.query.first()

    print("=" * 60)
    print("PASSWORD FUNCTIONALITY TEST")
    print("=" * 60)

    if not business:
        print("❌ No business found")
        exit(1)

    print(f"✓ Business: {business.name} ({business.email})")

    # Test current password
    print("\n1. Testing current password check...")
    if business.check_password("admin123"):
        print("   ✓ Current password 'admin123' is correct")
    else:
        print("   ❌ Current password check failed")

    # Test password change
    print("\n2. Testing password change...")
    business.set_password("newpassword123")

    if business.check_password("newpassword123"):
        print("   ✓ New password works!")
    else:
        print("   ❌ New password failed")

    # Reset
    business.set_password("admin123")
    db.session.commit()
    print("\n3. Password reset to 'admin123'")
    print("\n" + "=" * 60)
