# LHCMS - Lab Healthcare Case Management System

Enterprise-grade Flask microservice for dental laboratory case management with multi-tenant architecture and comprehensive security controls.

## Overview

LHCMS provides a complete case management solution for dental laboratories, featuring secure multi-tenant data isolation, integrated authentication, and real-time case tracking capabilities. The system is built on modern Flask architecture with enterprise-ready security and compliance features.

## Features

### Case Management
- Complete CRUD operations for dental cases
- Real-time case status tracking and updates
- Patient information management with privacy controls
- Procedure type classification and workflow management
- Audit trail and activity logging

### Security & Compliance
- JWT-based authentication with User Management Service integration
- Multi-tenant lab-based data isolation
- HIPAA-compliant data handling and storage
- Role-based access control
- Comprehensive audit logging

### API & Integration
- RESTful API with OpenAPI 3.0 specification
- Auto-generated Swagger documentation
- CORS support for web application integration
- Health monitoring and status endpoints
- Structured error handling and validation

## Installation

### System Requirements
- Python 3.8 or higher
- User Management Service (UMS) instance
- PostgreSQL (production) or SQLite (development)

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zaidku/LHCMS.git
   cd LHCMS
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with appropriate values
   ```

5. **Start the service**:
   ```bash
   python app.py
   ```

The service runs on port 5001 by default.

### API Documentation
Access the interactive API documentation:
- **Swagger UI**: http://localhost:5001/docs/
- **API JSON**: http://localhost:5001/api/v1/swagger.json

## Configuration

### Environment Variables
Configure the application using environment variables in `.env` file:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///case_service.db

# UMS Integration
UMS_BASE_URL=http://localhost:5000
UMS_API_KEY=your-ums-api-key

# Service Configuration
PORT=5001
DEBUG=true
```

### Deployment Environments
- **Development**: SQLite database with debug logging
- **QA**: PostgreSQL with structured logging
- **Production**: PostgreSQL with performance optimization

## API Reference

### Authentication
All API endpoints require JWT authentication using the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Core Endpoints

#### Cases
- `GET /api/v1/cases` - List all cases (lab-filtered)
- `POST /api/v1/cases` - Create new case
- `GET /api/v1/cases/{id}` - Get specific case
- `PUT /api/v1/cases/{id}` - Update case
- `DELETE /api/v1/cases/{id}` - Delete case

#### Health & Status
- `GET /health` - Service health check
- `GET /api/v1/health` - Detailed health status

### Request/Response Examples

#### Create Case
```bash
curl -X POST http://localhost:5001/api/v1/cases \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "John Doe",
    "procedure_type": "Crown",
    "status": "in_progress",
    "notes": "Upper molar crown preparation"
  }'
```

#### Response
```json
{
  "id": 1,
  "patient_name": "John Doe",
  "procedure_type": "Crown",
  "status": "in_progress",
  "notes": "Upper molar crown preparation",
  "lab_id": 123,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

## System Architecture

### Service Integration
```
Frontend Application → LHCMS (Port 5001) → UMS (Port 5000)
                              ↓
                        Database Layer
```

### Authentication Flow
1. User authentication processed by UMS
2. JWT token issued by UMS
3. Client applications authenticate with LHCMS using JWT
4. LHCMS validates tokens through UMS service
5. Data access filtered by lab membership

### Multi-Tenant Data Isolation
- Laboratory-based data segregation
- Users access only assigned laboratory cases
- Cross-laboratory data access for authorized users
- Comprehensive audit logging for compliance

## Development

### Project Structure
```
LHCMS/
├── app.py                    # Flask application entry point
├── config.py                # Environment configuration management
├── requirements.txt         # Python package dependencies
├── db.py                    # Database connection and initialization
├── models/
│   └── case.py             # Case entity data model
├── routes/
│   └── case_routes.py      # REST API endpoint definitions
├── services/
│   ├── ums_client.py       # User Management Service client
│   └── linkshub_client.py  # External service integration
├── utils/
│   └── auth.py             # Authentication and authorization
└── instance/
    └── case_service.db     # SQLite database (development)
```

### Testing
```bash
# Integration test suite
python integration_test.py

# UMS connectivity verification
python test_connection.py

# API endpoint examples
python api_examples.py
```

### Development Environment
1. Start User Management Service on port 5000
2. Launch LHCMS in development mode:
   ```bash
   python app.py
   ```
3. Access API documentation at http://localhost:5001/docs/

## Deployment

### Production Environment
1. **Configure environment variables**:
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@host:port/dbname
   ```

2. **Initialize database**:
   ```bash
   flask db upgrade
   ```

3. **Start production server**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

### Container Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
```

### Environment Variables for Production
```bash
FLASK_ENV=production
SECRET_KEY=secure-random-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
UMS_BASE_URL=https://ums.yourdomain.com
REDIS_URL=redis://redis:6379/0
```

## Monitoring & Logging

### Health Checks
- `/health` - Basic health status
- `/api/v1/health` - Detailed service status including UMS connectivity

### Logging
- Structured logging with JSON format in production
- Request/response logging for audit trails
- Error tracking and alerting integration

### Metrics
- Request count and response time metrics
- Database connection pool monitoring
- UMS integration health metrics

## Security

### Data Protection
- JWT token validation for all endpoints
- Lab-based data isolation
- SQL injection prevention via SQLAlchemy ORM
- Input validation and sanitization

### HIPAA Compliance
- Secure data transmission (HTTPS in production)
- Access logging and audit trails
- Data encryption at rest and in transit
- User activity monitoring

## Troubleshooting

### Common Issues

1. **UMS Connection Failed**:
   ```bash
   # Check UMS availability
   curl http://localhost:5000/health
   ```

2. **Database Connection Issues**:
   ```bash
   # Verify database URL
   echo $DATABASE_URL
   ```

3. **Authentication Errors**:
   - Verify JWT token format
   - Check UMS service status
   - Validate lab membership

### Debug Mode
```bash
export FLASK_ENV=development
python app.py
```

## Contributing

### Development Process
1. Fork the repository
2. Create feature branch from master
3. Implement changes with appropriate tests
4. Submit pull request with detailed description

### Code Standards
- PEP 8 compliance for Python code
- Type annotations where applicable
- Comprehensive unit and integration tests
- Documentation updates for new features

## License

This project is licensed under the MIT License.

## Support

Technical support and documentation:
- GitHub Issues for bug reports and feature requests
- Integration documentation: `UMS_INTEGRATION_GUIDE.md`
- API usage examples: `api_examples.py`

---

**System Requirements**: This service requires the User Management Service (UMS) to be operational for authentication and authorization functionality.