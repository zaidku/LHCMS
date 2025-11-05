# UMS Integration Specification

## Overview
Technical specification for integration between LHCMS and the User Management Service (UMS) within the LinksTechnologies dental laboratory platform.

## Service Architecture
```
┌────────────────────┐
│   Client Portal    │
└────────┬───────────┘
         │
   HTTPS Request
         │
 ┌───────▼────────┐
 │   API Gateway  │
 │ (Kong/Traefik) │
 └───────┬────────┘
         │
    ┌────▼────┐     ┌────▼────┐
    │   UMS   │────▶│  LHCMS  │
    │ :5000   │     │ :5001   │
    └─────────┘     └─────────┘
```

## Service Configuration

### UMS (User Management Service)
- **Port**: 5000
- **Base URL**: `http://localhost:5000`
- **API Base**: `http://localhost:5000/api`
- **Documentation**: HIPAA-compliant, multi-tenant architecture

### CMS (Case Management Service)  
- **Port**: 5001
- **Base URL**: `http://localhost:5001`
- **API Base**: `http://localhost:5001/api/v1`
- **Swagger Docs**: `http://localhost:5001/docs/`

## API Integration Points

### 1. Authentication Flow
```
Client → UMS Login → JWT Token → CMS API Calls
```

**UMS Login Endpoint:**
```bash
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "username": "john",
  "password": "pass123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@test.com",
    "labs": [
      {
        "lab_id": 1,
        "lab_name": "Test Lab",
        "role": "member",
        "membership_status": "active"
      }
    ]
  }
}
```

### 2. Token Verification
CMS verifies tokens with UMS using:

**UMS Token Verification:**
```bash
GET http://localhost:5000/api/auth/me
Authorization: Bearer {access_token}
```

**CMS Implementation:**
```python
# services/ums_client.py
def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    url = f"{self.api_base}/auth/me"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None
```

### 3. Lab-Based Access Control
CMS implements multi-tenant isolation matching UMS:

```python
# utils/auth.py
def get_user_lab_id():
    user = get_current_user()
    if user and 'labs' in user:
        for lab in user['labs']:
            if lab.get('membership_status') == 'active':
                return lab.get('lab_id')
    return None
```

### 4. Data Isolation
All CMS endpoints enforce lab-based data isolation:

```python
# routes/case_routes.py
@require_auth
def get_cases():
    user_lab_id = get_user_lab_id()
    cases = Case.query.filter_by(lab_id=user_lab_id).all()
    return cases
```

## Configuration Files

### CMS Environment (.env)
```properties
# External API Configuration
UMS_URL=http://localhost:5000  # UMS service endpoint
LINKSHUB_CORE_URL=https://core.linkstechnologies.io

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000

# JWT Configuration (should match UMS)
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
```

### CMS Configuration (config.py)
```python
class Config:
    UMS_URL = os.environ.get('UMS_URL') or 'http://localhost:5000'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-secret-key'
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM') or 'HS256'
```

## Testing Integration

### 1. Start Services
```bash
# Terminal 1: Start UMS
cd C:\Users\zaid.kuba\LHUMS
python run.py

# Terminal 2: Start CMS  
cd C:\Zaid\source\repos\lhcms\case_service
python app.py
```

### 2. Test Authentication Flow
```bash
# 1. Login to UMS
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"pass123"}'

# 2. Use token with CMS
curl -X GET http://localhost:5001/api/v1/cases/ \
  -H "Authorization: Bearer {access_token}"
```

### 3. Test Lab Isolation
```bash
# Create case (requires lab_id from UMS user data)
curl -X POST http://localhost:5001/api/v1/cases/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": "DOC001",
    "product_id": "PROD001", 
    "case_type": "crown",
    "patient_name": "John Doe"
  }'
```

## Error Handling

### UMS Connection Errors
```python
# CMS handles UMS downtime gracefully
try:
    user_info = ums_client.verify_token(token)
    if not user_info:
        return jsonify({'error': 'Invalid token'}), 401
except requests.exceptions.ConnectionError:
    return jsonify({'error': 'Authentication service unavailable'}), 503
```

### Token Refresh
```python
# Automatic token refresh when access token expires
def refresh_token(refresh_token: str):
    url = f"{self.api_base}/auth/refresh"
    headers = {'Authorization': f'Bearer {refresh_token}'}
    response = requests.post(url, headers=headers)
    return response.json() if response.status_code == 200 else None
```

## Security Considerations

### 1. HIPAA Compliance
- ✅ Password policies enforced by UMS
- ✅ Audit logging in both services
- ✅ Secure token transmission
- ✅ Data isolation between labs

### 2. Network Security
- Use HTTPS in production
- Implement API Gateway with rate limiting
- Configure proper CORS origins
- Use strong JWT secrets

### 3. Data Protection
- Lab-based tenant isolation
- Row-level security in database queries
- User authorization checks on all endpoints

## Production Deployment

### API Gateway Configuration (Kong/Traefik)
```yaml
# Example Kong configuration
services:
  - name: ums
    url: http://ums:5000
  - name: cms  
    url: http://cms:5001

routes:
  - name: ums-route
    service: ums
    paths: ["/api/auth", "/api/users", "/api/labs"]
  - name: cms-route
    service: cms
    paths: ["/api/v1/cases"]
```

### Docker Composition
```yaml
version: '3.8'
services:
  ums:
    build: ./ums
    ports: ["5000:5000"]
    environment:
      - DATABASE_URL=postgresql://...
      
  cms:
    build: ./cms
    ports: ["5001:5001"] 
    environment:
      - UMS_URL=http://ums:5000
      - DATABASE_URL=postgresql://...
    depends_on: [ums]
```

## Monitoring & Logging

### Health Checks
```bash
# UMS Health
curl http://localhost:5000/api/health

# CMS Health  
curl http://localhost:5001/health
```

### Audit Logs
Both services log authentication and data access events for HIPAA compliance.

## Next Steps

1. ✅ UMS client configuration updated
2. ✅ Authentication flow aligned 
3. ✅ CORS configuration set
4. 🔄 Test with running UMS instance
5. 🔄 Implement API Gateway proxy
6. 🔄 Production deployment setup

---

**Last Updated**: November 5, 2025  
**Version**: 1.0  
**Services**: UMS v1.0, CMS v1.0