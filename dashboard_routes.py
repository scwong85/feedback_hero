from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Feedback
from datetime import datetime, timedelta
from collections import defaultdict
import csv
from io import BytesIO, StringIO
import qrcode

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def overview():
    """Main dashboard overview page"""
    return render_template("dashboard/overview.html", business=current_user)


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    """Analytics page with detailed insights"""
    return render_template("dashboard/analytics.html", business=current_user)


@dashboard_bp.route("/feedback")
@login_required
def feedback_list():
    """Feedback list page"""
    return render_template("dashboard/feedback_list.html", business=current_user)


@dashboard_bp.route("/settings")
@login_required
def settings():
    """Settings page"""
    return render_template("dashboard/settings.html", business=current_user)


@dashboard_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change password for logged-in user"""
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect", "error")
        return redirect(url_for("dashboard.settings"))

    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect(url_for("dashboard.settings"))

    if len(new_password) < 8:
        flash("Password must be at least 8 characters long", "error")
        return redirect(url_for("dashboard.settings"))

    current_user.set_password(new_password)

    try:
        db.session.commit()
        flash("Password changed successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error changing password", "error")

    return redirect(url_for("dashboard.settings"))


@dashboard_bp.route("/update-business", methods=["POST"])
@login_required
def update_business():
    """Update business name and email"""
    business_name = request.form.get("business_name", "").strip()
    email = request.form.get("email", "").strip()

    if not business_name or not email:
        flash("Business name and email are required", "error")
        return redirect(url_for("dashboard.settings"))

    # Check if email is already taken by another business
    existing = Business.query.filter(
        Business.email == email, Business.id != current_user.id
    ).first()

    if existing:
        flash("Email already in use by another business", "error")
        return redirect(url_for("dashboard.settings"))

    current_user.name = business_name
    current_user.email = email

    try:
        db.session.commit()
        flash("Business information updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error updating business information", "error")

    return redirect(url_for("dashboard.settings"))


@dashboard_bp.route("/api/feedback/delete-all", methods=["DELETE"])
@login_required
def delete_all_feedback():
    """Delete all feedback (danger zone action)"""
    try:
        Feedback.query.filter_by(business_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"success": True, "message": "All feedback deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error deleting feedback"}), 500


# ==================== API ROUTES ====================


@dashboard_bp.route("/api/stats")
@login_required
def dashboard_stats():
    """
    Get dashboard statistics

    Returns:
    - Today's feedback count and average rating
    - Week's feedback count and average rating
    - Month's feedback count and average rating
    - Daily breakdown for the last 7 days
    - Category ratings for the last 30 days
    - NPS score for the last 30 days
    """
    try:
        # Today's stats
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_feedback = Feedback.query.filter(
            Feedback.business_id == current_user.id, Feedback.timestamp >= today_start
        ).all()

        # Last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_feedback = (
            Feedback.query.filter(
                Feedback.business_id == current_user.id, Feedback.timestamp >= week_ago
            )
            .order_by(Feedback.timestamp.asc())
            .all()
        )

        # Last 30 days
        month_ago = datetime.utcnow() - timedelta(days=30)
        month_feedback = Feedback.query.filter(
            Feedback.business_id == current_user.id, Feedback.timestamp >= month_ago
        ).all()

        # Calculate averages
        def calc_avg(feedback_list, field):
            values = [
                getattr(f, field)
                for f in feedback_list
                if getattr(f, field) is not None
            ]
            return round(sum(values) / len(values), 2) if values else 0

        # Daily breakdown for chart (last 7 days)
        daily_data = defaultdict(lambda: {"count": 0, "avg_rating": []})
        for f in week_feedback:
            day_key = f.timestamp.strftime("%Y-%m-%d")
            daily_data[day_key]["count"] += 1
            if f.overall_rating:
                daily_data[day_key]["avg_rating"].append(f.overall_rating)

        daily_chart = []
        for i in range(7):
            day = today_start - timedelta(days=6 - i)
            day_key = day.strftime("%Y-%m-%d")
            data = daily_data[day_key]
            avg = (
                round(sum(data["avg_rating"]) / len(data["avg_rating"]), 2)
                if data["avg_rating"]
                else 0
            )
            daily_chart.append(
                {
                    "date": day.strftime("%a %m/%d"),
                    "count": data["count"],
                    "avg_rating": avg,
                }
            )

        # Category breakdown (last 30 days)
        categories = {
            "food": calc_avg(month_feedback, "food_rating"),
            "service": calc_avg(month_feedback, "service_rating"),
            "staff": calc_avg(month_feedback, "staff_rating"),
            "cleanliness": calc_avg(month_feedback, "cleanliness_rating"),
            "value": calc_avg(month_feedback, "value_rating"),
        }

        # NPS calculation (last 30 days)
        nps_scores = [f.nps_score for f in month_feedback if f.nps_score is not None]
        if nps_scores:
            promoters = len([s for s in nps_scores if s >= 9])
            detractors = len([s for s in nps_scores if s <= 6])
            nps = round(((promoters - detractors) / len(nps_scores)) * 100, 1)
        else:
            nps = 0

        # Total responses ever
        total_responses = Feedback.query.filter_by(business_id=current_user.id).count()

        return jsonify(
            {
                "today": {
                    "count": len(today_feedback),
                    "avg_rating": calc_avg(today_feedback, "overall_rating"),
                },
                "week": {
                    "count": len(week_feedback),
                    "avg_rating": calc_avg(week_feedback, "overall_rating"),
                },
                "month": {
                    "count": len(month_feedback),
                    "avg_rating": calc_avg(month_feedback, "overall_rating"),
                },
                "daily_chart": daily_chart,
                "categories": categories,
                "nps": nps,
                "total_responses": total_responses,
            }
        )

    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({"error": "Error loading statistics"}), 500


@dashboard_bp.route("/api/feedback")
@login_required
def get_feedback():
    """
    Get paginated feedback list

    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - filter: Filter by rating (optional)
    - sort: Sort order (default: newest)
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        filter_rating = request.args.get("filter", type=int)
        sort_order = request.args.get("sort", "newest")

        # Base query
        query = Feedback.query.filter_by(business_id=current_user.id)

        # Apply filters
        if filter_rating and 1 <= filter_rating <= 3:
            query = query.filter_by(overall_rating=filter_rating)

        # Apply sorting
        if sort_order == "oldest":
            query = query.order_by(Feedback.timestamp.asc())
        elif sort_order == "rating_high":
            query = query.order_by(
                Feedback.overall_rating.desc(), Feedback.timestamp.desc()
            )
        elif sort_order == "rating_low":
            query = query.order_by(
                Feedback.overall_rating.asc(), Feedback.timestamp.desc()
            )
        else:  # newest (default)
            query = query.order_by(Feedback.timestamp.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify(
            {
                "feedback": [f.to_dict() for f in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page,
                "per_page": per_page,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            }
        )

    except Exception as e:
        print(f"Error getting feedback: {e}")
        return jsonify({"error": "Error loading feedback"}), 500


@dashboard_bp.route("/api/feedback/<int:feedback_id>", methods=["GET"])
@login_required
def get_single_feedback(feedback_id):
    """Get single feedback entry details"""
    feedback = Feedback.query.filter_by(
        id=feedback_id, business_id=current_user.id
    ).first()

    if not feedback:
        return jsonify({"error": "Feedback not found"}), 404

    return jsonify(feedback.to_dict())


@dashboard_bp.route("/api/feedback/<int:feedback_id>/review", methods=["POST"])
@login_required
def mark_reviewed(feedback_id):
    """Toggle feedback reviewed status"""
    try:
        feedback = Feedback.query.filter_by(
            id=feedback_id, business_id=current_user.id
        ).first()

        if not feedback:
            return jsonify({"error": "Feedback not found"}), 404

        feedback.reviewed = not feedback.reviewed
        db.session.commit()

        return jsonify(
            {"success": True, "reviewed": feedback.reviewed, "feedback_id": feedback.id}
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error marking feedback as reviewed: {e}")
        return jsonify({"error": "Error updating feedback"}), 500


@dashboard_bp.route("/api/feedback/<int:feedback_id>", methods=["DELETE"])
@login_required
def delete_feedback(feedback_id):
    """Delete a feedback entry"""
    try:
        feedback = Feedback.query.filter_by(
            id=feedback_id, business_id=current_user.id
        ).first()

        if not feedback:
            return jsonify({"error": "Feedback not found"}), 404

        db.session.delete(feedback)
        db.session.commit()

        return jsonify({"success": True, "message": "Feedback deleted successfully"})

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting feedback: {e}")
        return jsonify({"error": "Error deleting feedback"}), 500


@dashboard_bp.route("/api/export")
@login_required
def export_feedback():
    """
    Export feedback to CSV

    Query params:
    - format: csv (default) or json
    - period: all, today, week, month
    """
    try:
        period = request.args.get("period", "all")
        export_format = request.args.get("format", "csv")

        # Build query based on period
        query = Feedback.query.filter_by(business_id=current_user.id)

        if period == "today":
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            query = query.filter(Feedback.timestamp >= today_start)
        elif period == "week":
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(Feedback.timestamp >= week_ago)
        elif period == "month":
            month_ago = datetime.utcnow() - timedelta(days=30)
            query = query.filter(Feedback.timestamp >= month_ago)

        feedback_list = query.order_by(Feedback.timestamp.desc()).all()

        if export_format == "json":
            return jsonify(
                {
                    "feedback": [f.to_dict() for f in feedback_list],
                    "total": len(feedback_list),
                    "exported_at": datetime.utcnow().isoformat(),
                }
            )

        # CSV export
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "ID",
                "Date",
                "Time",
                "Overall Rating",
                "Food",
                "Service",
                "Staff",
                "Cleanliness",
                "Value",
                "NPS Score",
                "Comment",
                "Reviewed",
            ]
        )

        # Write data
        for f in feedback_list:
            writer.writerow(
                [
                    f.id,
                    f.timestamp.strftime("%Y-%m-%d"),
                    f.timestamp.strftime("%H:%M:%S"),
                    f.overall_rating,
                    f.food_rating or "",
                    f.service_rating or "",
                    f.staff_rating or "",
                    f.cleanliness_rating or "",
                    f.value_rating or "",
                    f.nps_score if f.nps_score is not None else "",
                    f.comment or "",
                    "Yes" if f.reviewed else "No",
                ]
            )

        # Create BytesIO object
        output.seek(0)
        bytes_output = BytesIO()
        bytes_output.write(
            output.getvalue().encode("utf-8-sig")
        )  # UTF-8 with BOM for Excel
        bytes_output.seek(0)

        filename = (
            f'feedback_{period}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )

        return send_file(
            bytes_output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        print(f"Error exporting feedback: {e}")
        return jsonify({"error": "Error exporting feedback"}), 500


@dashboard_bp.route("/api/qrcode")
@login_required
def generate_qr():
    """Generate QR code for feedback URL"""
    try:
        # Get feedback URL (homepage)
        feedback_url = request.url_root.rstrip("/")

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(feedback_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype="image/png",
            as_attachment=True,
            download_name=f'{current_user.name.lower().replace(" ", "_")}_feedback_qr.png',
        )

    except Exception as e:
        print(f"Error generating QR code: {e}")
        return jsonify({"error": "Error generating QR code"}), 500


@dashboard_bp.route("/api/summary")
@login_required
def get_summary():
    """Get summary statistics for various time periods"""
    try:
        now = datetime.utcnow()

        def get_period_stats(start_date):
            feedback_list = Feedback.query.filter(
                Feedback.business_id == current_user.id,
                Feedback.timestamp >= start_date,
            ).all()

            if not feedback_list:
                return {"count": 0, "avg_rating": 0, "happy": 0, "neutral": 0, "sad": 0}

            ratings = [f.overall_rating for f in feedback_list]
            return {
                "count": len(feedback_list),
                "avg_rating": round(sum(ratings) / len(ratings), 2),
                "happy": ratings.count(3),
                "neutral": ratings.count(2),
                "sad": ratings.count(1),
            }

        return jsonify(
            {
                "today": get_period_stats(
                    now.replace(hour=0, minute=0, second=0, microsecond=0)
                ),
                "yesterday": get_period_stats(
                    (now - timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                ),
                "this_week": get_period_stats(now - timedelta(days=7)),
                "this_month": get_period_stats(now - timedelta(days=30)),
                "all_time": get_period_stats(datetime(2020, 1, 1)),
            }
        )

    except Exception as e:
        print(f"Error getting summary: {e}")
        return jsonify({"error": "Error loading summary"}), 500
