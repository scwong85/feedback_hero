from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Business

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Business login page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.overview"))  # FIXED: was 'dashboard'

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember", False)

        if not email or not password:
            flash("Please provide both email and password", "error")
            return render_template("dashboard/login.html")

        business = Business.query.filter_by(email=email).first()

        if business and business.check_password(password):
            login_user(business, remember=bool(remember))

            # Redirect to next page or dashboard
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.overview"))  # FIXED: was 'dashboard'
        else:
            flash("Invalid email or password", "error")

    return render_template("dashboard/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Logout business user"""
    logout_user()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Optional: Register new business account
    This is disabled by default for single-tenant deployment
    Enable if you want multi-business support
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.overview"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not all([name, email, password, confirm_password]):
            flash("All fields are required", "error")
            return render_template("dashboard/register.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("dashboard/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long", "error")
            return render_template("dashboard/register.html")

        # Check if email already exists
        if Business.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return render_template("dashboard/register.html")

        # Create new business account
        business = Business(name=name, email=email)
        business.set_password(password)

        try:
            db.session.add(business)
            db.session.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash("Error creating account. Please try again.", "error")
            return render_template("dashboard/register.html")

    return render_template("dashboard/register.html")
