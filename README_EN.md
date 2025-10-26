### 🏠 MietSystem — Housing Rental Platform

A modern backend application for property rentals in Germany with multi-role support (Admin, Landlord, Tenant), separate dashboards, and an access control system.
The platform provides a fully featured system for property management, booking, reviews, and analytics.

### ✨ Key Features

### 🏠 Listing Management

* Create, edit, and delete listings
* Multilingual titles and descriptions (DE/EN/RU)
* Image upload (JPEG/PNG ≤ 5 MB)
* Availability calendar management
* Listing activity status

### 🔍 Search and Filtering

* FULLTEXT search by titles and descriptions
* Filtering by price, rooms, and property type
* Sorting by popularity, price, or date
* Pagination (20 items per page)
* Caching results in Redis

### 👥 Role System

* **Tenant**: search, booking, reviews
* **Landlord**: manage listings and bookings
* **Admin**: full access to all features

### 📅 Bookings

* Create bookings with availability checks
* Automatic price calculation
* Landlord confirmation or rejection
* Booking cancellation (up to 48 hours before)

### ⭐ Reviews and Ratings

* Reviews available after booking completion
* Admin moderation
* Cached average rating
* Landlord responses to reviews

### 📊 Analytics

* Popularity calculation (views × 0.3 + reviews × 0.5 + time_decay × 0.2)
* User search history
* Listing view history
* Analytics export to CSV

## 🛠 Tech Stack

### Backend

* **Python 3.11**
* **Django 5.0**
* **Django REST Framework**
* **MySQL 8.0** (with FULLTEXT, JSON, and indexes)
* **Redis 7.0** (caching, ElastiCache)
* **Celery + RabbitMQ** (asynchronous tasks)

### Frontend (Dashboard)

* **Django Admin Panel**
* **DRF Browsable API**
* **Swagger / Redoc** (drf-spectacular)
* **Multilingual interface** (DE/EN/RU)

### Security

* **JWT authentication** (SimpleJWT)
* **2FA** (TOTP)
* **Rate limiting** (100 req/min)
* **django-axes** (brute-force protection)
* **CSRF / XSS protection**

### 📁 Project Structure

```
Project_MietSystem/
├── analytics/          # Analytics and statistics
├── bookings/           # Booking system
├── core/               # Core app (routing, settings, middleware)
├── listings/           # Property listings
├── locations/          # Geolocation and maps
├── reviews/            # Reviews and ratings
├── users/              # User and role management
├── utils/              # Utility functions
├── templates/          # Dashboard templates
├── static/             # Static files
├── media/              # Media files
├── tests/              # Tests
├── docs/               # Documentation
├── docker-compose.yml  # Docker configuration
├── Dockerfile          # Docker image
├── requirements.txt    # Dependencies
└── manage.py           # Django manage script
```

### Data Models

* **User**: users with roles (Tenant / Landlord / Admin)
* **Listing**: property listings
* **Booking**: bookings with statuses
* **Review**: reviews and ratings
* **Location**: geolocation with coordinates
* **SearchHistory**: user search history
* **ViewHistory**: listing view history

### Local Setup

```bash
# Clone the repository
git clone <repository-url>
cd MietSystem

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure the database
# Create a MySQL database and update settings.py

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver 8001
```

## 📡 API Documentation

### Available Endpoints

* `/api/users/` – user management
* `/api/listings/` – property listings
* `/api/bookings/` – booking system
* `/api/reviews/` – reviews and ratings
* `/api/analytics/` – analytics
* `/api/docs/` – Swagger documentation
* `/admin/` – Django admin panel

### Response Format

```
json
// Success response
{
  "data": {
    "id": 42,
    "title": "Apartment in central Berlin",
    "price_per_night": 89.99
  },
  "meta": {
    "total_results": 127,
    "page": 1
  }
}

// Error
{
  "error": {
    "code": "INVALID_DATE",
    "message": "Booking dates overlap with existing booking",
    "status": 400
  }
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Load testing
locust -f tests/locustfile.py
```

### Test Coverage

* **Target**: ≥ 80 % code coverage
* **Unit tests**: models, serializers, permissions
* **Integration tests**: API endpoints
* **Load tests**: Locust (up to 1000 RPS)

## 🛡 Security

### Authentication

* JWT tokens (access + refresh)
* HttpOnly cookies + CSRF protection
* 2FA (TOTP) for enhanced security
* Password reset via email

### Protection

* Rate limiting (100 requests/minute)
* django-axes (brute-force protection)
* Argon2 password hashing
* XSS and CSRF protection

### Pre-commit Hooks

```bash
# Install pre-commit
pre-commit install

# Run all hooks
pre-commit run --all-files
```

## 📊 Monitoring

### Sentry

* Real-time error monitoring
* Request tracing
* Performance profiling

### Logging

* Detailed activity logging
* Error and warning logs
* Log rotation

## 👥 User Roles

### Tenant

* Search and filter listings
* Create bookings
* Leave reviews
* View and edit profile

### Landlord

* CRUD operations for own listings
* Manage bookings
* Reply to reviews
* Property analytics

### Admin

* Full access to all functionality
* Content moderation
* User management
* Analytics export

## 🌍 Localization

### Supported Languages

* 🇩🇪 German
* 🇬🇧 English
* 🇷🇺 Russian

### Currencies

* **EUR** – primary currency
* Support for additional currencies planned

### Geography

* German federal states
* Cities and regions
* Address format (Street, ZIP, City)

## 📈 Development Roadmap

### Short-Term Plans

* Docker / Kubernetes → production deployment on AWS
* Map integration (OpenStreetMap / Google Maps)
* Built-in messenger between tenant and landlord
* Notifications via SMS and WebPush
* Multi-currency support

### Long-Term Goals

* Expansion to other countries
* ML-based recommendation system
* Mobile app (iOS / Android)
* Integration with payment systems (Stripe, PayPal)

## 📞 Contacts

**Developer**: Alex Sidorenko (email:alexgruening@icloud.com)
*The project is built following modern web development best practices.*
