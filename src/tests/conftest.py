"""
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client for FastAPI app
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for FastAPI app
    """
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    from uuid import uuid4
    return uuid4()


@pytest.fixture
def sample_event_id():
    """Sample event ID for testing"""
    from uuid import uuid4
    return uuid4()


@pytest.fixture
def sample_opportunity_id():
    """Sample opportunity ID for testing"""
    from uuid import uuid4
    return uuid4()


@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    from datetime import datetime, timedelta
    return {
        "title": "Test Event",
        "description": "A test event for unit testing",
        "location": {
            "name": "Test Location",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TX",
            "postal_code": "12345"
        },
        "required_skills": ["python", "testing"],
        "starts_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "ends_at": (datetime.now() + timedelta(days=1, hours=2)).isoformat(),
        "capacity": 10
    }


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "display_name": "Test User",
        "phone": "+1234567890",
        "skills": ["python", "testing", "fastapi"],
        "tags": ["volunteer", "developer"],
        "availability": [
            {
                "weekday": 1,  # Monday
                "start_time": "09:00:00",
                "end_time": "17:00:00"
            },
            {
                "weekday": 5,  # Friday
                "start_time": "10:00:00",
                "end_time": "16:00:00"
            }
        ]
    }


@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing"""
    return {
        "recipient_id": "550e8400-e29b-41d4-a716-446655440000",
        "subject": "Test Notification",
        "body": "This is a test notification body",
        "notification_type": "event_assignment",
        "priority": "normal"
    }