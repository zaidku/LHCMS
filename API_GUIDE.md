# Case Service API - HTTP Methods & Versioning Guide

## API Versioning Strategy

### Current Version: v1.0
- **Base URL**: `http://127.0.0.1:5000/api/v1`
- **Documentation**: `http://127.0.0.1:5000/docs/`
- **Status**: Active, Stable

### Version Headers
```http
Accept: application/json
Content-Type: application/json
API-Version: 1.0
Authorization: Bearer <jwt-token>
```

## HTTP Methods Documentation

### GET Methods - Data Retrieval

#### 1. GET /api/v1/cases/
**Purpose**: Retrieve paginated list of cases with filtering
```http
GET /api/v1/cases/?page=1&per_page=20&status=pending&case_type=crown
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters**:
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (max: 100)
- `status` (enum): pending, in_progress, completed, cancelled, on_hold
- `case_type` (enum): fixed_prosthetic, denture, night_guard, implant
- `priority` (enum): low, medium, high
- `doctor_id` (string): Filter by doctor ID
- `product_id` (string): Filter by product ID
- `rush_order` (boolean): true/false

**Response**:
```json
{
  "cases": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_prev": false,
    "has_next": true
  }
}
```

#### 2. GET /api/v1/cases/{case_id}
**Purpose**: Retrieve specific case details
```http
GET /api/v1/cases/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 3. GET /api/v1/cases/types
**Purpose**: Get available case types and specifications
```http
GET /api/v1/cases/types
```

#### 4. GET /api/v1/cases/shades
**Purpose**: Get shade systems and color specifications
```http
GET /api/v1/cases/shades
```

#### 5. GET /api/v1/cases/materials
**Purpose**: Get material specifications by category
```http
GET /api/v1/cases/materials
```

#### 6. GET /api/v1/cases/doctor-info/{doctor_id}
**Purpose**: Get doctor account information
```http
GET /api/v1/cases/doctor-info/doctor_123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### POST Methods - Resource Creation

#### 1. POST /api/v1/cases/
**Purpose**: Create new dental case

**Fixed Prosthetic Example**:
```http
POST /api/v1/cases/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "doctor_id": "doctor_123",
  "product_id": "crown_zirconia_001",
  "case_name": "Patient Smith - Crown #3",
  "case_type": "fixed_prosthetic",
  "priority": "medium",
  "due_date": "2025-11-19",
  "rush_order": false,
  "patient_info": {
    "patient_id": "patient_456",
    "age": 45,
    "gender": "female",
    "medical_history": "No significant history"
  },
  "special_instructions": "Match adjacent teeth closely",
  "fixed_prosthetic": {
    "type": "crown",
    "material": "zirconia",
    "tooth_numbers": [3],
    "preparation_type": "full_coverage",
    "margin_type": "shoulder",
    "shade": {
      "shade_system": "vita_classical",
      "shade_value": "A2",
      "translucency": "low_translucent",
      "notes": "Match to adjacent tooth #2"
    },
    "occlusion_type": "centric_occlusion"
  }
}
```

**Denture Example**:
```http
POST /api/v1/cases/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "doctor_id": "doctor_789",
  "product_id": "denture_complete_upper_001",
  "case_name": "Patient Johnson - Complete Upper",
  "case_type": "denture",
  "priority": "high",
  "due_date": "2025-11-26",
  "denture": {
    "type": "complete_upper",
    "material": "acrylic_resin",
    "tooth_material": "acrylic",
    "shade": {
      "shade_system": "vita_classical",
      "shade_value": "A3"
    },
    "retention_type": "conventional_suction"
  }
}
```

**Night Guard Example**:
```http
POST /api/v1/cases/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "doctor_id": "doctor_456",
  "product_id": "night_guard_dual_001",
  "case_name": "Patient Williams - Night Guard",
  "case_type": "night_guard",
  "rush_order": true,
  "night_guard": {
    "type": "dual_laminate",
    "material": "dual_layer",
    "thickness": "3mm",
    "arch": "upper",
    "design": "full_coverage",
    "special_features": ["bite_ramps", "breathing_holes"]
  }
}
```

**Implant Example**:
```http
POST /api/v1/cases/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "doctor_id": "doctor_654",
  "product_id": "implant_crown_001",
  "case_name": "Patient Davis - Implant Crown #19",
  "case_type": "implant",
  "implant": {
    "implant_system": "straumann",
    "implant_diameter": "4.1mm",
    "implant_length": "10mm",
    "platform_type": "morse_taper",
    "abutment_type": "custom_abutment",
    "restoration_type": "single_crown",
    "tooth_number": 19
  }
}
```

### PUT Methods - Complete Resource Update

#### 1. PUT /api/v1/cases/{case_id}
**Purpose**: Update complete case information
```http
PUT /api/v1/cases/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "case_name": "Updated Case Name",
  "description": "Updated description",
  "priority": "high",
  "status": "in_progress",
  "due_date": "2025-11-20",
  "special_instructions": "Rush processing required",
  "fixed_prosthetic": {
    "shade": {
      "shade_system": "vita_classical",
      "shade_value": "A3",
      "notes": "Shade adjusted per doctor request"
    }
  }
}
```

### PATCH Methods - Partial Resource Update

#### 1. PATCH /api/v1/cases/{case_id}/status
**Purpose**: Update only case status
```http
PATCH /api/v1/cases/123/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "in_progress"
}
```

### DELETE Methods - Resource Removal

#### 1. DELETE /api/v1/cases/{case_id}
**Purpose**: Permanently delete a case
```http
DELETE /api/v1/cases/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response**: `204 No Content`

### OPTIONS Methods - CORS Preflight

#### Automatic CORS Support
**Purpose**: Browser preflight requests for cross-origin access
```http
OPTIONS /api/v1/cases/
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Authorization, Content-Type
Origin: https://lab-portal.linkstechnologies.io
```

## Status Codes & Error Handling

### Success Codes
- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE

### Client Error Codes
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Access denied (lab restrictions)
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors

### Server Error Codes
- `500 Internal Server Error`: Unexpected server error

### Error Response Format
```json
{
  "error": "Bad Request",
  "message": "Invalid shade system: invalid_system",
  "code": 400,
  "timestamp": "2025-11-05T15:30:00Z"
}
```

## API Rate Limiting (Production Recommendations)

### Rate Limits
- **Standard Users**: 100 requests/minute
- **Premium Users**: 500 requests/minute
- **Bulk Operations**: Special limits apply

### Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1636123800
```

## Caching Strategies

### GET Requests
- **Reference Data**: Cache for 1 hour (types, shades, materials)
- **Case Data**: Cache for 5 minutes
- **Doctor Info**: Cache for 30 minutes

### Cache Headers
```http
Cache-Control: public, max-age=3600
ETag: "abc123def456"
Last-Modified: Tue, 05 Nov 2025 15:30:00 GMT
```

## API Evolution Strategy

### Versioning Approach
- **URL Versioning**: `/api/v1/`, `/api/v2/`
- **Backward Compatibility**: v1.0 supported for 2 years
- **Deprecation Notice**: 6 months advance warning

### Future Versions
- **v1.1**: Minor enhancements, backward compatible
- **v2.0**: Major changes, breaking changes allowed
- **v3.0**: Next generation architecture

## Testing Examples

### cURL Examples
```bash
# List cases
curl -X GET "http://127.0.0.1:5000/api/v1/cases/?page=1&status=pending" \
  -H "Authorization: Bearer <token>"

# Create case
curl -X POST "http://127.0.0.1:5000/api/v1/cases/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @case_data.json

# Update status
curl -X PATCH "http://127.0.0.1:5000/api/v1/cases/123/status" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Delete case
curl -X DELETE "http://127.0.0.1:5000/api/v1/cases/123" \
  -H "Authorization: Bearer <token>"
```

### Python Requests Examples
```python
import requests

headers = {
    'Authorization': 'Bearer <your-token>',
    'Content-Type': 'application/json'
}

# GET request
response = requests.get(
    'http://127.0.0.1:5000/api/v1/cases/',
    headers=headers,
    params={'page': 1, 'status': 'pending'}
)

# POST request
case_data = {...}  # Your case data
response = requests.post(
    'http://127.0.0.1:5000/api/v1/cases/',
    headers=headers,
    json=case_data
)

# PATCH request
response = requests.patch(
    'http://127.0.0.1:5000/api/v1/cases/123/status',
    headers=headers,
    json={'status': 'completed'}
)
```

## Integration Guidelines

### Frontend Integration
- Use proper error handling for all status codes
- Implement retry logic for 5xx errors
- Cache reference data (types, shades, materials)
- Show loading states for async operations

### Backend Integration
- Validate all input data before API calls
- Use bulk operations where available
- Implement circuit breaker patterns
- Log all API interactions for debugging

### Mobile App Integration
- Use compressed request/response bodies
- Implement offline caching
- Handle network connectivity issues
- Use background sync for data uploads