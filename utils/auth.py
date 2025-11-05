import jwt
import requests
from functools import wraps
from flask import request, jsonify, current_app
from services.ums_client import UMSClient

def require_auth(f):
    """Decorator to require JWT authentication for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is required'}), 401
        
        # Extract token from "Bearer <token>" format
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # Verify token with UMS
        ums_client = UMSClient()
        try:
            user_info = ums_client.verify_token(token)
            if not user_info:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Add user info to request context
            request.user = user_info
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def get_current_user():
    """Get current authenticated user from request context."""
    return getattr(request, 'user', None)

def get_user_lab_id():
    """Get lab_id for the current authenticated user."""
    user = get_current_user()
    if user:
        # Check if user has lab memberships (UMS multi-tenant structure)
        if 'labs' in user and len(user['labs']) > 0:
            # Return the first active lab ID (you might want different logic)
            for lab in user['labs']:
                if lab.get('membership_status') == 'active':
                    return lab.get('lab_id')
            # If no active lab, return first lab
            return user['labs'][0].get('lab_id')
        # Fallback to direct lab_id field if exists
        return user.get('lab_id')
    return None

def verify_jwt_token(token):
    """Verify JWT token locally (for development/testing)."""
    try:
        payload = jwt.decode(
            token, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_test_token(user_data):
    """Create a test JWT token (for development/testing only)."""
    import jwt
    payload = {
        'user_id': user_data.get('user_id'),
        'lab_id': user_data.get('lab_id'),
        'email': user_data.get('email'),
        'exp': user_data.get('exp')
    }
    
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )