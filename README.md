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
- **Authentication**: Auth0 JWT tokens
- **Validation**: Pydantic models with comprehensive validation
- **Testing**: Pytest with coverage reporting
- **Documentation**: Auto-generated OpenAPI/Swagger docs

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
make test          # Run tests
make coverage      # Run tests with coverage
make lint          # Run linting
make format        # Format code
```

<!-- ## License

This project is licensed under the terms specified in the repository. -->
