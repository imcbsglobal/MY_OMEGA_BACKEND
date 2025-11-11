# MY OMEGA BACKEND

> **Enterprise-grade Django REST API for HR Management & Interview Processing**

[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16.1-red.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)

A robust, scalable Django REST Framework backend designed for comprehensive HR operations, candidate management, interview workflows, and user access control. Built with enterprise patterns, JWT authentication, and cloud storage integration.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Database Schema](#-database-schema)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Development Guide](#-development-guide)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Features

### Core Functionality

- **🔐 Authentication & Authorization**
  - JWT-based authentication with access/refresh tokens
  - Role-based access control (RBAC)
  - Custom user model with extended fields
  - Token expiration and rotation

- **👥 User Management**
  - Custom user profiles with job roles
  - User CRUD operations with permissions
  - Document management (Aadhar, photos)
  - Activity tracking and audit logs

- **📋 CV Management**
  - CV upload and processing
  - Job title categorization
  - Interview status tracking (pending, ongoing, selected, rejected)
  - Kerala district-specific location data
  - Multi-source CV ingestion (Direct, LinkedIn, etc.)

- **🎯 Interview Management**
  - Interview scheduling and workflow
  - Real-time status updates
  - Comprehensive evaluation system (5 rating categories)
  - Voice note recording support
  - Automatic CV status synchronization

- **🏢 HR Operations**
  - Employee attendance tracking
  - Break time management
  - Shift scheduling
  - Department organization

- **🎛️ User Access Control**
  - Dynamic menu permissions
  - Role-based menu visibility
  - Hierarchical access control
  - Custom permission management

### Technical Features

- **📦 Cloud Storage Integration**
  - Cloudflare R2 support for scalable file storage
  - Fallback to local storage
  - Configurable storage backends

- **🔄 RESTful API Design**
  - Standardized response formats
  - Comprehensive error handling
  - Pagination and filtering
  - CORS support for cross-origin requests

- **📊 Database Optimization**
  - PostgreSQL with advanced querying
  - Optimized select_related/prefetch_related
  - Database indexing
  - Transaction management

---

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│           Client Applications               │
│     (Web, Mobile, Third-party APIs)         │
└──────────────────┬──────────────────────────┘
                   │
                   │ HTTPS/JWT
                   │
┌──────────────────▼──────────────────────────┐
│         API Gateway / CORS Layer            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        Django REST Framework Layer          │
│  ┌──────────────────────────────────────┐   │
│  │  ViewSets (ModelViewSet, APIView)   │   │
│  ├──────────────────────────────────────┤   │
│  │  Serializers (Validation & I/O)     │   │
│  ├──────────────────────────────────────┤   │
│  │  Permissions & Authentication        │   │
│  └──────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Business Logic Layer              │
│  ┌──────────────────────────────────────┐   │
│  │  Models (ORM)                        │   │
│  ├──────────────────────────────────────┤   │
│  │  Custom Managers & QuerySets        │   │
│  ├──────────────────────────────────────┤   │
│  │  Signals & Middleware               │   │
│  └──────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Data Persistence Layer             │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │   PostgreSQL    │  │  File Storage    │  │
│  │   (Primary DB)  │  │  (R2/Local)      │  │
│  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────┘
```

### Application Modules

```
MY_OMEGA_BACKEND/
├── login/              # Authentication & JWT token management
├── User/               # User model & profile management
├── user_controll/      # RBAC & menu access control
├── cv_management/      # CV processing & job applications
├── interview_management/ # Interview workflow & evaluations
├── HR/                 # HR operations & attendance
├── common/             # Shared utilities & storage backends
└── myomega_backend/    # Core settings & configuration
```

---

## 🛠️ Tech Stack

### Backend Framework
- **Django 5.2.7** - High-level Python web framework
- **Django REST Framework 3.16.1** - Powerful toolkit for building Web APIs
- **djangorestframework-simplejwt** - JWT authentication for DRF

### Database
- **PostgreSQL** - Advanced open-source relational database
- **psycopg2** - PostgreSQL adapter for Python

### Storage
- **Cloudflare R2** - S3-compatible object storage
- **django-storages** - Custom storage backends
- **boto3** - AWS SDK for Python (R2 compatibility)

### Media Processing
- **Pillow 12.0.0** - Python Imaging Library

### Development Tools
- **python-dotenv** - Environment variable management
- **django-cors-headers** - CORS handling

---

## 📦 Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **PostgreSQL 12+** ([Download](https://www.postgresql.org/download/))
- **pip** (Python package manager)
- **virtualenv** or **venv** (Python virtual environment)
- **Git** ([Download](https://git-scm.com/downloads))

### Optional
- **Postman** or **curl** - For API testing
- **pgAdmin** - PostgreSQL GUI client
- **Docker** - For containerized deployment

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/imcbsglobal/MY_OMEGA_BACKEND.git
cd MY_OMEGA_BACKEND
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env
# Database Configuration
DB_NAME=myomega_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # minutes (1 day)

# Cloudflare R2 Storage (Optional)
CLOUDFLARE_R2_ENABLED=false
CLOUDFLARE_R2_ACCESS_KEY=your_r2_access_key
CLOUDFLARE_R2_SECRET_KEY=your_r2_secret_key
CLOUDFLARE_R2_BUCKET_NAME=myomega-files
CLOUDFLARE_R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
CLOUDFLARE_R2_REGION_NAME=auto

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. Setup PostgreSQL Database

**Create Database:**
```sql
-- Login to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE myomega_db;

-- Create user (optional)
CREATE USER myomega_user WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE myomega_db TO myomega_user;

-- Exit
\q
```

### 6. Run Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Run Development Server

```bash
python manage.py runserver
```

Server will start at: `http://127.0.0.1:8000/`

**Admin Panel:** `http://127.0.0.1:8000/admin/`

---

## 🔧 Configuration

### Database Configuration

Edit `myomega_backend/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'myomega_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'admin'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://localhost:5173",  # Vite default
    "http://localhost:8080",  # Vue default
]

CORS_ALLOW_CREDENTIALS = True
```

### Cloudflare R2 Storage

```python
if CLOUDFLARE_R2_ENABLED:
    DEFAULT_FILE_STORAGE = 'common.storage_backends.R2MediaStorage'
    AWS_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('CLOUDFLARE_R2_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = os.getenv('CLOUDFLARE_R2_ENDPOINT_URL')
    AWS_S3_REGION_NAME = os.getenv('CLOUDFLARE_R2_REGION_NAME', 'auto')
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

---

## 📊 Database Schema

### Core Models Overview

#### User Module
- **AppUser** - Extended Django user with job roles, contact info, and documents
- Custom user manager with email-based authentication

#### CV Management
- **JobTitle** - Available job positions
- **UserCvData** - Candidate CVs with interview status tracking

#### Interview Management
- **Interview** - Interview scheduling and status
- **InterviewEvaluation** - Comprehensive evaluation metrics

#### User Control
- **MenuItem** - Dynamic menu structure
- **UserMenuAccess** - Role-based menu permissions

#### HR Module
- **Attendance** - Employee check-in/check-out
- **Break** - Break time tracking

### Key Relationships

```
AppUser (1) ──────── (N) UserCvData (created_by)
                          │
                          │ (1)
                          │
                          ▼
                      Interview (N) ──────── (1) InterviewEvaluation
                          │
                          │ (N)
                          │
                      AppUser (interviewer)

MenuItem (1) ──────── (N) UserMenuAccess ──────── (N) AppUser
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login/` | User login (returns JWT tokens) |
| POST | `/token/refresh/` | Refresh access token |
| POST | `/logout/` | User logout |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/` | List all users |
| POST | `/users/` | Create new user |
| GET | `/users/{id}/` | Get user details |
| PUT/PATCH | `/users/{id}/` | Update user |
| DELETE | `/users/{id}/` | Delete user |

### CV Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cv-management/cvs/` | List all CVs |
| POST | `/cv-management/cvs/` | Upload new CV |
| GET | `/cv-management/cvs/{id}/` | Get CV details |
| PUT/PATCH | `/cv-management/cvs/{id}/` | Update CV |
| DELETE | `/cv-management/cvs/{id}/` | Delete CV |
| GET | `/cv-management/job-titles/` | List job titles |

### Interview Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/interview-management/` | List all interviews |
| GET | `/interview-management/cvs-for-interview/` | Get CVs for dropdown |
| POST | `/interview-management/start-interview/` | Start new interview |
| GET | `/interview-management/ongoing-interviews/` | List ongoing interviews |
| GET | `/interview-management/{id}/` | Get interview details |
| PATCH | `/interview-management/{id}/update-status/` | Update interview status |
| POST/PUT/PATCH | `/interview-management/{id}/evaluation/` | Create/update evaluation |
| DELETE | `/interview-management/{id}/` | Delete interview |

### HR Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/hr/attendance/` | List attendance records |
| POST | `/hr/attendance/check-in/` | Check-in |
| POST | `/hr/attendance/check-out/` | Check-out |
| GET | `/hr/breaks/` | List breaks |
| POST | `/hr/breaks/` | Record break |

### User Access Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user-controll/menu-items/` | List menu items |
| GET | `/user-controll/user-menu/` | Get user's accessible menus |
| POST | `/user-controll/assign-menu/` | Assign menu to user |

### Detailed Documentation

For comprehensive API documentation with request/response examples, see:
- **CV Management:** [`doc/cv_api_documentation.md`](doc/cv_api_documentation.md)
- **Interview Management:** [`doc/interview_management_api_documentation.md`](doc/interview_management_api_documentation.md)

---

## 📁 Project Structure

```
MY_OMEGA_BACKEND/
│
├── myomega_backend/          # Core Django project settings
│   ├── __init__.py
│   ├── settings.py           # Main configuration
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
│
├── login/                    # Authentication module
│   ├── models.py            # Auth models
│   ├── views.py             # Login/logout views
│   ├── serializers.py       # Auth serializers
│   ├── auth.py              # Custom authentication
│   └── urls.py
│
├── User/                     # User management module
│   ├── models.py            # AppUser model
│   ├── views.py             # User CRUD operations
│   ├── serializers.py       # User serializers
│   └── urls.py
│
├── user_controll/           # Access control module
│   ├── models.py            # MenuItem, UserMenuAccess
│   ├── views.py             # Permission management
│   ├── permissions.py       # Custom permissions
│   ├── management/          # Management commands
│   │   └── commands/
│   │       └── seed_menu_items.py
│   └── urls.py
│
├── cv_management/           # CV processing module
│   ├── models.py            # UserCvData, JobTitle
│   ├── views.py             # CV CRUD operations
│   ├── serializers.py       # CV serializers
│   └── urls.py
│
├── interview_management/    # Interview workflow module
│   ├── models.py            # Interview, InterviewEvaluation
│   ├── views.py             # Interview operations
│   ├── serializers.py       # Interview serializers
│   └── urls.py
│
├── HR/                      # HR operations module
│   ├── models.py            # Attendance, Break
│   ├── views.py             # HR operations
│   ├── Serializers.py       # HR serializers
│   └── urls.py
│
├── common/                  # Shared utilities
│   └── storage_backends.py  # Custom storage backends
│
├── doc/                     # API documentation
│   ├── cv_api_documentation.md
│   └── interview_management_api_documentation.md
│
├── media/                   # User-uploaded files (dev only)
│   ├── cvs/
│   ├── user_photos/
│   └── user_documents/
│
├── staticfiles/             # Collected static files
│
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
├── .env                    # Environment variables (not in git)
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

---

## 💻 Development Guide

### Setting Up Development Environment

1. **Install development dependencies:**
```bash
pip install -r requirements.txt
pip install black flake8 pytest pytest-django  # Optional dev tools
```

2. **Code formatting (Black):**
```bash
black .
```

3. **Linting (Flake8):**
```bash
flake8 --max-line-length=120 --exclude=venv,migrations
```

### Creating a New App

```bash
python manage.py startapp new_app_name
```

Then:
1. Add to `INSTALLED_APPS` in `settings.py`
2. Create models, views, serializers
3. Add URLs to main `urls.py`
4. Run migrations

### Database Operations

**Create migrations:**
```bash
python manage.py makemigrations
```

**Apply migrations:**
```bash
python manage.py migrate
```

**Rollback migration:**
```bash
python manage.py migrate app_name migration_number
```

**Show migrations:**
```bash
python manage.py showmigrations
```

**SQL for migration:**
```bash
python manage.py sqlmigrate app_name migration_number
```

### Django Shell

```bash
python manage.py shell
```

```python
# Example: Query users
from User.models import AppUser
users = AppUser.objects.all()
for user in users:
    print(user.email, user.job_role)
```

### Custom Management Commands

```bash
# Seed menu items
python manage.py seed_menu_items
```

### API Testing with cURL

**Login:**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "yourpassword"}'
```

**Authenticated Request:**
```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use strong `SECRET_KEY` (generate with `get_random_secret_key()`)
- [ ] Setup PostgreSQL with proper credentials
- [ ] Configure HTTPS/SSL certificates
- [ ] Setup static file serving (Nginx/Whitenoise)
- [ ] Enable Cloudflare R2 for file storage
- [ ] Configure CORS for production frontend
- [ ] Setup logging and monitoring
- [ ] Create database backups
- [ ] Setup environment variables securely

### Production Settings

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Deployment with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn myomega_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

EXPOSE 8000

CMD ["gunicorn", "myomega_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myomega_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn myomega_backend.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:your_password@db:5432/myomega_db

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test cv_management

# Run with coverage
coverage run manage.py test
coverage report
```

### Writing Tests

Example test file (`cv_management/tests.py`):

```python
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserCvData, JobTitle

class CVManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.job_title = JobTitle.objects.create(title="Developer")
    
    def test_create_cv(self):
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'job_title': self.job_title.id,
            'phone_number': '1234567890'
        }
        response = self.client.post('/api/cv-management/cvs/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

---

## 🔒 Security

### Best Practices Implemented

1. **JWT Authentication**
   - Token-based authentication
   - Token expiration and rotation
   - Secure token storage

2. **Password Security**
   - Django's built-in password hashing (PBKDF2)
   - Password validation rules
   - Minimum length requirements

3. **SQL Injection Protection**
   - Django ORM parameterized queries
   - No raw SQL queries

4. **CSRF Protection**
   - CSRF tokens for state-changing operations
   - CORS configuration for API access

5. **Data Validation**
   - DRF serializer validation
   - Model-level constraints
   - Custom validators

6. **File Upload Security**
   - File type validation
   - Size limits
   - Secure file storage

### Security Recommendations

- Always use HTTPS in production
- Keep dependencies updated (`pip list --outdated`)
- Regular security audits
- Implement rate limiting
- Setup logging and monitoring
- Regular database backups
- Use environment variables for secrets
- Implement API versioning

---

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make changes and commit:**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open Pull Request**

### Coding Standards

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Write docstrings for functions and classes
- Add comments for complex logic
- Write tests for new features
- Update documentation

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Example:**
```
feat(interview): Add voice note support to evaluations

- Added voice_note field to InterviewEvaluation model
- Updated serializer to handle file uploads
- Added file validation

Closes #123
```

---

## 📞 Support & Contact

- **Documentation:** [API Docs](doc/)
- **Issues:** [GitHub Issues](https://github.com/imcbsglobal/MY_OMEGA_BACKEND/issues)
- **Repository:** [GitHub](https://github.com/imcbsglobal/MY_OMEGA_BACKEND)

---

## 📄 License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

**Copyright © 2025 IMCBS Global. All rights reserved.**

---

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- PostgreSQL team
- Cloudflare for R2 storage
- All contributors and team members

---

## 📈 Roadmap

### Version 1.1 (Planned)
- [ ] Real-time notifications (WebSocket)
- [ ] Advanced reporting and analytics
- [ ] Email notifications for interviews
- [ ] Bulk CV import
- [ ] Interview scheduling calendar integration

### Version 1.2 (Future)
- [ ] AI-powered CV parsing
- [ ] Video interview integration
- [ ] Mobile application
- [ ] Multi-language support
- [ ] Advanced search and filtering

---

## 📝 Changelog

### v1.0.0 (Current)
- Initial release
- Core authentication system
- CV management module
- Interview management workflow
- HR operations module
- User access control
- Cloudflare R2 integration

---

**Built with ❤️ by the IMCBS Global Team**

*Last Updated: November 11, 2025*
