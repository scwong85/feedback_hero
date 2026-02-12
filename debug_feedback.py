import sys

sys.path.insert(0, ".")

from app import app, db
from models import Business, Feedback

with app.app_context():
    # Check businesses
    businesses = Business.query.all()
    print("=" * 60)
    print("BUSINESSES IN DATABASE:")
    print("=" * 60)
    for b in businesses:
        print(f"ID: {b.id}, Name: {b.name}, Email: {b.email}")

    print("\n" + "=" * 60)
    print("FEEDBACK IN DATABASE:")
    print("=" * 60)

    # Check feedback
    all_feedback = Feedback.query.all()
    print(f"Total feedback entries: {len(all_feedback)}\n")

    for f in all_feedback:
        print(f"ID: {f.id}")
        print(f"Business ID: {f.business_id}")
        print(f"Timestamp: {f.timestamp}")
        print(f"Overall Rating: {f.overall_rating}")
        print(f"Food: {f.food_rating}, Service: {f.service_rating}")
        print(f"NPS: {f.nps_score}")
        print(f"Comment: {f.comment}")
        print("-" * 40)

    if len(all_feedback) == 0:
        print("⚠️  No feedback found in database!")
        print("\nPossible issues:")
        print("1. Feedback submission might be failing")
        print("2. Database path might be wrong")
        print("3. Check browser console for errors")
