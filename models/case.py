from db import db, TimestampMixin
from sqlalchemy import Enum
import enum

class CaseStatus(enum.Enum):
    """Enumeration for case status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class Case(db.Model, TimestampMixin):
    """Case model for storing case information."""
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.String(50), nullable=False, index=True)
    doctor_id = db.Column(db.String(50), nullable=False, index=True)
    product_id = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(Enum(CaseStatus), nullable=False, default=CaseStatus.PENDING)
    
    # Basic case information
    case_name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Metadata
    created_by = db.Column(db.String(50), nullable=True)
    assigned_to = db.Column(db.String(50), nullable=True)
    
    # Dental-specific fields
    case_type = db.Column(db.String(50), nullable=True)  # fixed_prosthetic, denture, night_guard, implant, etc.
    due_date = db.Column(db.Date, nullable=True)
    rush_order = db.Column(db.Boolean, default=False)
    special_instructions = db.Column(db.Text, nullable=True)
    
    # Patient information (stored as JSON)
    patient_info = db.Column(db.JSON, nullable=True)
    
    # Dental product details (stored as JSON for flexibility)
    fixed_prosthetic_details = db.Column(db.JSON, nullable=True)
    denture_details = db.Column(db.JSON, nullable=True)
    night_guard_details = db.Column(db.JSON, nullable=True)
    implant_details = db.Column(db.JSON, nullable=True)
    
    def __init__(self, lab_id, doctor_id, product_id, status=CaseStatus.PENDING, **kwargs):
        """Initialize a new case."""
        self.lab_id = lab_id
        self.doctor_id = doctor_id
        self.product_id = product_id
        self.status = status
        
        # Set optional fields
        optional_fields = [
            'case_name', 'description', 'priority', 'created_by', 'assigned_to',
            'case_type', 'due_date', 'rush_order', 'special_instructions', 'patient_info'
        ]
        
        for field in optional_fields:
            if field in kwargs:
                if field == 'due_date' and isinstance(kwargs[field], str):
                    # Convert string date to date object
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(kwargs[field], '%Y-%m-%d').date()
                        setattr(self, field, date_obj)
                    except ValueError:
                        pass  # Skip invalid date formats
                else:
                    setattr(self, field, kwargs[field])
        
        # Handle dental-specific details
        dental_detail_mapping = {
            'fixed_prosthetic': 'fixed_prosthetic_details',
            'denture': 'denture_details',
            'night_guard': 'night_guard_details',
            'implant': 'implant_details'
        }
        
        for api_field, db_field in dental_detail_mapping.items():
            if api_field in kwargs and kwargs[api_field]:
                setattr(self, db_field, kwargs[api_field])
    
    def to_dict(self):
        """Convert case to dictionary representation."""
        return {
            'id': self.id,
            'lab_id': self.lab_id,
            'doctor_id': self.doctor_id,
            'product_id': self.product_id,
            'status': self.status.value if self.status else None,
            'case_name': self.case_name,
            'description': self.description,
            'priority': self.priority,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'case_type': self.case_type,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'rush_order': self.rush_order,
            'special_instructions': self.special_instructions,
            'patient_info': self.patient_info,
            'fixed_prosthetic': self.fixed_prosthetic_details,
            'denture': self.denture_details,
            'night_guard': self.night_guard_details,
            'implant': self.implant_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_from_dict(self, data):
        """Update case from dictionary data."""
        updatable_fields = [
            'case_name', 'description', 'priority', 'status', 'assigned_to',
            'case_type', 'due_date', 'rush_order', 'special_instructions',
            'patient_info'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'status' and isinstance(data[field], str):
                    # Convert string status to enum
                    try:
                        setattr(self, field, CaseStatus(data[field]))
                    except ValueError:
                        continue  # Skip invalid status values
                elif field == 'due_date' and isinstance(data[field], str):
                    # Convert string date to date object
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(data[field], '%Y-%m-%d').date()
                        setattr(self, field, date_obj)
                    except ValueError:
                        continue  # Skip invalid date formats
                else:
                    setattr(self, field, data[field])
        
        # Handle dental-specific details
        dental_detail_fields = {
            'fixed_prosthetic': 'fixed_prosthetic_details',
            'denture': 'denture_details',
            'night_guard': 'night_guard_details',
            'implant': 'implant_details'
        }
        
        for api_field, db_field in dental_detail_fields.items():
            if api_field in data and data[api_field]:
                setattr(self, db_field, data[api_field])
    
    def __repr__(self):
        """String representation of the case."""
        return f'<Case {self.id}: Lab={self.lab_id}, Doctor={self.doctor_id}, Status={self.status.value if self.status else None}>'