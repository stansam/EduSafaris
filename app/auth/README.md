# Flask Authentication Blueprint

A comprehensive Flask authentication system with both web-based session authentication (Flask-Login) and JWT API authentication.

## Features

### Core Authentication
- **User Registration** with email verification
- **User Login/Logout** with session management
- **Password Reset** via email with secure tokens
- **JWT API Authentication** for API clients
- **Role-based Access Control** with dashboard routing
- **Rate Limiting** for password reset requests

### Security Features
- Password hashing with Werkzeug
- Secure token generation using itsdangerous
- CSRF protection with Flask-WTF
- Email verification workflow
- Account deactivation support
- Session management with Flask-Login

### User Experience
- Responsive Bootstrap-based UI
- Real-time client-side validation
- Password strength indicator
- Password visibility toggle
- Auto-hide alerts
- Loading states for forms

## Quick Start

### 1. Installation

```bash
# Clone or create your Flask project
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Especially important: EMAIL settings for password reset
```

### 3. Database Setup

```python
# Initialize database
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
```

### 4. Run Application

```bash
python run.py
```

Visit `http://localhost:5000/auth/register` to start!

## Configuration

### Required Environment Variables

```bash
# Security (REQUIRED)
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=sqlite:///app.db  # or PostgreSQL URL for production

# Email (for password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Email Provider Setup

#### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate App Password: Google Account → Security → App passwords
3. Use app password in `MAIL_PASSWORD`

#### Other Providers
Update `MAIL_SERVER`, `MAIL_PORT`, and `MAIL_USE_TLS` accordingly.

## API Endpoints

### Web Routes (Session-based)
- `GET/POST /auth/register` - User registration
- `GET/POST /auth/login` - User login  
- `GET /auth/logout` - User logout
- `GET/POST /auth/reset_password` - Request password reset
- `GET/POST /auth/reset_password/<token>` - Reset with token
- `GET /auth/verify_email/<token>` - Email verification

### API Routes (JWT-based)
- `POST /auth/api/login` - JWT login
- `POST /auth/api/register` - API registration

#### JWT API Examples

**Login:**
```bash
curl -X POST http://localhost:5000/auth/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "role": "user",
    "is_verified": true
  }
}
```

**Using JWT Token:**
```bash
curl -X GET http://localhost:5000/protected-endpoint \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## User Model

The `User` model includes:

```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
```

### Role-based Dashboards
Users are redirected to role-specific dashboards:
- `admin` → `/admin/dashboard`
- `moderator` → `/moderator/dashboard`  
- `user` → `/user/dashboard`

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_auth.py

# Run with coverage
python -m pytest tests/ --cov=app
```

### Test Coverage
The test suite covers:
- User registration (valid/invalid data)
- Login/logout functionality
- Password reset flow
- Email verification
- JWT API endpoints
- Rate limiting
- Security edge cases

## Customization

### Templates
Templates are in `app/auth/templates/auth/`:
- `base.html` - Base template
- `register.html` - Registration form
- `login.html` - Login form  
- `reset_request.html` - Password reset request
- `reset_password.html` - Password reset form

### Styling
- `app/auth/static/auth.css` - Authentication styles
- `app/auth/static/auth.js` - Client-side validation and UX

### Email Templates
Email templates in `app/templates/email/`:
- `password_reset.html` - Password reset email
- `email_verification.html` - Email verification

## Security Considerations

### Production Checklist
- [ ] Change default secret keys
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set up proper email provider (not Gmail for production)
- [ ] Configure proper CORS for JWT API
- [ ] Set up rate limiting with Redis
- [ ] Enable logging and monitoring
- [ ] Regular security audits

### Rate Limiting
Current implementation uses in-memory storage. For production:

```python
# Use Redis for distributed rate limiting
import redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

@auth_bp.route('/reset_password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_request():
    # Code here
```

### Protecting Routes

```python
from flask_login import login_required, current_user

@app.route('/dashboard')
@login_required
def dashboard():
    return f"Welcome {current_user.username}!"

# Role-based protection
from functools import wraps

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin')
@login_required
@role_required('admin')
def admin_panel():
    return "Admin only content"
```

### JWT Protection

```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/api/profile')
@jwt_required()
def api_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    })
```

## Troubleshooting

### Common Issues

**Email not sending:**
- Check spam folder
- Verify email credentials
- Check firewall/network settings
- Try different email provider

**Database errors:**
- Run `db.create_all()` to create tables
- Check database permissions
- Verify connection string

**JWT issues:**
- Verify JWT_SECRET_KEY is set
- Check token expiration
- Ensure proper Authorization header format

**Template not found:**
- Verify blueprint template folder registration
- Check file paths and names
- Ensure templates are in correct directory

## Support

For questions or issues:
1. Check this documentation
2. Review test cases for examples
3. Check Flask and extension documentation
4. Open an issue with reproduction steps

## License

This project is provided as-is for educational and development purposes.