from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploads = db.relationship('Upload', backref='user', lazy=True)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    encoding = db.Column(db.String(20), default='utf-8')
    file_size = db.Column(db.Integer)  # Size in bytes
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'upload_date': self.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'encoding': self.encoding,
            'file_size': self.file_size
        }

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # e.g., 'customer_segmentation', 'sales_forecast'
    parameters = db.Column(db.Text)  # JSON string of parameters used
    result_path = db.Column(db.String(255))  # Path to results file if applicable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    upload = db.relationship('Upload', backref=db.backref('analyses', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'upload_id': self.upload_id,
            'analysis_type': self.analysis_type,
            'parameters': self.parameters,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
