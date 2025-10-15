"""
Tests for AuthProvider
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta

from src.services.auth import AuthProvider


class TestAuthProvider:
    """Test AuthProvider functionality"""
    
    @pytest.fixture
    def auth_provider(self):
        """Create AuthProvider instance for testing"""
        return AuthProvider(
            domain="test.auth0.com",
            audience="test-audience",
            algorithms=["RS256"]
        )
    
    @pytest.fixture
    def valid_payload(self):
        """Sample valid JWT payload"""
        return {
            "sub": "auth0|123456789",
            "aud": "test-audience",
            "iss": "https://test.auth0.com/",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "scope": "read:profile write:profile",
            "permissions": ["read:events", "write:events"]
        }
    
    @pytest.fixture
    def expired_payload(self):
        """Sample expired JWT payload"""
        return {
            "sub": "auth0|123456789",
            "aud": "test-audience",
            "iss": "https://test.auth0.com/",
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),  # Expired
            "iat": int(datetime.utcnow().timestamp()),
            "scope": "read:profile",
            "permissions": ["read:events"]
        }
    
    def test_auth_provider_initialization(self, auth_provider):
        """Test AuthProvider initializes correctly"""
        assert auth_provider.issuer == "https://test.auth0.com/"
        assert auth_provider.audience == "test-audience"
        assert auth_provider.algorithms == ["RS256"]
        assert auth_provider.jwks_url == "https://test.auth0.com/.well-known/jwks.json"
        assert auth_provider.jwk_client is not None
        assert auth_provider.bearer is not None
    
    @patch('src.services.auth.jwt.decode')
    @patch.object(AuthProvider, '__init__', lambda x, domain, audience, algorithms: None)
    def test_verify_jwt_valid_token(self, mock_jwt_decode, valid_payload):
        """Test verifying valid JWT token"""
        # Setup
        auth_provider = AuthProvider.__new__(AuthProvider)
        auth_provider.algorithms = ["RS256"]
        auth_provider.audience = "test-audience"
        auth_provider.issuer = "https://test.auth0.com/"
        auth_provider.jwk_client = Mock()
        auth_provider.jwk_client.get_signing_key_from_jwt.return_value.key = "test-key"
        
        mock_jwt_decode.return_value = valid_payload
        
        # Test
        result = auth_provider.verify_jwt("valid.jwt.token")
        
        # Assertions
        assert result == valid_payload
        mock_jwt_decode.assert_called_once_with(
            "valid.jwt.token",
            "test-key",
            algorithms=["RS256"],
            audience="test-audience",
            issuer="https://test.auth0.com/"
        )
    
    @patch('src.services.auth.jwt.decode')
    @patch.object(AuthProvider, '__init__', lambda x, domain, audience, algorithms: None)
    def test_verify_jwt_expired_token(self, mock_jwt_decode):
        """Test verifying expired JWT token raises HTTPException"""
        # Setup
        auth_provider = AuthProvider.__new__(AuthProvider)
        auth_provider.algorithms = ["RS256"]
        auth_provider.audience = "test-audience"
        auth_provider.issuer = "https://test.auth0.com/"
        auth_provider.jwk_client = Mock()
        auth_provider.jwk_client.get_signing_key_from_jwt.return_value.key = "test-key"
        
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
        
        # Test & Assert
        with pytest.raises(HTTPException) as exc_info:
            auth_provider.verify_jwt("expired.jwt.token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token expired"
    
    @patch('src.services.auth.jwt.decode')
    @patch.object(AuthProvider, '__init__', lambda x, domain, audience, algorithms: None)
    def test_verify_jwt_invalid_token(self, mock_jwt_decode):
        """Test verifying invalid JWT token raises HTTPException"""
        # Setup
        auth_provider = AuthProvider.__new__(AuthProvider)
        auth_provider.algorithms = ["RS256"]
        auth_provider.audience = "test-audience"
        auth_provider.issuer = "https://test.auth0.com/"
        auth_provider.jwk_client = Mock()
        auth_provider.jwk_client.get_signing_key_from_jwt.return_value.key = "test-key"
        
        mock_jwt_decode.side_effect = jwt.InvalidTokenError("Invalid token")
        
        # Test & Assert
        with pytest.raises(HTTPException) as exc_info:
            auth_provider.verify_jwt("invalid.jwt.token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
    
    def test_require_permissions_with_permissions_array(self, auth_provider):
        """Test require_permissions with permissions in payload"""
        payload = {
            "sub": "auth0|123456789",
            "permissions": ["read:events", "write:events", "admin:users"]
        }
        
        # Create dependency function
        dependency = auth_provider.require_permissions("read:events", "write:events")
        
        # Test - should pass since user has required permissions
        result = dependency(payload)
        assert result == payload
    
    def test_require_permissions_with_scope_string(self, auth_provider):
        """Test require_permissions with scope string in payload"""
        payload = {
            "sub": "auth0|123456789",
            "scope": "read:events write:events admin:users"
        }
        
        # Create dependency function
        dependency = auth_provider.require_permissions("read:events", "write:events")
        
        # Test - should pass since user has required permissions in scope
        result = dependency(payload)
        assert result == payload
    
    def test_require_permissions_insufficient_permissions(self, auth_provider):
        """Test require_permissions with insufficient permissions"""
        payload = {
            "sub": "auth0|123456789",
            "permissions": ["read:events"]  # Missing write:events
        }
        
        # Create dependency function
        dependency = auth_provider.require_permissions("read:events", "write:events")
        
        # Test - should raise HTTPException due to missing permissions
        with pytest.raises(HTTPException) as exc_info:
            dependency(payload)
        
        assert exc_info.value.status_code == 403
        assert "Missing required permissions" in exc_info.value.detail
    
    def test_require_permissions_no_permissions_in_payload(self, auth_provider):
        """Test require_permissions with no permissions in payload"""
        payload = {
            "sub": "auth0|123456789"
            # No permissions or scope
        }
        
        # Create dependency function
        dependency = auth_provider.require_permissions("read:events")
        
        # Test - should raise HTTPException due to missing permissions
        with pytest.raises(HTTPException) as exc_info:
            dependency(payload)
        
        assert exc_info.value.status_code == 403
        assert "Missing required permissions" in exc_info.value.detail
    
    def test_require_permissions_empty_requirements(self, auth_provider):
        """Test require_permissions with no required permissions"""
        payload = {
            "sub": "auth0|123456789",
            "permissions": []
        }
        
        # Create dependency function with no required permissions
        dependency = auth_provider.require_permissions()
        
        # Test - should pass since no permissions are required
        result = dependency(payload)
        assert result == payload
    
    def test_require_permissions_mixed_permissions_and_scope(self, auth_provider):
        """Test require_permissions prefers permissions over scope"""
        payload = {
            "sub": "auth0|123456789",
            "permissions": ["read:events"],  # Has read but not write
            "scope": "read:events write:events"  # Scope has both
        }
        
        # Create dependency function
        dependency = auth_provider.require_permissions("read:events", "write:events")
        
        # Test - should fail because permissions array takes precedence over scope
        with pytest.raises(HTTPException) as exc_info:
            dependency(payload)
        
        assert exc_info.value.status_code == 403
    
    def test_require_permissions_subset_check(self, auth_provider):
        """Test that all required permissions must be present"""
        payload = {
            "sub": "auth0|123456789",
            "permissions": ["read:events", "write:events", "delete:events", "admin:users"]
        }
        
        # Create dependency function requiring subset of user's permissions
        dependency = auth_provider.require_permissions("read:events", "write:events")
        
        # Test - should pass since user has all required permissions (and more)
        result = dependency(payload)
        assert result == payload
    
    def test_auth_provider_with_different_algorithms(self):
        """Test AuthProvider with different algorithm"""
        auth_provider = AuthProvider(
            domain="test.auth0.com",
            audience="test-audience",
            algorithms=["HS256"]
        )
        
        assert auth_provider.algorithms == ["HS256"]
    
    def test_auth_provider_with_multiple_algorithms(self):
        """Test AuthProvider with multiple algorithms"""
        auth_provider = AuthProvider(
            domain="test.auth0.com",
            audience="test-audience",
            algorithms=["RS256", "HS256"]
        )
        
        assert auth_provider.algorithms == ["RS256", "HS256"]