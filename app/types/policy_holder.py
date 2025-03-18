# app/types/policy_holder.py
from database import db
import datetime

class PolicyHolder(db.Model):
    __tablename__ = 'POLICY_HOLDER'
    __table_args__ = {'schema': 'base'}

    USER_CODE = db.Column(db.String(20), primary_key=True)
    USER_NAME = db.Column(db.String(500), nullable=False)
    UUID = db.Column(db.String(100), nullable=False)
    USER_EMAIL = db.Column(db.String(100), unique=True, nullable=False)
    USER_ADDRESS = db.Column(db.String(500))
    USER_PASSWORD_HASH = db.Column(db.String(500), nullable=False)
    USER_IMAGE_PATH = db.Column(db.String(500))  # Added to store the image URL
    USER_MOBILE = db.Column(db.String(100))
    USER_STATUS = db.Column(db.String(1), nullable=False)
    POLICY_ID = db.Column(db.String(1), nullable=False)
    CREATED_USER_CODE = db.Column(db.String(20))
    CREATED_DATE = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    LAST_MOD_USER_CODE = db.Column(db.String(20))
    LAST_MOD_DATE = db.Column(db.DateTime)
