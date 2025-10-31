# Volunteer Management System API

A comprehensive FastAPI-based backend system for managing volunteer events, profiles, matching, history tracking, and notifications.

## Overview

The Volunteer Management System provides a robust platform for organizations to manage volunteer activities, track participation history, match volunteers with opportunities, and maintain communication through notifications.

## Features

- **Event Management**: Create, update, publish, and manage volunteer events
- **Profile Management**: Comprehensive volunteer profile system with skills and availability
- **Volunteer Matching**: Intelligent matching system between volunteers and opportunities
- **History Tracking**: Complete volunteer participation history and statistics
- **Notification System**: Multi-channel notification management with preferences
- **Authentication**: Auth0-based JWT authentication with role-based permissions

## Tech Stack

- **Framework**: FastAPI 0.115.11
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **Authentication**: Auth0 JWT tokens
- **Validation**: Pydantic models with comprehensive validation
- **Testing**: Pytest with coverage reporting
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## Database Layer

The application uses SQLAlchemy ORM with the Repository pattern and Unit of Work for clean separation between business logic and data access.

### Architecture

```
Domain Layer (Pure Business Logic)
├── domain/
│   ├── users.py           # User entities and value objects
│   ├── profiles.py        # Profile entities  
│   ├── events.py          # Event entities
│   ├── volunteering.py    # Volunteering entities (opportunities, matches, etc.)
│   ├── notifications.py   # Notification entities
│   └── repositories.py   # Repository interfaces (protocols)

Repository Layer (Data Access)
├── repositories/
│   ├── models.py              # SQLAlchemy database models
│   ├── sqlalchemy_repositories.py  # Repository implementations
│   ├── unit_of_work.py       # Transaction management
│   ├── database.py           # Database configuration and setup
│   └── migrations.py         # Database migration utilities
├── config/
│   └── database_settings.py  # FastAPI integration and initialization
```

### Database Models

The following entities are mapped to database tables:

- **Users** - User accounts with Auth0 integration (`auth0_sub` field)
- **Profiles** - User profiles with skills, availability, etc.
- **Events** - Volunteer events with location and capacity
- **Opportunities** - Specific volunteer roles within events
- **Matches** - Confirmed volunteer assignments
- **Match Requests** - Pending volunteer applications
- **Notifications** - System notifications with delivery status
- **Volunteer History** - Historical volunteer activity records

### Database Configuration

Configure the PostgreSQL database using environment variables:

```bash
# Database URL (recommended)
DATABASE_URL=postgresql://user:password@localhost/volunteer_management

# Or individual components (for development)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=volunteer_management
DATABASE_USER=postgres
DATABASE_PASSWORD=password
```

For development, you can use default values if no environment variables are set:
- Host: localhost
- Port: 5432
- Database: volunteer_management
- User: postgres
- Password: postgres

### Database Commands

Use the Makefile for database operations (migrations are bootstrapped automatically):

```bash
# Initialize PostgreSQL database and create tables
make db-init

# Check database connection
make db-check

# Drop all tables (WARNING: destructive!)
make db-drop

# Reset database (drop + recreate all tables)
make db-reset
```

The database tables are automatically created when you run `make db-init`. No separate migration files are needed - the schema is defined in the SQLAlchemy models and created directly.

### Using Repositories in Code

The application uses the Unit of Work pattern for database transactions:

```python
from src.config.database_settings import get_uow

# In FastAPI routes
@app.post("/users/")
def create_user(user_data: dict, uow = Depends(get_uow)):
    with uow_manager.get_uow() as uow:
        user = User(...)
        uow.users.add(user)
        uow.commit()

# In services
def create_user_profile(user_id: str, profile_data: dict):
    with uow_manager.get_uow() as uow:
        # Find user
        user = uow.users.get_by_auth0_sub(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Create profile
        profile = Profile(user_id=user.id, ...)
        uow.profiles.save(profile)
        
        # Commit transaction
        uow.commit()
```

### Auth0 Integration

Since authentication is handled by Auth0:

- Users are linked via `auth0_sub` field (Auth0 subject identifier)
- No passwords or local authentication tokens are stored
- User lookup supports both email and Auth0 sub: `get_by_email()`, `get_by_auth0_sub()`

### Health Checks

Database health is monitored through API endpoints:

- `GET /health` - General application health
- `GET /health/database` - Database connection status and configuration

## Quick Start

### Installation

```bash
# Clone the repository
git clone git@github.com:kobetyleryoung/COSC-4353-backend.git
cd COSC-4353-backend

# Install dependencies
pip install -r requirements.txt

# Start the development server
make run
```

### API Documentation

- Interactive API docs: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/health`

## API Endpoints

### Core Endpoints

#### Health Check
- `GET /health` - System health status

### Events API (`/api/v1/events`)

#### Event Management
- `GET /` - List all events
- `GET /published` - List published events only
- `GET /upcoming` - List upcoming events
- `GET /{event_id}` - Get specific event details
- `POST /` - Create new event
- `PUT /{event_id}` - Update existing event
- `DELETE /{event_id}` - Delete event

#### Event Operations
- `POST /{event_id}/publish` - Publish event
- `POST /{event_id}/cancel` - Cancel event
- `POST /search` - Search events by criteria

### Profile API (`/api/v1/profile`)

#### Profile Management
- `GET /` - List all profiles
- `GET /{user_id}` - Get user profile
- `POST /` - Create new profile
- `PUT /{user_id}` - Update profile
- `DELETE /{user_id}` - Delete profile

#### Skills Management
- `POST /{user_id}/skills` - Add skills to profile
- `DELETE /{user_id}/skills/{skill}` - Remove skill from profile

#### Tags Management
- `POST /{user_id}/tags` - Add tags to profile
- `DELETE /{user_id}/tags/{tag}` - Remove tag from profile

#### Availability Management
- `POST /{user_id}/availability` - Set user availability
- `DELETE /{user_id}/availability` - Clear availability

#### Profile Search & Stats
- `GET /search/by-skills` - Search profiles by skills
- `GET /search/by-tags` - Search profiles by tags
- `GET /{user_id}/stats` - Get profile statistics

### Volunteer Matching API (`/api/v1/volunteer-matching`)

#### Opportunities
- `GET /opportunities` - List all opportunities
- `GET /opportunities/{opportunity_id}` - Get specific opportunity
- `GET /opportunities/by-event/{event_id}` - Get opportunities for event
- `POST /opportunities` - Create new opportunity

#### Match Requests
- `POST /match-requests` - Create match request
- `GET /match-requests/by-opportunity/{opportunity_id}` - Get requests for opportunity
- `GET /match-requests/by-user/{user_id}` - Get user's match requests
- `POST /match-requests/{request_id}/approve` - Approve match request
- `POST /match-requests/{request_id}/reject` - Reject match request

#### Matches
- `GET /matches/by-user/{user_id}` - Get user's matches
- `GET /matches/by-opportunity/{opportunity_id}` - Get opportunity matches
- `DELETE /matches/{match_id}` - Remove match

#### Matching Algorithms
- `GET /find-volunteers/{opportunity_id}` - Find suitable volunteers
- `GET /find-opportunities/{user_id}` - Find suitable opportunities

#### Maintenance
- `POST /expire-old-requests` - Expire old match requests

### Volunteer History API (`/api/v1/volunteer-history`)

#### History Management
- `GET /` - List all history entries
- `GET /{entry_id}` - Get specific history entry
- `GET /user/{user_id}` - Get user's volunteer history
- `GET /event/{event_id}` - Get event's volunteer history
- `POST /` - Create history entry
- `PUT /{entry_id}` - Update history entry
- `DELETE /{entry_id}` - Delete history entry

#### Statistics & Analytics
- `GET /user/{user_id}/total-hours` - Get user's total volunteer hours
- `GET /user/{user_id}/hours-in-period` - Get hours in specific period
- `GET /user/{user_id}/event-count` - Get user's event participation count
- `GET /user/{user_id}/roles` - Get user's volunteer roles summary
- `GET /user/{user_id}/statistics` - Get comprehensive user statistics
- `GET /user/{user_id}/monthly-hours/{year}` - Get monthly hours for year

#### Leaderboards
- `GET /top-volunteers/by-hours` - Top volunteers by hours contributed
- `GET /top-volunteers/by-events` - Top volunteers by events attended

### Notifications API (`/api/v1/notifications`)

#### User Notifications
- `GET /user/{user_id}` - Get user notifications
- `GET /user/{user_id}/unread-count` - Get unread notification count
- `POST /{notification_id}/mark-read` - Mark notification as read

#### Notification Types
- `POST /send` - Send general notification
- `POST /event-assignment` - Send event assignment notification
- `POST /event-reminder` - Send event reminder
- `POST /event-update` - Send event update notification
- `POST /event-cancellation` - Send event cancellation notification
- `POST /match-request-approved` - Send match approval notification
- `POST /match-request-rejected` - Send match rejection notification
- `POST /new-opportunity` - Send new opportunity notification

#### Notification Preferences
- `GET /user/{user_id}/preferences` - Get user notification preferences
- `PUT /user/{user_id}/preferences` - Update notification preferences

#### System Operations
- `GET /pending` - Get pending notifications
- `POST /retry-failed` - Retry failed notifications

## Data Models

### Event
- **id**: Unique identifier
- **title**: Event title (1-100 characters)
- **description**: Event description (1-500 characters)
- **location**: Location object with address details
- **required_skills**: List of required skills
- **starts_at**: Event start datetime
- **ends_at**: Event end datetime (optional)
- **capacity**: Maximum participants (optional)
- **status**: Event status (draft, published, cancelled)

### Profile
- **id**: Unique identifier
- **user_id**: Associated user ID
- **full_name**: User's full name
- **address**: Address information
- **skills**: List of user skills
- **preferences**: User preferences
- **availability**: User availability schedule

### Opportunity
- **id**: Unique identifier
- **event_id**: Associated event
- **title**: Opportunity title
- **description**: Detailed description
- **required_skills**: Required skills list
- **time_commitment**: Expected time commitment
- **location**: Opportunity location

### Match Request
- **id**: Unique identifier
- **user_id**: Requesting user
- **opportunity_id**: Target opportunity
- **status**: Request status (pending, approved, rejected)
- **created_at**: Request timestamp

### Notification
- **id**: Unique identifier
- **user_id**: Target user
- **type**: Notification type
- **message**: Notification content
- **is_read**: Read status
- **created_at**: Creation timestamp

## Authentication

The API uses Auth0 JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

Required permissions vary by endpoint and are enforced through Auth0 role-based access control.

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation errors)
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Unprocessable Entity
- **500**: Internal Server Error

Error responses include detailed messages and validation error details where applicable.

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/api/test_events.py
```

### Code Quality

The project uses comprehensive testing with pytest and includes:
- Unit tests for all services
- API endpoint tests
- Integration tests
- Code coverage reporting

### Makefile Commands

Common development commands are available through the Makefile:

```bash
# Development
make install       # Install dependencies
make dev          # Run development server with auto-reload
make run          # Run production server

# Testing
make test         # Run all tests with coverage
make test-unit    # Run unit tests only
make test-coverage # Run tests with detailed coverage
make test-html    # Generate HTML coverage report

# Code Quality
make lint         # Check code style
make format       # Format code
make clean        # Clean cache files

# Database
make db-init      # Initialize database tables
make db-check     # Check database connection
make db-drop      # Drop all tables (WARNING: destructive!)
make db-reset     # Drop and recreate all tables (WARNING: destructive!)
```

<!-- ## License

This project is licensed under the terms specified in the repository. -->
