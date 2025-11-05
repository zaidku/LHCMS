# Case Management Service (CMS)

A Flask-based microservice for dental case management with JWT authentication integration and lab-based multi-tenant architecture.

## Features

### Core Functionality
- 🦷 **Dental Case Management**: Complete CRUD operations for dental cases
- 📊 **Case Tracking**: Status management and progress tracking
- 🔒 **JWT Authentication**: Integration with User Management Service (UMS)
- 🏢 **Multi-Tenant Architecture**: Lab-based data isolation
- 📝 **Swagger Documentation**: Auto-generated API documentation
- 🛡️ **HIPAA Compliance**: Secure handling of dental health information

### API Features
- RESTful API design with Flask-RESTX
- Comprehensive data validation
- Error handling and logging
- CORS support for frontend integration
- Health check endpoints

### Authentication & Security
- JWT token validation via UMS integration
- Lab-based access control
- Secure session management
- Environment-based configuration

## Quick Start

### Prerequisites
- Python 3.8+
- User Management Service (UMS) running on port 5000
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd case_service
   ```

2. **Create and activate virtual environment**:
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

4. **Run the application**:
   ```bash
   python app.py
   ```

The service will start on `http://localhost:5001`

### API Documentation
Once running, access the Swagger documentation at:
- **Swagger UI**: http://localhost:5001/docs/
- **API JSON**: http://localhost:5001/api/v1/swagger.json

## Configuration

### Environment Variables
Create a `.env` file or set environment variables:

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

### Configuration Profiles
- **Development**: SQLite database, debug mode enabled
- **QA**: PostgreSQL, limited logging
- **Production**: PostgreSQL, optimized for performance

## API Reference

### Authentication
All endpoints require JWT authentication via the `Authorization` header:
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

## Integration with UMS

### Architecture Overview
```
[Frontend] → [CMS:5001] → [UMS:5000]
                ↓
           [Database]
```

### Authentication Flow
1. User authenticates with UMS
2. UMS returns JWT token
3. Frontend sends requests to CMS with token
4. CMS validates token with UMS
5. CMS filters data by user's lab membership

### Lab-Based Access Control
- Users can only access cases within their assigned labs
- Multi-lab users see aggregated data
- Strict data isolation between labs

## Development

### Project Structure
```
case_service/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── db.py                 # Database initialization
├── models/
│   └── case.py          # Case data model
├── routes/
│   └── case_routes.py   # API route definitions
├── services/
│   ├── ums_client.py    # UMS integration client
│   └── linkshub_client.py # LinksHub integration
├── utils/
│   └── auth.py          # Authentication utilities
└── instance/
    └── case_service.db  # SQLite database (dev)
```

### Running Tests
```bash
# Integration tests
python integration_test.py

# Test UMS connection
python test_connection.py

# API examples
python api_examples.py
```

### Development Setup
1. Ensure UMS is running on port 5000
2. Start CMS in development mode:
   ```bash
   python app.py
   ```
3. Access Swagger docs at http://localhost:5001/docs/

## Deployment

### Production Deployment
1. **Environment Setup**:
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@host:port/dbname
   ```

2. **Database Migration**:
   ```bash
   flask db upgrade
   ```

3. **Production Server**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

### Docker Deployment
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

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints where applicable
- Write comprehensive tests
- Update documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the integration documentation in `UMS_INTEGRATION_GUIDE.md`
- Review API examples in `api_examples.py`

---

**Note**: This service is designed to work in conjunction with the User Management Service (UMS). Ensure UMS is properly configured and running before starting the Case Management Service.