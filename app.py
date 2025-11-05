import os
import logging
from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from config import config
from db import init_db
from routes.case_routes import api as cases_ns

def create_app(config_name=None):
    """Application factory pattern for creating Flask app."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize database
    init_db(app)
    
    # Initialize Flask-RESTX API with comprehensive documentation
    api = Api(
        app,
        version='1.0',
        title='Case Service API',
        description='''
        **Dental Laboratory Case Management System**
        
        A comprehensive Flask microservice for managing dental laboratory cases with JWT authentication.
        
        ## Features
        - **Complete Case Management**: Create, read, update, delete dental cases
        - **Dental Product Support**: Fixed prosthetics, dentures, night guards, implants
        - **Professional Shade Matching**: VITA Classical, 3D-Master, Chromascop systems
        - **Material Specifications**: Comprehensive material library with properties
        - **Doctor Integration**: External UMS and LinksHub API integration
        - **JWT Authentication**: Secure token-based authentication
        - **Lab-based Access Control**: Multi-tenancy support
        
        ## API Versioning
        - **Current Version**: 1.0
        - **Base URL**: `/api/v1`
        - **Documentation**: Available at `/docs/`
        
        ## Authentication
        All endpoints require a valid JWT token in the Authorization header:
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ## Supported HTTP Methods
        - **GET**: Retrieve resources (cases, types, shades, materials)
        - **POST**: Create new cases with comprehensive specifications
        - **PUT**: Update complete case information
        - **PATCH**: Partial updates (e.g., status changes)
        - **DELETE**: Remove cases permanently
        - **OPTIONS**: CORS preflight requests
        
        ## Rate Limiting
        - Production environments should implement rate limiting
        - Recommended: 100 requests per minute per user
        
        ## Error Handling
        Standard HTTP status codes with detailed error messages:
        - **400**: Bad Request - Invalid input data
        - **401**: Unauthorized - Missing or invalid authentication
        - **403**: Forbidden - Access denied (lab restrictions)
        - **404**: Not Found - Resource doesn't exist
        - **422**: Unprocessable Entity - Validation errors
        - **500**: Internal Server Error - Unexpected server errors
        ''',
        doc='/docs/',
        prefix=f'/api/{app.config["API_VERSION"]}',
        contact='Lab Case Management Team',
        contact_email='support@linkstechnologies.io',
        license='Proprietary',
        license_url='https://linkstechnologies.io/license',
        terms_url='https://linkstechnologies.io/terms',
        validate=True,
        ordered=True
    )
    
    # Register namespaces
    api.add_namespace(cases_ns, path='/cases')
    
    # Configure logging
    configure_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'service': 'case_service',
            'version': '1.0.0'
        }
    
    return app

def configure_logging(app):
    """Configure application logging."""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('case_service.log')
        ]
    )
    
    # Set specific loggers
    app.logger.setLevel(log_level)
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'message': str(error)}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'Access denied'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}")
        return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Run the application on port 5001 (UMS runs on 5000)
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5001)),  # Changed to 5001 to avoid conflict with UMS
        debug=app.config.get('DEBUG', False)
    )