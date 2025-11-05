from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from models.case import Case, CaseStatus
from utils.auth import require_auth, get_current_user, get_user_lab_id
from services.ums_client import UMSClient
from services.linkshub_client import LinksHubClient
from db import db
import logging

logger = logging.getLogger(__name__)

# Create namespace for case routes with versioning
api = Namespace('cases', description='Case Management API v1.0', version='1.0')

# API Response Models
error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error type'),
    'message': fields.String(required=True, description='Error message'),
    'code': fields.Integer(description='Error code'),
    'timestamp': fields.DateTime(description='Error timestamp')
})

success_model = api.model('Success', {
    'message': fields.String(required=True, description='Success message'),
    'data': fields.Raw(description='Response data')
})

pagination_model = api.model('Pagination', {
    'page': fields.Integer(required=True, description='Current page number'),
    'per_page': fields.Integer(required=True, description='Items per page'),
    'total': fields.Integer(required=True, description='Total number of items'),
    'pages': fields.Integer(required=True, description='Total number of pages'),
    'has_prev': fields.Boolean(description='Has previous page'),
    'has_next': fields.Boolean(description='Has next page')
})

# Define API models for documentation

# Doctor Account Model
doctor_account_model = api.model('DoctorAccount', {
    'doctor_id': fields.String(required=True, description='Unique doctor identifier'),
    'first_name': fields.String(required=True, description='Doctor first name'),
    'last_name': fields.String(required=True, description='Doctor last name'),
    'email': fields.String(required=True, description='Doctor email address'),
    'phone': fields.String(description='Doctor phone number'),
    'practice_name': fields.String(description='Name of dental practice'),
    'license_number': fields.String(description='Dental license number'),
    'specialty': fields.String(description='Dental specialty', enum=[
        'general_dentistry', 'orthodontics', 'prosthodontics', 'oral_surgery',
        'periodontics', 'endodontics', 'pediatric_dentistry', 'cosmetic_dentistry'
    ]),
    'address': fields.Nested(api.model('Address', {
        'street': fields.String(description='Street address'),
        'city': fields.String(description='City'),
        'state': fields.String(description='State/Province'),
        'zip_code': fields.String(description='ZIP/Postal code'),
        'country': fields.String(description='Country')
    })),
    'lab_relations': fields.List(fields.String, description='List of associated lab IDs'),
    'created_at': fields.DateTime(readonly=True, description='Account creation date'),
    'is_active': fields.Boolean(description='Account status')
})

# Shade Information Model
shade_model = api.model('Shade', {
    'shade_id': fields.String(required=True, description='Shade identifier'),
    'shade_system': fields.String(required=True, description='Shade system used', enum=[
        'vita_classical', 'vita_3d_master', 'ivoclar_chromascop', 'shofu_vintage',
        'dentsply_trubyte', 'custom'
    ]),
    'shade_value': fields.String(required=True, description='Specific shade value (e.g., A1, B2, C3)'),
    'shade_description': fields.String(description='Detailed shade description'),
    'translucency': fields.String(description='Translucency level', enum=[
        'high_translucent', 'low_translucent', 'opaque'
    ]),
    'notes': fields.String(description='Additional shade matching notes')
})

# Dental Product Models
fixed_prosthetic_model = api.model('FixedProsthetic', {
    'type': fields.String(required=True, description='Type of fixed prosthetic', enum=[
        'crown', 'bridge', 'inlay', 'onlay', 'veneer', 'implant_crown'
    ]),
    'material': fields.String(required=True, description='Material used', enum=[
        'porcelain_fused_metal', 'all_ceramic', 'zirconia', 'emax', 'gold',
        'composite', 'pfm_high_noble', 'pfm_noble', 'pfm_base'
    ]),
    'tooth_numbers': fields.List(fields.Integer, required=True, description='Affected tooth numbers'),
    'preparation_type': fields.String(description='Preparation type', enum=[
        'full_coverage', 'partial_coverage', 'minimal_prep', 'no_prep'
    ]),
    'margin_type': fields.String(description='Margin design', enum=[
        'shoulder', 'chamfer', 'knife_edge', 'feather_edge'
    ]),
    'shade': fields.Nested(shade_model, description='Shade information'),
    'occlusion_type': fields.String(description='Occlusion type', enum=[
        'centric_occlusion', 'working_side', 'balancing_side', 'protrusive'
    ])
})

denture_model = api.model('Denture', {
    'type': fields.String(required=True, description='Denture type', enum=[
        'complete_upper', 'complete_lower', 'complete_full', 'partial_upper',
        'partial_lower', 'immediate', 'conventional', 'implant_supported'
    ]),
    'material': fields.String(required=True, description='Base material', enum=[
        'acrylic_resin', 'flexible_nylon', 'metal_framework', 'titanium'
    ]),
    'tooth_material': fields.String(description='Artificial teeth material', enum=[
        'acrylic', 'porcelain', 'composite'
    ]),
    'shade': fields.Nested(shade_model, description='Tooth shade information'),
    'clasp_design': fields.String(description='Clasp design for partials', enum=[
        'cast_clasps', 'wrought_wire', 'precision_attachments', 'none'
    ]),
    'retention_type': fields.String(description='Retention mechanism', enum=[
        'conventional_suction', 'implant_retained', 'implant_supported', 'adhesive'
    ])
})

night_guard_model = api.model('NightGuard', {
    'type': fields.String(required=True, description='Night guard type', enum=[
        'soft_guard', 'hard_guard', 'dual_laminate', 'nti_tss'
    ]),
    'material': fields.String(required=True, description='Material composition', enum=[
        'soft_vinyl', 'hard_acrylic', 'dual_layer', 'thermoplastic'
    ]),
    'thickness': fields.String(description='Material thickness', enum=[
        '1mm', '2mm', '3mm', '4mm', 'custom'
    ]),
    'arch': fields.String(required=True, description='Target arch', enum=[
        'upper', 'lower', 'both'
    ]),
    'design': fields.String(description='Guard design', enum=[
        'full_coverage', 'anterior_only', 'canine_guidance', 'balanced_occlusion'
    ]),
    'special_features': fields.List(fields.String, description='Special features', enum=[
        'bite_ramps', 'tongue_space', 'breathing_holes', 'custom_thickness'
    ])
})

implant_model = api.model('Implant', {
    'implant_system': fields.String(required=True, description='Implant system', enum=[
        'nobel_biocare', 'straumann', 'zimmer_biomet', 'dentsply_sirona',
        'megagen', 'bicon', 'other'
    ]),
    'implant_diameter': fields.String(required=True, description='Implant diameter', enum=[
        '3.0mm', '3.3mm', '3.5mm', '4.0mm', '4.1mm', '4.3mm', '4.5mm', '5.0mm', '6.0mm'
    ]),
    'implant_length': fields.String(required=True, description='Implant length', enum=[
        '6mm', '8mm', '10mm', '11.5mm', '13mm', '15mm', '18mm'
    ]),
    'platform_type': fields.String(description='Platform connection', enum=[
        'external_hex', 'internal_hex', 'internal_tri_channel', 'morse_taper'
    ]),
    'abutment_type': fields.String(description='Abutment type', enum=[
        'stock_abutment', 'custom_abutment', 'angled_abutment', 'temporary_abutment'
    ]),
    'restoration_type': fields.String(description='Final restoration', enum=[
        'single_crown', 'bridge_abutment', 'overdenture_attachment', 'bar_retained'
    ]),
    'tooth_number': fields.Integer(required=True, description='Tooth position number'),
    'tissue_level': fields.String(description='Tissue level', enum=[
        'tissue_level', 'bone_level', 'subcrestal'
    ])
})

# Enhanced Case Model with dental-specific details
case_model = api.model('Case', {
    'id': fields.Integer(readonly=True, description='Case ID'),
    'lab_id': fields.String(required=True, description='Laboratory ID'),
    'doctor_id': fields.String(required=True, description='Doctor ID'),
    'product_id': fields.String(required=True, description='Product ID'),
    'status': fields.String(description='Case status', enum=[s.value for s in CaseStatus]),
    'case_name': fields.String(description='Case name/title'),
    'description': fields.String(description='Case description'),
    'priority': fields.String(description='Case priority', enum=['low', 'medium', 'high']),
    'created_by': fields.String(description='User who created the case'),
    'assigned_to': fields.String(description='User assigned to the case'),
    'patient_info': fields.Nested(api.model('PatientInfo', {
        'patient_id': fields.String(description='Patient identifier'),
        'age': fields.Integer(description='Patient age'),
        'gender': fields.String(description='Patient gender', enum=['male', 'female', 'other']),
        'medical_history': fields.String(description='Relevant medical history')
    }), description='Patient information'),
    'due_date': fields.Date(description='Case due date'),
    'rush_order': fields.Boolean(description='Rush order flag'),
    'special_instructions': fields.String(description='Special fabrication instructions'),
    'fixed_prosthetic': fields.Nested(fixed_prosthetic_model, description='Fixed prosthetic details'),
    'denture': fields.Nested(denture_model, description='Denture details'),
    'night_guard': fields.Nested(night_guard_model, description='Night guard details'),
    'implant': fields.Nested(implant_model, description='Implant details'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp')
})

case_input_model = api.model('CaseInput', {
    'doctor_id': fields.String(required=True, description='Doctor ID'),
    'product_id': fields.String(required=True, description='Product ID'),
    'case_name': fields.String(description='Case name/title'),
    'description': fields.String(description='Case description'),
    'priority': fields.String(description='Case priority', enum=['low', 'medium', 'high']),
    'assigned_to': fields.String(description='User assigned to the case'),
    'patient_info': fields.Nested(api.model('PatientInfoInput', {
        'patient_id': fields.String(description='Patient identifier'),
        'age': fields.Integer(description='Patient age'),
        'gender': fields.String(description='Patient gender', enum=['male', 'female', 'other']),
        'medical_history': fields.String(description='Relevant medical history')
    }), description='Patient information'),
    'due_date': fields.Date(description='Case due date (YYYY-MM-DD)'),
    'rush_order': fields.Boolean(description='Rush order flag'),
    'special_instructions': fields.String(description='Special fabrication instructions'),
    'case_type': fields.String(required=True, description='Type of dental case', enum=[
        'fixed_prosthetic', 'denture', 'night_guard', 'implant', 'orthodontic', 'other'
    ]),
    'fixed_prosthetic': fields.Nested(fixed_prosthetic_model, description='Fixed prosthetic details'),
    'denture': fields.Nested(denture_model, description='Denture details'),
    'night_guard': fields.Nested(night_guard_model, description='Night guard details'),
    'implant': fields.Nested(implant_model, description='Implant details')
})

case_update_model = api.model('CaseUpdate', {
    'case_name': fields.String(description='Case name/title'),
    'description': fields.String(description='Case description'),
    'priority': fields.String(description='Case priority', enum=['low', 'medium', 'high']),
    'status': fields.String(description='Case status', enum=[s.value for s in CaseStatus]),
    'assigned_to': fields.String(description='User assigned to the case'),
    'due_date': fields.Date(description='Case due date (YYYY-MM-DD)'),
    'rush_order': fields.Boolean(description='Rush order flag'),
    'special_instructions': fields.String(description='Special fabrication instructions'),
    'patient_info': fields.Nested(api.model('PatientInfoUpdate', {
        'patient_id': fields.String(description='Patient identifier'),
        'age': fields.Integer(description='Patient age'),
        'gender': fields.String(description='Patient gender', enum=['male', 'female', 'other']),
        'medical_history': fields.String(description='Relevant medical history')
    }), description='Patient information'),
    'fixed_prosthetic': fields.Nested(fixed_prosthetic_model, description='Fixed prosthetic details'),
    'denture': fields.Nested(denture_model, description='Denture details'),
    'night_guard': fields.Nested(night_guard_model, description='Night guard details'),
    'implant': fields.Nested(implant_model, description='Implant details')
})

# Case Output Model (for responses)
case_output_model = api.model('Case', {
    'id': fields.Integer(readonly=True, description='Case ID'),
    'doctor_id': fields.String(required=True, description='Doctor ID'),
    'product_id': fields.String(required=True, description='Product ID'),
    'lab_id': fields.String(readonly=True, description='Laboratory ID'),
    'case_name': fields.String(description='Case name/title'),
    'description': fields.String(description='Case description'),
    'priority': fields.String(description='Case priority'),
    'status': fields.String(readonly=True, description='Case status'),
    'assigned_to': fields.String(description='User assigned to the case'),
    'patient_info': fields.Raw(description='Patient information'),
    'dental_details': fields.Raw(description='Dental work details'),
    'due_date': fields.Date(description='Case due date'),
    'rush_order': fields.Boolean(description='Rush order flag'),
    'special_instructions': fields.String(description='Special fabrication instructions'),
    'case_type': fields.String(description='Type of dental case'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp')
})

# Case List Response Model
case_list_response = api.model('CaseListResponse', {
    'cases': fields.List(fields.Nested(case_output_model)),
    'pagination': fields.Nested(pagination_model)
})

@api.route('/')
class CaseList(Resource):
    @api.doc(
        'list_cases',
        description='Retrieve a paginated list of cases for the authenticated laboratory',
        responses={
            200: 'Success - Returns list of cases with pagination',
            401: 'Unauthorized - Invalid or missing JWT token',
            403: 'Forbidden - User lab information not available',
            500: 'Internal Server Error'
        },
        params={
            'page': {'description': 'Page number (default: 1)', 'type': 'integer', 'default': 1},
            'per_page': {'description': 'Items per page (default: 20, max: 100)', 'type': 'integer', 'default': 20},
            'status': {'description': 'Filter by case status', 'type': 'string', 'enum': [s.value for s in CaseStatus]},
            'doctor_id': {'description': 'Filter by doctor ID', 'type': 'string'},
            'product_id': {'description': 'Filter by product ID', 'type': 'string'},
            'case_type': {'description': 'Filter by case type', 'type': 'string', 'enum': ['fixed_prosthetic', 'denture', 'night_guard', 'implant']},
            'priority': {'description': 'Filter by priority level', 'type': 'string', 'enum': ['low', 'medium', 'high']},
            'rush_order': {'description': 'Filter by rush order status', 'type': 'boolean'}
        }
    )
    @api.marshal_with(case_list_response)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @require_auth
    def get(self):
        """
        GET /api/v1/cases/
        
        Retrieve a paginated list of cases for the authenticated laboratory.
        Supports filtering by status, doctor, product, case type, priority, and rush order status.
        """
        try:
            user_lab_id = get_user_lab_id()
            if not user_lab_id:
                api.abort(403, 'User lab information not available')
            
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            # Get filter parameters
            status = request.args.get('status')
            doctor_id = request.args.get('doctor_id')
            product_id = request.args.get('product_id')
            case_type = request.args.get('case_type')
            priority = request.args.get('priority')
            rush_order = request.args.get('rush_order', type=bool)
            
            # Build query
            query = Case.query.filter_by(lab_id=user_lab_id)
            
            if status:
                try:
                    status_enum = CaseStatus(status)
                    query = query.filter_by(status=status_enum)
                except ValueError:
                    api.abort(400, f'Invalid status: {status}')
            
            if doctor_id:
                query = query.filter_by(doctor_id=doctor_id)
            
            if product_id:
                query = query.filter_by(product_id=product_id)
            
            if case_type:
                query = query.filter_by(case_type=case_type)
            
            if priority:
                query = query.filter_by(priority=priority)
            
            if rush_order is not None:
                query = query.filter_by(rush_order=rush_order)
            
            # Execute paginated query
            cases_pagination = query.order_by(Case.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'cases': [case.to_dict() for case in cases_pagination.items],
                'pagination': {
                    'page': cases_pagination.page,
                    'per_page': cases_pagination.per_page,
                    'total': cases_pagination.total,
                    'pages': cases_pagination.pages,
                    'has_prev': cases_pagination.has_prev,
                    'has_next': cases_pagination.has_next
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing cases: {str(e)}")
            api.abort(500, 'Internal server error')
    
    @api.doc(
        'create_case',
        description='Create a new dental case with comprehensive specifications',
        responses={
            201: 'Created - Case created successfully',
            400: 'Bad Request - Invalid input data or validation errors',
            401: 'Unauthorized - Invalid or missing JWT token',
            403: 'Forbidden - User lab information not available or doctor not associated',
            500: 'Internal Server Error'
        }
    )
    @api.expect(case_input_model, validate=True)
    @api.marshal_with(case_output_model, code=201)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @require_auth
    def post(self):
        """
        POST /api/v1/cases/
        
        Create a new dental case with comprehensive specifications including:
        - Patient information
        - Dental product details (crowns, dentures, night guards, implants)
        - Shade and material specifications
        - Due dates and priority levels
        - Special instructions and rush orders
        
        The system validates doctor-lab relationships and product availability
        through external API calls to UMS and LinksHub services.
        """
        try:
            user = get_current_user()
            user_lab_id = get_user_lab_id()
            
            if not user_lab_id:
                api.abort(403, 'User lab information not available')
            
            data = api.payload
            
            # Get token for external API calls
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1] if auth_header else None
            
            # Validate doctor and product using external APIs
            linkshub_client = LinksHubClient()
            
            # Verify doctor exists and has relation with lab
            doctor_info = linkshub_client.get_doctor_info(data['doctor_id'], token)
            if not doctor_info:
                api.abort(400, 'Doctor not found')
            
            # Validate doctor-lab relationship
            if not linkshub_client.validate_doctor_lab_relation(data['doctor_id'], user_lab_id, token):
                api.abort(400, 'Doctor is not associated with your lab')
            
            # Verify product exists and is available for lab
            product_info = linkshub_client.get_product_info(data['product_id'], token)
            if not product_info:
                api.abort(400, 'Product not found')
            
            # Create new case with all provided data
            case = Case(
                lab_id=user_lab_id,
                doctor_id=data['doctor_id'],
                product_id=data['product_id'],
                case_name=data.get('case_name'),
                description=data.get('description'),
                priority=data.get('priority', 'medium'),
                created_by=user.get('user_id'),
                assigned_to=data.get('assigned_to'),
                case_type=data.get('case_type'),
                due_date=data.get('due_date'),
                rush_order=data.get('rush_order', False),
                special_instructions=data.get('special_instructions'),
                patient_info=data.get('patient_info'),
                fixed_prosthetic=data.get('fixed_prosthetic'),
                denture=data.get('denture'),
                night_guard=data.get('night_guard'),
                implant=data.get('implant')
            )
            
            db.session.add(case)
            db.session.commit()
            
            logger.info(f"Case created successfully: {case.id}")
            return case.to_dict(), 201
            
        except Exception as e:
            logger.error(f"Error creating case: {str(e)}")
            db.session.rollback()
            api.abort(500, 'Internal server error')

@api.route('/<int:case_id>')
@api.param('case_id', 'The case identifier')
class CaseDetail(Resource):
    @api.doc(
        'get_case',
        description='Retrieve detailed information for a specific case',
        responses={
            200: 'Success - Returns case details',
            401: 'Unauthorized - Invalid or missing JWT token',
            403: 'Forbidden - User lab information not available',
            404: 'Not Found - Case not found or not accessible',
            500: 'Internal Server Error'
        }
    )
    @api.marshal_with(case_output_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'Not Found', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @require_auth
    def get(self, case_id):
        """
        GET /api/v1/cases/{case_id}
        
        Retrieve detailed information for a specific case including:
        - All case metadata and status
        - Patient information
        - Dental product specifications
        - Shade and material details
        - Timeline and assignment information
        """
        try:
            user_lab_id = get_user_lab_id()
            if not user_lab_id:
                api.abort(403, 'User lab information not available')
            
            case = Case.query.filter_by(id=case_id, lab_id=user_lab_id).first()
            if not case:
                api.abort(404, 'Case not found')
            
            return case.to_dict()
            
        except Exception as e:
            logger.error(f"Error retrieving case {case_id}: {str(e)}")
            api.abort(500, 'Internal server error')
    
    @api.doc(
        'update_case',
        description='Update case information with partial or complete data',
        responses={
            200: 'Success - Case updated successfully',
            400: 'Bad Request - Invalid input data',
            401: 'Unauthorized - Invalid or missing JWT token',
            403: 'Forbidden - User lab information not available',
            404: 'Not Found - Case not found or not accessible',
            500: 'Internal Server Error'
        }
    )
    @api.expect(case_update_model, validate=True)
    @api.marshal_with(case_output_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'Not Found', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @require_auth
    def put(self, case_id):
        """
        PUT /api/v1/cases/{case_id}
        
        Update case information with partial or complete data.
        Supports updating all case fields including:
        - Basic information (name, description, priority)
        - Status and assignments
        - Patient information
        - Dental product specifications
        - Due dates and special instructions
        """
        try:
            user_lab_id = get_user_lab_id()
            if not user_lab_id:
                api.abort(403, 'User lab information not available')
            
            case = Case.query.filter_by(id=case_id, lab_id=user_lab_id).first()
            if not case:
                api.abort(404, 'Case not found')
            
            data = api.payload
            case.update_from_dict(data)
            
            db.session.commit()
            
            logger.info(f"Case updated successfully: {case_id}")
            return case.to_dict()
            
        except Exception as e:
            logger.error(f"Error updating case {case_id}: {str(e)}")
            db.session.rollback()
            api.abort(500, 'Internal server error')
    
    @api.doc(
        'delete_case',
        description='Permanently delete a case and all associated data',
        responses={
            204: 'No Content - Case deleted successfully',
            401: 'Unauthorized - Invalid or missing JWT token',
            403: 'Forbidden - User lab information not available',
            404: 'Not Found - Case not found or not accessible',
            500: 'Internal Server Error'
        }
    )
    @api.response(401, 'Unauthorized', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'Not Found', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @require_auth
    def delete(self, case_id):
        """
        DELETE /api/v1/cases/{case_id}
        
        Permanently delete a case and all associated data.
        This action cannot be undone.
        
        Note: Consider implementing soft delete in production
        environments to maintain audit trails.
        """
        try:
            user_lab_id = get_user_lab_id()
            if not user_lab_id:
                api.abort(403, 'User lab information not available')
            
            case = Case.query.filter_by(id=case_id, lab_id=user_lab_id).first()
            if not case:
                api.abort(404, 'Case not found')
            
            db.session.delete(case)
            db.session.commit()
            
            logger.info(f"Case deleted successfully: {case_id}")
            return '', 204
            
        except Exception as e:
            logger.error(f"Error deleting case {case_id}: {str(e)}")
            db.session.rollback()
            api.abort(500, 'Internal server error')

@api.route('/<int:case_id>/status')
@api.param('case_id', 'The case identifier')
class CaseStatusUpdate(Resource):
    @api.doc('update_case_status')
    @api.expect(api.model('StatusUpdate', {
        'status': fields.String(required=True, description='New case status', 
                               enum=[s.value for s in CaseStatus])
    }))
    @api.marshal_with(case_output_model)
    @require_auth
    def patch(self, case_id):
        """Update case status only"""
        try:
            user_lab_id = get_user_lab_id()
            if not user_lab_id:
                api.abort(403, 'User lab information not available')
            
            case = Case.query.filter_by(id=case_id, lab_id=user_lab_id).first()
            if not case:
                api.abort(404, 'Case not found')
            
            data = api.payload
            new_status = data.get('status')
            
            try:
                case.status = CaseStatus(new_status)
            except ValueError:
                api.abort(400, f'Invalid status: {new_status}')
            
            db.session.commit()
            
            logger.info(f"Case status updated: {case_id} -> {new_status}")
            return case.to_dict()
            
        except Exception as e:
            logger.error(f"Error updating case status {case_id}: {str(e)}")
            db.session.rollback()
            api.abort(500, 'Internal server error')

# Additional dental-specific endpoints
@api.route('/types')
class CaseTypes(Resource):
    @api.doc(
        'get_case_types',
        description='Get available dental case types and their specifications',
        responses={
            200: 'Success - Returns available case types with specifications',
            500: 'Internal Server Error'
        }
    )
    @api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """
        GET /api/v1/cases/types
        
        Retrieve available dental case types and their specifications including:
        - Fixed prosthetics (crowns, bridges, inlays, onlays, veneers)
        - Dentures (complete, partial, immediate, implant-supported)
        - Night guards (soft, hard, dual laminate)
        - Implant restorations (single, bridge, overdenture)
        
        Each type includes available subtypes and compatible materials.
        """
        return {
            'api_version': '1.0',
            'case_types': [
                {
                    'type': 'fixed_prosthetic',
                    'name': 'Fixed Prosthetics',
                    'description': 'Crowns, bridges, inlays, onlays, veneers',
                    'subtypes': ['crown', 'bridge', 'inlay', 'onlay', 'veneer', 'implant_crown'],
                    'materials': ['porcelain_fused_metal', 'all_ceramic', 'zirconia', 'emax', 'gold', 'composite'],
                    'preparation_types': ['full_coverage', 'partial_coverage', 'minimal_prep', 'no_prep'],
                    'margin_types': ['shoulder', 'chamfer', 'knife_edge', 'feather_edge']
                },
                {
                    'type': 'denture',
                    'name': 'Dentures',
                    'description': 'Complete and partial dentures',
                    'subtypes': ['complete_upper', 'complete_lower', 'complete_full', 'partial_upper', 'partial_lower', 'immediate', 'conventional', 'implant_supported'],
                    'materials': ['acrylic_resin', 'flexible_nylon', 'metal_framework', 'titanium'],
                    'tooth_materials': ['acrylic', 'porcelain', 'composite'],
                    'clasp_designs': ['cast_clasps', 'wrought_wire', 'precision_attachments', 'none'],
                    'retention_types': ['conventional_suction', 'implant_retained', 'implant_supported', 'adhesive']
                },
                {
                    'type': 'night_guard',
                    'name': 'Night Guards',
                    'description': 'Protective appliances for bruxism',
                    'subtypes': ['soft_guard', 'hard_guard', 'dual_laminate', 'nti_tss'],
                    'materials': ['soft_vinyl', 'hard_acrylic', 'dual_layer', 'thermoplastic'],
                    'thickness_options': ['1mm', '2mm', '3mm', '4mm', 'custom'],
                    'arch_options': ['upper', 'lower', 'both'],
                    'designs': ['full_coverage', 'anterior_only', 'canine_guidance', 'balanced_occlusion'],
                    'special_features': ['bite_ramps', 'tongue_space', 'breathing_holes', 'custom_thickness']
                },
                {
                    'type': 'implant',
                    'name': 'Implant Restorations',
                    'description': 'Implant-supported restorations',
                    'subtypes': ['single_crown', 'bridge_abutment', 'overdenture_attachment', 'bar_retained'],
                    'systems': ['nobel_biocare', 'straumann', 'zimmer_biomet', 'dentsply_sirona', 'megagen', 'bicon', 'other'],
                    'diameters': ['3.0mm', '3.3mm', '3.5mm', '4.0mm', '4.1mm', '4.3mm', '4.5mm', '5.0mm', '6.0mm'],
                    'lengths': ['6mm', '8mm', '10mm', '11.5mm', '13mm', '15mm', '18mm'],
                    'platform_types': ['external_hex', 'internal_hex', 'internal_tri_channel', 'morse_taper'],
                    'abutment_types': ['stock_abutment', 'custom_abutment', 'angled_abutment', 'temporary_abutment']
                }
            ]
        }

@api.route('/shades')
class ShadeReference(Resource):
    @api.doc(
        'get_shade_systems',
        description='Get available shade systems, values, and color matching information',
        responses={
            200: 'Success - Returns shade systems and specifications',
            500: 'Internal Server Error'
        }
    )
    @api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """
        GET /api/v1/cases/shades
        
        Retrieve comprehensive shade matching information including:
        - VITA Classical shade system (A1-D4 series)
        - VITA 3D-Master system (3-dimensional classification)
        - Ivoclar Chromascop system (systematic progression)
        - Translucency levels and descriptions
        
        Essential for accurate color matching in dental restorations.
        """
        return {
            'api_version': '1.0',
            'shade_systems': {
                'vita_classical': {
                    'name': 'VITA Classical',
                    'description': 'Traditional 16-shade system organized by hue families',
                    'shades': {
                        'A_series': {
                            'name': 'Reddish-brown',
                            'shades': ['A1', 'A2', 'A3', 'A3.5', 'A4']
                        },
                        'B_series': {
                            'name': 'Reddish-yellow',
                            'shades': ['B1', 'B2', 'B3', 'B4']
                        },
                        'C_series': {
                            'name': 'Gray',
                            'shades': ['C1', 'C2', 'C3', 'C4']
                        },
                        'D_series': {
                            'name': 'Reddish-gray',
                            'shades': ['D2', 'D3', 'D4']
                        }
                    }
                },
                'vita_3d_master': {
                    'name': 'VITA 3D-Master',
                    'description': '3-dimensional shade system with lightness, chroma, and hue',
                    'lightness_range': '0-5 (0=lightest, 5=darkest)',
                    'chroma_types': ['M=medium', 'L=low', 'R=high'],
                    'hue_range': '1-3 (1=yellow, 2=neutral, 3=red)',
                    'sample_shades': ['0M1', '0M2', '0M3', '1M1', '1M2', '2L1.5', '2L2.5', '2M1', '2M2', '2M3', '2R1.5', '2R2.5', '3L1.5', '3L2.5', '3M1', '3M2', '3M3', '3R1.5', '3R2.5', '4L1.5', '4L2.5', '4M1', '4M2', '4M3', '4R1.5', '4R2.5', '5M1', '5M2', '5M3']
                },
                'ivoclar_chromascop': {
                    'name': 'Ivoclar Chromascop',
                    'description': 'Systematic shade classification with numerical progression',
                    'pattern': 'XYZ format where X=hue, Y=lightness, Z=chroma',
                    'shades': ['110', '120', '130', '140', '210', '220', '230', '240', '310', '320', '330', '340', '410', '420', '430', '440']
                }
            },
            'translucency_levels': {
                'high_translucent': {
                    'description': 'Maximum light transmission, ideal for incisal edges',
                    'applications': ['Anterior restorations', 'Thin veneers', 'Incisal areas']
                },
                'low_translucent': {
                    'description': 'Moderate opacity, suitable for most restorations',
                    'applications': ['Body areas', 'Standard crowns', 'General restorations']
                },
                'opaque': {
                    'description': 'Minimal light transmission, for masking dark substrates',
                    'applications': ['Metal coverage', 'Dark tooth structure', 'Implant abutments']
                }
            }
        }

@api.route('/materials')
class MaterialReference(Resource):
    @api.doc(
        'get_materials',
        description='Get comprehensive material specifications organized by dental application',
        responses={
            200: 'Success - Returns material specifications by category',
            500: 'Internal Server Error'
        }
    )
    @api.response(500, 'Internal Server Error', error_model)
    def get(self):
        """
        GET /api/v1/cases/materials
        
        Retrieve comprehensive material specifications including:
        - Crown and bridge materials with properties
        - Denture base materials and characteristics  
        - Night guard materials and applications
        - Strength, esthetics, and durability ratings
        
        Essential for material selection and case planning.
        """
        return {
            'api_version': '1.0',
            'materials': {
                'crown_bridge': {
                    'porcelain_fused_metal': {
                        'name': 'Porcelain Fused to Metal (PFM)',
                        'description': 'Traditional metal-ceramic restoration',
                        'strength': 'high',
                        'esthetics': 'good',
                        'durability': 'excellent',
                        'applications': ['Posterior crowns', 'Long-span bridges', 'High stress areas'],
                        'contraindications': ['Esthetic zones with thin tissues', 'Metal allergies'],
                        'typical_thickness': '1.5-2.0mm'
                    },
                    'all_ceramic': {
                        'name': 'All Ceramic',
                        'description': 'Metal-free ceramic restoration',
                        'strength': 'moderate',
                        'esthetics': 'excellent',
                        'durability': 'good',
                        'applications': ['Anterior crowns', 'Veneers', 'Inlays/Onlays'],
                        'advantages': ['Superior esthetics', 'Biocompatible', 'No metal show-through'],
                        'typical_thickness': '1.0-1.5mm'
                    },
                    'zirconia': {
                        'name': 'Zirconia',
                        'description': 'High-strength ceramic material',
                        'strength': 'very_high',
                        'esthetics': 'very_good',
                        'durability': 'excellent',
                        'applications': ['Posterior crowns', 'Bridges', 'Implant abutments'],
                        'advantages': ['Exceptional strength', 'Biocompatible', 'Minimal wear on opposing teeth'],
                        'typical_thickness': '0.8-1.5mm'
                    },
                    'emax': {
                        'name': 'IPS e.max (Lithium Disilicate)',
                        'description': 'High-strength glass ceramic',
                        'strength': 'high',
                        'esthetics': 'excellent',
                        'durability': 'very_good',
                        'applications': ['Anterior/posterior crowns', 'Veneers', 'Inlays/Onlays'],
                        'advantages': ['Exceptional esthetics', 'Excellent strength', 'Conservative preparation'],
                        'typical_thickness': '1.0-1.5mm'
                    }
                },
                'denture_base': {
                    'acrylic_resin': {
                        'name': 'Acrylic Resin',
                        'description': 'Traditional denture base material',
                        'flexibility': 'rigid',
                        'durability': 'good',
                        'repairability': 'excellent',
                        'applications': ['Complete dentures', 'Partial denture bases'],
                        'advantages': ['Easy to adjust', 'Cost effective', 'Easy to repair'],
                        'maintenance': 'Regular cleaning and periodic relining'
                    },
                    'flexible_nylon': {
                        'name': 'Flexible Nylon (Thermoplastic)',
                        'description': 'Flexible partial denture material',
                        'flexibility': 'high',
                        'durability': 'moderate',
                        'esthetics': 'excellent',
                        'applications': ['Partial dentures', 'Esthetic clasps'],
                        'advantages': ['No metal clasps', 'Comfortable fit', 'Natural appearance'],
                        'limitations': ['Difficult to adjust', 'Limited repairability']
                    },
                    'metal_framework': {
                        'name': 'Metal Framework (Titanium/Cobalt-Chrome)',
                        'description': 'High-strength metal framework',
                        'strength': 'excellent',
                        'biocompatibility': 'excellent',
                        'applications': ['Implant-supported prosthetics', 'High-stress situations'],
                        'advantages': ['Superior strength', 'Precise fit', 'Long-term stability']
                    }
                },
                'night_guard': {
                    'soft_vinyl': {
                        'name': 'Soft Vinyl',
                        'description': 'Soft, cushioning material',
                        'comfort': 'high',
                        'durability': 'moderate',
                        'applications': ['Light bruxism', 'TMJ therapy', 'Sports guards'],
                        'advantages': ['Maximum comfort', 'Easy adaptation'],
                        'limitations': ['Shorter lifespan', 'May encourage chewing']
                    },
                    'hard_acrylic': {
                        'name': 'Hard Acrylic',
                        'description': 'Rigid protective material',
                        'protection': 'excellent',
                        'durability': 'high',
                        'applications': ['Severe bruxism', 'Long-term use'],
                        'advantages': ['Maximum protection', 'Long-lasting', 'Easy to clean'],
                        'considerations': ['Initial comfort adjustment period']
                    },
                    'dual_layer': {
                        'name': 'Dual Laminate',
                        'description': 'Soft inner, hard outer layer',
                        'comfort': 'high',
                        'protection': 'excellent',
                        'applications': ['Moderate to severe bruxism', 'Patient comfort priority'],
                        'advantages': ['Comfort and protection', 'Better retention', 'Reduced bulk']
                    }
                }
            }
        }

@api.route('/doctor-info/<string:doctor_id>')
@api.param('doctor_id', 'The doctor identifier')
class DoctorInfo(Resource):
    @api.doc(
        'get_doctor_info',
        description='Retrieve comprehensive doctor account and practice information',
        responses={
            200: 'Success - Returns doctor account information',
            401: 'Unauthorized - Invalid or missing JWT token',
            404: 'Not Found - Doctor not found',
            500: 'Internal Server Error'
        }
    )
    @api.marshal_with(doctor_account_model)
    @api.response(401, 'Unauthorized', error_model)
    @api.response(404, 'Not Found', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @require_auth
    def get(self, doctor_id):
        """
        GET /api/v1/cases/doctor-info/{doctor_id}
        
        Retrieve comprehensive doctor account information including:
        - Professional details and credentials
        - Practice information and specialties
        - Contact information and addresses
        - Laboratory relationships and associations
        
        Used for case assignment validation and communication.
        """
        try:
            # Get token for external API calls
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1] if auth_header else None
            
            # Fetch doctor info from external API
            linkshub_client = LinksHubClient()
            doctor_info = linkshub_client.get_doctor_info(doctor_id, token)
            
            if not doctor_info:
                api.abort(404, 'Doctor not found')
            
            return doctor_info
            
        except Exception as e:
            logger.error(f"Error fetching doctor info: {str(e)}")
            api.abort(500, 'Internal server error')