from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    
    with app.app_context():
        # Import all models to ensure they are registered
        from models.case import Case
        
        # Create all tables
        db.create_all()
        
def get_db():
    """Get database instance."""
    return db

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)