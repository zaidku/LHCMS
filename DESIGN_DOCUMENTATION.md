# LHCMS Design Documentation

## System Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile App     │    │   Lab Portal    │
│   (React/Vue)   │    │   (Flutter)     │    │   (Angular)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   API Gateway   │
                        │  (Rate Limiting, │
                        │   Validation)    │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │     LHCMS       │
                        │  (Flask-RESTX)  │
                        └────────┬────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
     ┌────▼────┐        ┌────────▼────────┐    ┌────────▼────────┐
     │   UMS   │        │   PostgreSQL    │    │   Redis Cache   │
     │(Auth/   │        │   (Primary DB)  │    │  (Sessions/     │
     │Users)   │        │                 │    │   Cache)        │
     └─────────┘        └─────────────────┘    └─────────────────┘
```

### Microservices Architecture
- **LHCMS**: Case management and business logic
- **UMS**: User authentication and authorization
- **Notification Service**: Email/SMS notifications (future)
- **File Storage Service**: Document and image management (future)
- **Analytics Service**: Reporting and business intelligence (future)

## Data Model Design

### Core Entities

#### Laboratory Entity
```python
class Laboratory(db.Model):
    """
    Represents a dental laboratory organization
    Multi-tenant root entity for data isolation
    """
    __tablename__ = 'laboratories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    license_number = db.Column(db.String(100), unique=True)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    
    # Compliance and business info
    hipaa_covered_entity = db.Column(db.Boolean, default=True)
    business_license_expiry = db.Column(db.Date)
    insurance_policy_number = db.Column(db.String(100))
    
    # Relationships
    cases = db.relationship('Case', backref='laboratory', lazy='dynamic')
    users = db.relationship('User', secondary='lab_users', backref='laboratories')
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
```

#### Case Entity - Comprehensive Design
```python
class Case(db.Model):
    """
    Central entity representing a dental case
    Contains all case lifecycle information
    """
    __tablename__ = 'cases'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('laboratories.id'), nullable=False)
    
    # Patient information (PHI - encrypted)
    patient_name = db.Column(db.String(255), nullable=False)  # Encrypted
    patient_dob = db.Column(db.Date)  # Encrypted
    patient_gender = db.Column(db.Enum('M', 'F', 'O', name='gender_enum'))
    patient_insurance = db.Column(db.String(100))  # Encrypted
    
    # Dental provider information
    dentist_name = db.Column(db.String(255), nullable=False)
    dentist_license = db.Column(db.String(100))
    practice_name = db.Column(db.String(255))
    practice_address = db.Column(db.Text)
    
    # Case details
    procedure_type = db.Column(db.String(100), nullable=False)
    tooth_numbers = db.Column(db.JSON)  # Array of tooth numbers
    material_type = db.Column(db.String(100))
    shade = db.Column(db.String(50))
    due_date = db.Column(db.Date)
    rush_order = db.Column(db.Boolean, default=False)
    
    # Case workflow
    status = db.Column(db.Enum(
        'received', 'in_progress', 'quality_check', 
        'completed', 'shipped', 'delivered', 
        'returned', 'cancelled',
        name='case_status_enum'
    ), default='received')
    
    priority = db.Column(db.Enum(
        'low', 'normal', 'high', 'urgent',
        name='priority_enum'
    ), default='normal')
    
    # Instructions and notes
    special_instructions = db.Column(db.Text)
    lab_notes = db.Column(db.Text)
    quality_notes = db.Column(db.Text)
    
    # Financial
    estimated_cost = db.Column(db.Decimal(10, 2))
    final_cost = db.Column(db.Decimal(10, 2))
    payment_status = db.Column(db.Enum(
        'pending', 'partial', 'paid', 'overdue',
        name='payment_status_enum'
    ), default='pending')
    
    # Relationships
    lab_id = db.Column(db.Integer, db.ForeignKey('laboratories.id'), nullable=False)
    assigned_technician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    quality_inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Audit and compliance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deleted_at = db.Column(db.DateTime)  # Soft delete for compliance
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_case_lab_status', 'lab_id', 'status'),
        db.Index('idx_case_due_date', 'due_date'),
        db.Index('idx_case_created', 'created_at'),
        db.Index('idx_case_number', 'case_number'),
    )
```

#### Case Workflow State Machine
```python
class CaseWorkflow:
    """
    Manages case status transitions and business rules
    """
    VALID_TRANSITIONS = {
        'received': ['in_progress', 'cancelled'],
        'in_progress': ['quality_check', 'returned', 'cancelled'],
        'quality_check': ['completed', 'in_progress', 'returned'],
        'completed': ['shipped', 'returned'],
        'shipped': ['delivered', 'returned'],
        'delivered': [],  # Terminal state
        'returned': ['in_progress', 'cancelled'],
        'cancelled': []   # Terminal state
    }
    
    @classmethod
    def can_transition(cls, from_status, to_status):
        """Check if status transition is valid"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])
    
    @classmethod
    def get_next_states(cls, current_status):
        """Get valid next states for current status"""
        return cls.VALID_TRANSITIONS.get(current_status, [])
```

## Case Creation Workflow

### 1. Case Intake Process
```python
class CaseCreationService:
    """
    Handles the complete case creation workflow
    Implements business rules and validation
    """
    
    def __init__(self, lab_id, created_by_id):
        self.lab_id = lab_id
        self.created_by_id = created_by_id
        self.validation_errors = []
    
    def create_case(self, case_data):
        """
        Main case creation method with comprehensive validation
        """
        try:
            # Step 1: Validate user permissions
            self._validate_user_permissions()
            
            # Step 2: Validate case data
            validated_data = self._validate_case_data(case_data)
            
            # Step 3: Generate case number
            case_number = self._generate_case_number()
            
            # Step 4: Create case entity
            case = self._create_case_entity(validated_data, case_number)
            
            # Step 5: Initialize workflow
            self._initialize_workflow(case)
            
            # Step 6: Create audit log
            self._log_case_creation(case)
            
            # Step 7: Send notifications
            self._send_notifications(case)
            
            return case
            
        except ValidationError as e:
            self._log_validation_error(e)
            raise
        except Exception as e:
            self._log_system_error(e)
            raise
```

### 2. Case Data Validation
```python
def _validate_case_data(self, case_data):
    """
    Comprehensive case data validation with business rules
    """
    validator = CaseDataValidator()
    
    # Required field validation
    required_fields = [
        'patient_name', 'dentist_name', 'procedure_type',
        'due_date', 'tooth_numbers'
    ]
    
    for field in required_fields:
        if not case_data.get(field):
            raise ValidationError(f"Required field missing: {field}")
    
    # Business rule validation
    validated_data = {}
    
    # Patient name validation (PHI handling)
    validated_data['patient_name'] = validator.validate_patient_name(
        case_data['patient_name']
    )
    
    # Dentist validation
    validated_data['dentist_name'] = validator.validate_dentist_name(
        case_data['dentist_name']
    )
    
    # Procedure type validation
    validated_data['procedure_type'] = validator.validate_procedure_type(
        case_data['procedure_type']
    )
    
    # Due date validation (business days only, minimum lead time)
    validated_data['due_date'] = validator.validate_due_date(
        case_data['due_date'],
        procedure_type=validated_data['procedure_type'],
        rush_order=case_data.get('rush_order', False)
    )
    
    # Tooth number validation (dental numbering system)
    validated_data['tooth_numbers'] = validator.validate_tooth_numbers(
        case_data['tooth_numbers']
    )
    
    return validated_data

class CaseDataValidator:
    """Specific validation logic for case data"""
    
    VALID_PROCEDURE_TYPES = [
        'crown', 'bridge', 'implant_crown', 'partial_denture',
        'full_denture', 'inlay', 'onlay', 'veneer'
    ]
    
    MINIMUM_LEAD_TIMES = {
        'crown': 5,          # 5 business days
        'bridge': 7,         # 7 business days
        'implant_crown': 10, # 10 business days
        'partial_denture': 14,
        'full_denture': 21,
        'inlay': 3,
        'onlay': 3,
        'veneer': 7
    }
    
    def validate_procedure_type(self, procedure_type):
        if procedure_type.lower() not in self.VALID_PROCEDURE_TYPES:
            raise ValidationError(f"Invalid procedure type: {procedure_type}")
        return procedure_type.lower()
    
    def validate_due_date(self, due_date_str, procedure_type, rush_order=False):
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # Calculate business days between now and due date
        business_days = self._count_business_days(today, due_date)
        
        # Get minimum lead time for procedure
        min_lead_time = self.MINIMUM_LEAD_TIMES.get(procedure_type, 5)
        
        # Rush orders can reduce lead time by 50%
        if rush_order:
            min_lead_time = max(1, min_lead_time // 2)
        
        if business_days < min_lead_time:
            raise ValidationError(
                f"Due date too soon. Minimum {min_lead_time} business days required for {procedure_type}"
            )
        
        return due_date
    
    def validate_tooth_numbers(self, tooth_numbers):
        """Validate using Universal Numbering System (1-32)"""
        if not isinstance(tooth_numbers, list) or not tooth_numbers:
            raise ValidationError("At least one tooth number required")
        
        valid_numbers = set(range(1, 33))  # 1-32 for adult teeth
        
        for tooth in tooth_numbers:
            if tooth not in valid_numbers:
                raise ValidationError(f"Invalid tooth number: {tooth}")
        
        return sorted(list(set(tooth_numbers)))  # Remove duplicates, sort
```

### 3. Case Number Generation
```python
def _generate_case_number(self):
    """
    Generate unique case number with lab prefix and sequential number
    Format: {LAB_CODE}{YEAR}{MONTH}{SEQUENCE}
    Example: GLW202411001
    """
    lab = Laboratory.query.get(self.lab_id)
    lab_code = lab.code or f"LAB{lab.id:03d}"
    
    current_date = datetime.now()
    year_month = current_date.strftime("%Y%m")
    
    # Get next sequence number for this lab and month
    last_case = Case.query.filter(
        Case.lab_id == self.lab_id,
        Case.case_number.like(f"{lab_code}{year_month}%")
    ).order_by(Case.case_number.desc()).first()
    
    if last_case:
        last_sequence = int(last_case.case_number[-3:])
        next_sequence = last_sequence + 1
    else:
        next_sequence = 1
    
    case_number = f"{lab_code}{year_month}{next_sequence:03d}"
    
    # Ensure uniqueness (handle race conditions)
    while Case.query.filter_by(case_number=case_number).first():
        next_sequence += 1
        case_number = f"{lab_code}{year_month}{next_sequence:03d}"
    
    return case_number
```

## Business Logic Implementation

### Case Assignment Algorithm
```python
class CaseAssignmentService:
    """
    Intelligent case assignment to technicians
    Based on workload, skills, and availability
    """
    
    def assign_case(self, case_id):
        case = Case.query.get(case_id)
        if not case:
            raise ValueError("Case not found")
        
        # Get eligible technicians
        eligible_technicians = self._get_eligible_technicians(case)
        
        # Score technicians based on multiple factors
        scored_technicians = self._score_technicians(eligible_technicians, case)
        
        # Assign to best match
        if scored_technicians:
            best_technician = scored_technicians[0]
            case.assigned_technician_id = best_technician['technician_id']
            db.session.commit()
            
            # Log assignment
            self._log_assignment(case, best_technician)
            
            return best_technician['technician_id']
        
        return None
    
    def _score_technicians(self, technicians, case):
        """Score technicians based on various factors"""
        scored = []
        
        for tech in technicians:
            score = 0
            
            # Skill match (40% weight)
            skill_score = self._calculate_skill_score(tech, case)
            score += skill_score * 0.4
            
            # Workload balance (30% weight)
            workload_score = self._calculate_workload_score(tech)
            score += workload_score * 0.3
            
            # Historical performance (20% weight)
            performance_score = self._calculate_performance_score(tech, case)
            score += performance_score * 0.2
            
            # Availability (10% weight)
            availability_score = self._calculate_availability_score(tech, case)
            score += availability_score * 0.1
            
            scored.append({
                'technician_id': tech.id,
                'score': score,
                'breakdown': {
                    'skill': skill_score,
                    'workload': workload_score,
                    'performance': performance_score,
                    'availability': availability_score
                }
            })
        
        return sorted(scored, key=lambda x: x['score'], reverse=True)
```

### Quality Control Process
```python
class QualityControlService:
    """
    Manages quality control workflow and standards
    """
    
    QUALITY_CHECKPOINTS = {
        'crown': [
            'margin_adaptation',
            'occlusal_contacts',
            'shade_match',
            'surface_finish',
            'anatomical_form'
        ],
        'bridge': [
            'margin_adaptation',
            'occlusal_contacts',
            'shade_match',
            'surface_finish',
            'connector_strength',
            'pontic_design'
        ]
    }
    
    def initiate_quality_check(self, case_id, inspector_id):
        """Start quality control process for a case"""
        case = Case.query.get(case_id)
        if case.status != 'completed':
            raise ValueError("Case must be completed before quality check")
        
        # Create quality check record
        qc_record = QualityCheck(
            case_id=case_id,
            inspector_id=inspector_id,
            checkpoints=self.QUALITY_CHECKPOINTS.get(case.procedure_type, []),
            status='in_progress',
            created_at=datetime.utcnow()
        )
        
        db.session.add(qc_record)
        case.status = 'quality_check'
        case.quality_inspector_id = inspector_id
        
        db.session.commit()
        
        return qc_record
    
    def complete_quality_check(self, qc_id, results):
        """Complete quality check with pass/fail results"""
        qc_record = QualityCheck.query.get(qc_id)
        case = qc_record.case
        
        # Validate all checkpoints completed
        for checkpoint in qc_record.checkpoints:
            if checkpoint not in results:
                raise ValueError(f"Missing checkpoint result: {checkpoint}")
        
        # Calculate overall result
        passed_count = sum(1 for result in results.values() if result['passed'])
        total_count = len(results)
        pass_rate = passed_count / total_count
        
        qc_record.results = results
        qc_record.pass_rate = pass_rate
        qc_record.completed_at = datetime.utcnow()
        
        if pass_rate >= 0.9:  # 90% pass rate required
            qc_record.status = 'passed'
            case.status = 'completed'
        else:
            qc_record.status = 'failed'
            case.status = 'in_progress'  # Return to production
            
            # Create rework task
            self._create_rework_task(case, results)
        
        db.session.commit()
        
        return qc_record
```

## API Design Patterns

### RESTful Endpoint Structure
```python
# Cases API with full CRUD operations
@api.route('/cases')
class CaseListAPI(Resource):
    @api.doc('list_cases')
    @api.marshal_list_with(case_model)
    @require_auth
    @require_lab_access
    def get(self):
        """Retrieve cases for authenticated user's labs"""
        user_labs = get_user_lab_ids(current_user.id)
        
        # Build query with filters
        query = Case.query.filter(Case.lab_id.in_(user_labs))
        
        # Apply filters
        if request.args.get('status'):
            query = query.filter(Case.status == request.args.get('status'))
        
        if request.args.get('procedure_type'):
            query = query.filter(Case.procedure_type == request.args.get('procedure_type'))
        
        if request.args.get('due_date_from'):
            due_date_from = datetime.strptime(request.args.get('due_date_from'), '%Y-%m-%d').date()
            query = query.filter(Case.due_date >= due_date_from)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        pagination = query.paginate(page=page, per_page=per_page)
        
        return {
            'cases': [case.to_dict() for case in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    
    @api.doc('create_case')
    @api.expect(case_input_model)
    @api.marshal_with(case_model, code=201)
    @require_auth
    @require_permissions(['create_case'])
    def post(self):
        """Create a new case"""
        try:
            # Get user's primary lab
            user_lab_id = get_user_primary_lab_id(current_user.id)
            
            # Create case using service
            case_service = CaseCreationService(user_lab_id, current_user.id)
            case = case_service.create_case(api.payload)
            
            # Return created case
            return case.to_dict(), 201
            
        except ValidationError as e:
            api.abort(400, str(e))
        except Exception as e:
            api.abort(500, "Internal server error")

@api.route('/cases/<int:case_id>')
class CaseAPI(Resource):
    @api.doc('get_case')
    @api.marshal_with(case_model)
    @require_auth
    @require_case_access
    def get(self, case_id):
        """Get case details"""
        case = Case.query.get_or_404(case_id)
        return case.to_dict()
    
    @api.doc('update_case')
    @api.expect(case_update_model)
    @api.marshal_with(case_model)
    @require_auth
    @require_case_access
    @require_permissions(['update_case'])
    def put(self, case_id):
        """Update case"""
        case = Case.query.get_or_404(case_id)
        
        # Validate status transitions
        if 'status' in api.payload:
            new_status = api.payload['status']
            if not CaseWorkflow.can_transition(case.status, new_status):
                api.abort(400, f"Invalid status transition from {case.status} to {new_status}")
        
        # Update case fields
        updatable_fields = ['status', 'special_instructions', 'lab_notes', 'due_date']
        for field in updatable_fields:
            if field in api.payload:
                setattr(case, field, api.payload[field])
        
        case.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log the update
        audit_log.log_case_update(case_id, current_user.id, api.payload)
        
        return case.to_dict()
```

### Advanced Query Patterns
```python
class CaseQueryService:
    """Advanced querying capabilities for cases"""
    
    @staticmethod
    def search_cases(search_params):
        """Complex case search with multiple criteria"""
        query = Case.query
        
        # Full-text search on patient name, case number, dentist
        if search_params.get('q'):
            search_term = f"%{search_params['q']}%"
            query = query.filter(
                db.or_(
                    Case.patient_name.ilike(search_term),
                    Case.case_number.ilike(search_term),
                    Case.dentist_name.ilike(search_term)
                )
            )
        
        # Date range filters
        if search_params.get('created_after'):
            query = query.filter(Case.created_at >= search_params['created_after'])
        
        if search_params.get('due_before'):
            query = query.filter(Case.due_date <= search_params['due_before'])
        
        # Status filters (multiple)
        if search_params.get('statuses'):
            query = query.filter(Case.status.in_(search_params['statuses']))
        
        # Priority filter
        if search_params.get('priority'):
            query = query.filter(Case.priority == search_params['priority'])
        
        # Lab filter (for admin users)
        if search_params.get('lab_ids'):
            query = query.filter(Case.lab_id.in_(search_params['lab_ids']))
        
        # Sorting
        sort_by = search_params.get('sort_by', 'created_at')
        sort_order = search_params.get('sort_order', 'desc')
        
        if hasattr(Case, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(Case, sort_by).desc())
            else:
                query = query.order_by(getattr(Case, sort_by).asc())
        
        return query
```

## Performance Optimization

### Database Optimization
```python
# Efficient queries with proper joins
def get_cases_with_details(lab_ids, limit=50):
    """Optimized query to get cases with related data"""
    return db.session.query(Case)\
        .options(
            joinedload(Case.assigned_technician),
            joinedload(Case.quality_inspector),
            joinedload(Case.laboratory)
        )\
        .filter(Case.lab_id.in_(lab_ids))\
        .filter(Case.deleted_at.is_(None))\
        .order_by(Case.created_at.desc())\
        .limit(limit)\
        .all()

# Database indexes for common queries
class Case(db.Model):
    __table_args__ = (
        # Composite indexes for common query patterns
        db.Index('idx_case_lab_status_created', 'lab_id', 'status', 'created_at'),
        db.Index('idx_case_due_date_priority', 'due_date', 'priority'),
        db.Index('idx_case_technician_status', 'assigned_technician_id', 'status'),
        
        # Full-text search indexes (PostgreSQL)
        db.Index('idx_case_search', 'patient_name', 'dentist_name', 'case_number',
                 postgresql_using='gin'),
    )
```

### Caching Strategy
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@cache.memoize(timeout=300)
def get_case_statistics(lab_id):
    """Cached case statistics for dashboard"""
    return {
        'total_cases': Case.query.filter_by(lab_id=lab_id).count(),
        'active_cases': Case.query.filter_by(lab_id=lab_id, status='in_progress').count(),
        'overdue_cases': Case.query.filter(
            Case.lab_id == lab_id,
            Case.due_date < datetime.now().date(),
            Case.status.in_(['received', 'in_progress', 'quality_check'])
        ).count()
    }

# Cache invalidation on case updates
def invalidate_case_cache(lab_id):
    cache.delete_memoized(get_case_statistics, lab_id)
```

## Error Handling and Logging

### Structured Error Responses
```python
class APIError(Exception):
    """Base API error class"""
    status_code = 500
    message = "Internal server error"
    error_code = "INTERNAL_ERROR"
    
    def __init__(self, message=None, status_code=None, error_code=None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code

class ValidationError(APIError):
    status_code = 400
    error_code = "VALIDATION_ERROR"

class CaseNotFoundError(APIError):
    status_code = 404
    error_code = "CASE_NOT_FOUND"
    message = "Case not found"

class UnauthorizedError(APIError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required"

@app.errorhandler(APIError)
def handle_api_error(error):
    response = {
        'error': {
            'code': error.error_code,
            'message': error.message,
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    return jsonify(response), error.status_code
```

### Comprehensive Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def log_case_creation(case_id, user_id, lab_id):
    """Log case creation with structured data"""
    logger.info(
        "case_created",
        case_id=case_id,
        user_id=user_id,
        lab_id=lab_id,
        action="create_case",
        timestamp=datetime.utcnow().isoformat()
    )

def log_case_status_change(case_id, old_status, new_status, user_id):
    """Log case status changes for audit trail"""
    logger.info(
        "case_status_changed",
        case_id=case_id,
        old_status=old_status,
        new_status=new_status,
        user_id=user_id,
        action="update_case_status",
        timestamp=datetime.utcnow().isoformat()
    )
```

This comprehensive design documentation covers the complete system architecture, data models, business logic, and implementation patterns. It provides the detailed design-level information needed to understand how to create cases, manage workflows, and implement the various features of the LHCMS system.