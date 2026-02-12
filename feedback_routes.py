from flask import Blueprint, render_template, request, jsonify, session
from models import db, Business, Feedback
from datetime import datetime, timedelta

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/')
def index():
    """Customer feedback landing page"""
    business = Business.query.first()
    if not business:
        return "Business not configured", 500
    return render_template('customer/index.html', business=business)

@feedback_bp.route('/thankyou')
def thankyou():
    """Thank you page after feedback submission"""
    business = Business.query.first()
    return render_template('customer/thankyou.html', business=business)

@feedback_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit customer feedback

    Expected JSON payload:
    {
        "overall_rating": 1-3,
        "food_rating": 1-5,
        "service_rating": 1-5,
        "staff_rating": 1-5,
        "cleanliness_rating": 1-5,
        "value_rating": 1-5,
        "nps_score": 0-10,
        "comment": "optional text"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Rate limiting check using session
        last_feedback = session.get('last_feedback_time')
        if last_feedback:
            try:
                last_time = datetime.fromisoformat(last_feedback)
                cooldown = timedelta(minutes=5)
                if datetime.utcnow() - last_time < cooldown:
                    minutes_left = 5 - int((datetime.utcnow() - last_time).total_seconds() / 60)
                    return jsonify({
                        'error': f'Please wait {minutes_left} more minute(s) before submitting again'
                    }), 429
            except:
                pass

        # Get business (for single-tenant, it's the first one)
        business = Business.query.first()
        if not business:
            return jsonify({'error': 'Business not found'}), 404

        # Validate required fields
        overall_rating = data.get('overall_rating')
        if not overall_rating or overall_rating not in [1, 2, 3]:
            return jsonify({'error': 'Invalid overall rating'}), 400

        # Validate optional ratings
        def validate_rating(value, min_val, max_val):
            if value is None:
                return None
            try:
                val = int(value)
                if min_val <= val <= max_val:
                    return val
            except:
                pass
            return None

        # Create feedback entry
        feedback = Feedback(
            business_id=business.id,
            overall_rating=overall_rating,
            food_rating=validate_rating(data.get('food_rating'), 1, 5),
            service_rating=validate_rating(data.get('service_rating'), 1, 5),
            staff_rating=validate_rating(data.get('staff_rating'), 1, 5),
            cleanliness_rating=validate_rating(data.get('cleanliness_rating'), 1, 5),
            value_rating=validate_rating(data.get('value_rating'), 1, 5),
            nps_score=validate_rating(data.get('nps_score'), 0, 10),
            comment=data.get('comment', '').strip()[:200] or None
        )

        db.session.add(feedback)
        db.session.commit()

        # Update session to prevent spam
        session['last_feedback_time'] = datetime.utcnow().isoformat()
        session.permanent = True

        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedback_id': feedback.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error submitting feedback: {e}")
        return jsonify({'error': 'An error occurred while submitting feedback'}), 500

@feedback_bp.route('/api/feedback/check-limit', methods=['GET'])
def check_limit():
    """Check if user can submit feedback (rate limiting check)"""
    last_feedback = session.get('last_feedback_time')

    if not last_feedback:
        return jsonify({'can_submit': True, 'wait_minutes': 0})

    try:
        last_time = datetime.fromisoformat(last_feedback)
        cooldown = timedelta(minutes=5)
        time_diff = datetime.utcnow() - last_time

        if time_diff < cooldown:
            minutes_left = 5 - int(time_diff.total_seconds() / 60)
            return jsonify({
                'can_submit': False,
                'wait_minutes': minutes_left
            })
    except:
        pass

    return jsonify({'can_submit': True, 'wait_minutes': 0})

@feedback_bp.route('/api/feedback/stats', methods=['GET'])
def public_stats():
    """
    Optional: Public statistics endpoint
    Shows aggregate statistics without revealing individual feedback
    """
    business = Business.query.first()
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    # Get last 30 days of feedback
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    feedback_list = Feedback.query.filter(
        Feedback.business_id == business.id,
        Feedback.timestamp >= thirty_days_ago
    ).all()

    if not feedback_list:
        return jsonify({
            'total_responses': 0,
            'average_rating': 0,
            'response_message': 'Be the first to leave feedback!'
        })

    # Calculate average overall rating
    avg_rating = sum(f.overall_rating for f in feedback_list) / len(feedback_list)

    # Calculate NPS
    nps_scores = [f.nps_score for f in feedback_list if f.nps_score is not None]
    nps = 0
    if nps_scores:
        promoters = len([s for s in nps_scores if s >= 9])
        detractors = len([s for s in nps_scores if s <= 6])
        nps = round(((promoters - detractors) / len(nps_scores)) * 100, 1)

    return jsonify({
        'total_responses': len(feedback_list),
        'average_rating': round(avg_rating, 2),
        'nps_score': nps,
        'business_name': business.name
    })
