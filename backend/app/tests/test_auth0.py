"""Tests for Auth0 authentication and authorization"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.core.auth0 import User, UserRole, Auth0TokenValidator, get_current_user


class TestUserRole:
    """Test UserRole enum"""

    def test_role_values(self):
        """Test role enum values"""
        assert UserRole.SUPERUSER.value == "superuser"
        assert UserRole.PROJECT_MANAGER.value == "project_manager"
        assert UserRole.STAFF.value == "staff"


class TestUser:
    """Test User model"""

    def test_user_creation(self):
        """Test creating a user"""
        user = User(
            sub="auth0|123456",
            email="test@example.com",
            roles=["superuser"],
            name="Test User",
        )

        assert user.sub == "auth0|123456"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.roles == ["superuser"]

    def test_has_role(self):
        """Test has_role method"""
        user = User(
            sub="auth0|123",
            email="pm@example.com",
            roles=["project_manager"],
        )

        assert user.has_role(UserRole.PROJECT_MANAGER) is True
        assert user.has_role(UserRole.SUPERUSER) is False
        assert user.has_role(UserRole.STAFF) is False

    def test_has_any_role(self):
        """Test has_any_role method"""
        user = User(
            sub="auth0|123",
            email="staff@example.com",
            roles=["staff"],
        )

        assert user.has_any_role(UserRole.STAFF, UserRole.PROJECT_MANAGER) is True
        assert user.has_any_role(UserRole.PROJECT_MANAGER, UserRole.SUPERUSER) is False

    def test_role_properties(self):
        """Test role property shortcuts"""
        superuser = User(sub="auth0|1", email="admin@example.com", roles=["superuser"])
        assert superuser.is_superuser is True
        assert superuser.is_project_manager is False
        assert superuser.is_staff is False

        pm = User(sub="auth0|2", email="pm@example.com", roles=["project_manager"])
        assert pm.is_superuser is False
        assert pm.is_project_manager is True
        assert pm.is_staff is False

        staff = User(sub="auth0|3", email="staff@example.com", roles=["staff"])
        assert staff.is_superuser is False
        assert staff.is_project_manager is False
        assert staff.is_staff is True

    def test_multiple_roles(self):
        """Test user with multiple roles"""
        user = User(
            sub="auth0|4",
            email="multi@example.com",
            roles=["staff", "project_manager"],
        )

        assert user.has_role(UserRole.STAFF) is True
        assert user.has_role(UserRole.PROJECT_MANAGER) is True
        assert user.has_role(UserRole.SUPERUSER) is False


class TestAuth0TokenValidator:
    """Test Auth0TokenValidator"""

    @patch("app.core.auth0.settings")
    def test_validator_disabled(self, mock_settings):
        """Test validator when Auth0 is disabled"""
        mock_settings.auth0_enabled = False
        mock_settings.auth0_domain = None

        validator = Auth0TokenValidator()
        assert validator.enabled is False
        assert validator.jwks_client is None

    @patch("app.core.auth0.settings")
    def test_validator_enabled(self, mock_settings):
        """Test validator when Auth0 is enabled"""
        mock_settings.auth0_enabled = True
        mock_settings.auth0_domain = "test.auth0.com"
        mock_settings.auth0_audience = "https://api.example.com"

        with patch("app.core.auth0.PyJWKClient"):
            validator = Auth0TokenValidator()
            assert validator.enabled is True
            assert validator.domain == "test.auth0.com"
            assert validator.audience == "https://api.example.com"

    @patch("app.core.auth0.settings")
    def test_verify_token_disabled(self, mock_settings):
        """Test verify_token raises error when Auth0 is disabled"""
        mock_settings.auth0_enabled = False
        mock_settings.auth0_domain = None

        validator = Auth0TokenValidator()

        with pytest.raises(HTTPException) as exc_info:
            validator.verify_token("fake_token")

        assert exc_info.value.status_code == 501
        assert "not enabled" in exc_info.value.detail

    @patch("app.core.auth0.settings")
    @patch("app.core.auth0.jwt.decode")
    def test_verify_token_expired(self, mock_decode, mock_settings):
        """Test verify_token with expired token"""
        import jwt

        mock_settings.auth0_enabled = True
        mock_settings.auth0_domain = "test.auth0.com"
        mock_settings.auth0_audience = "https://api.example.com"

        mock_decode.side_effect = jwt.ExpiredSignatureError()

        with patch("app.core.auth0.PyJWKClient"):
            validator = Auth0TokenValidator()

            with pytest.raises(HTTPException) as exc_info:
                validator.verify_token("expired_token")

            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    @patch("app.core.auth0.settings")
    @patch("app.core.auth0.jwt.decode")
    def test_verify_token_invalid(self, mock_decode, mock_settings):
        """Test verify_token with invalid token"""
        import jwt

        mock_settings.auth0_enabled = True
        mock_settings.auth0_domain = "test.auth0.com"
        mock_settings.auth0_audience = "https://api.example.com"

        mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

        with patch("app.core.auth0.PyJWKClient"):
            validator = Auth0TokenValidator()

            with pytest.raises(HTTPException) as exc_info:
                validator.verify_token("invalid_token")

            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @patch("app.core.auth0.token_validator")
    async def test_get_current_user_missing_credentials(self, mock_validator):
        """Test get_current_user with missing credentials"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None)

        assert exc_info.value.status_code == 401
        assert "Missing authentication token" in exc_info.value.detail

    @patch("app.core.auth0.token_validator")
    async def test_get_current_user_success(self, mock_validator):
        """Test get_current_user with valid token"""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        # Mock token payload
        mock_payload = {
            "sub": "auth0|123456",
            "email": "test@example.com",
            "name": "Test User",
            "https://staffingagent.com/roles": ["superuser"],
        }
        mock_validator.verify_token.return_value = mock_payload

        user = await get_current_user(credentials=mock_credentials)

        assert user.sub == "auth0|123456"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.roles == ["superuser"]
        assert user.is_superuser is True

    @patch("app.core.auth0.token_validator")
    async def test_get_current_user_roles_as_string(self, mock_validator):
        """Test get_current_user when roles is a string instead of list"""
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        # Roles as string (should be converted to list)
        mock_payload = {
            "sub": "auth0|123",
            "email": "staff@example.com",
            "name": "Staff User",
            "https://staffingagent.com/roles": "staff",
        }
        mock_validator.verify_token.return_value = mock_payload

        user = await get_current_user(credentials=mock_credentials)

        assert user.roles == ["staff"]
        assert user.is_staff is True

    @patch("app.core.auth0.token_validator")
    async def test_get_current_user_no_roles(self, mock_validator):
        """Test get_current_user with no roles in token"""
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        # No roles claim
        mock_payload = {
            "sub": "auth0|123",
            "email": "noroles@example.com",
            "name": "No Roles User",
        }
        mock_validator.verify_token.return_value = mock_payload

        user = await get_current_user(credentials=mock_credentials)

        assert user.roles == []
        assert user.is_superuser is False
        assert user.is_project_manager is False
        assert user.is_staff is False

    @patch("app.core.auth0.token_validator")
    async def test_get_current_user_missing_email(self, mock_validator):
        """Test get_current_user with missing email"""
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        # Missing email
        mock_payload = {
            "sub": "auth0|123",
            "https://staffingagent.com/roles": ["staff"],
        }
        mock_validator.verify_token.return_value = mock_payload

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail


# ============================================================================
# Integration tests (require Auth0 to be configured)
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    "not config.getoption('--run-integration')",
    reason="Integration tests require --run-integration flag",
)
class TestAuth0Integration:
    """
    Integration tests for Auth0.

    These tests require Auth0 to be configured and enabled.
    Run with: pytest --run-integration
    """

    def test_real_auth0_flow(self):
        """
        Test real Auth0 authentication flow.

        This would test the actual Auth0 integration:
        1. Get login URL
        2. Perform OAuth flow
        3. Exchange code for token
        4. Verify token
        5. Extract user info

        NOTE: This requires Auth0 to be set up and configured.
        """
        # This is a placeholder for real integration tests
        # In a real scenario, you would:
        # - Use Selenium/Playwright to automate browser login
        # - Or use Auth0's M2M (machine-to-machine) flow for testing
        pass


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require Auth0",
    )
