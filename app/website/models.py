from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from . import db

class File(db.Model):
    # Define the table name (optional, SQLAlchemy will automatically name it "file" if not specified)
    __tablename__ = 'files'
    
    # Define the columns
    id = db.Column(db.Integer, primary_key=True)  # Adding a primary key field (automatically created in Django)
    created = db.Column(db.DateTime, default=datetime.utcnow)  # Using a default function for auto_now_add
    modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # auto_now
    filename = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    hash = db.Column(db.String(64), nullable=False)
    
    # Define choices
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    STATUS_CHOICES = [
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]
    
    # Status field with choices
    status = db.Column(db.String(20), default=IN_PROGRESS, nullable=False)

    def __init__(self, filename, location, hash, status=IN_PROGRESS):
        self.filename = filename
        self.location = location
        self.hash = hash
        self.status = status

    def __repr__(self):
        return f"<File {self.filename}>"
