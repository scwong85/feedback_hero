from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


class Business(UserMixin, db.Model):
    __tablename__ = "business"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    settings_json = db.Column(db.Text, default="{}")

    # Relationship
    feedback = db.relationship(
        "Feedback", backref="business", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_settings(self):
        try:
            return json.loads(self.settings_json)
        except:
            return {}

    def set_settings(self, settings_dict):
        self.settings_json = json.dumps(settings_dict)


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("business.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Ratings
    overall_rating = db.Column(db.Integer, nullable=False)  # 1=sad, 2=neutral, 3=happy
    food_rating = db.Column(db.Integer)  # 1-5
    service_rating = db.Column(db.Integer)  # 1-5
    staff_rating = db.Column(db.Integer)  # 1-5
    cleanliness_rating = db.Column(db.Integer)  # 1-5
    value_rating = db.Column(db.Integer)  # 1-5
    nps_score = db.Column(db.Integer)  # 0-10

    # Optional text feedback
    comment = db.Column(db.Text)

    # Management
    reviewed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "overall_rating": self.overall_rating,
            "food_rating": self.food_rating,
            "service_rating": self.service_rating,
            "staff_rating": self.staff_rating,
            "cleanliness_rating": self.cleanliness_rating,
            "value_rating": self.value_rating,
            "nps_score": self.nps_score,
            "comment": self.comment,
            "reviewed": self.reviewed,
        }
