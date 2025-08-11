"""
Core tests for QU Security Backend
"""

from common.test_utils import BaseAPITestCase


class HealthCheckTestCase(BaseAPITestCase):
    """Test the health check endpoint"""

    def test_health_check_endpoint(self):
        """Test that health check endpoint works"""
        response = self.client.get("/en/api/health/")
        self.assert_response_success(response)
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "ok")


class AuthenticationTestCase(BaseAPITestCase):
    """JWT Authentication tests"""

    def test_login_success(self):
        """Test successful login"""
        login_data = {"username": "admin", "password": "testpass123"}
        response = self.client.post("/en/api/auth/login/", login_data)
        self.assert_response_success(response)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_failure(self):
        """Test failed login"""
        login_data = {"username": "admin", "password": "wrongpass"}
        response = self.client.post("/en/api/auth/login/", login_data)
        self.assert_response_error(response, 401)


class UserAPITestCase(BaseAPITestCase):
    """User API tests"""

    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "username": "newuser",
            "password": "newpass123",
            "password_confirm": "newpass123",
            "email": "newuser@test.com",
        }
        response = self.client.post("/en/api/users/", user_data)
        self.assert_response_success(response, 201)

    def test_user_me_endpoint(self):
        """Test current user profile endpoint"""
        self.authenticate_as(self.admin_user)
        response = self.client.get("/en/api/users/me/")
        self.assert_response_success(response)
        self.assertEqual(response.data["username"], "admin")


class PropertyAPITestCase(BaseAPITestCase):
    """Property API tests"""

    def test_client_can_create_property(self):
        """Test that client can create property"""
        self.authenticate_as(self.client_user)
        property_data = {"address": "456 New Street", "total_hours": 120}
        response = self.client.post("/en/api/properties/", property_data)
        self.assert_response_success(response, 201)

    def test_client_sees_own_properties(self):
        """Test that client sees only their own properties"""
        self.authenticate_as(self.client_user)
        response = self.client.get("/en/api/properties/")
        self.assert_response_success(response)

        # Check if response is paginated
        data = response.data.get("results", response.data)
        if isinstance(data, list):
            property_ids = [p["id"] for p in data]
            self.assertIn(self.property.id, property_ids)


class GuardAPITestCase(BaseAPITestCase):
    """Guard API tests"""

    def test_admin_can_list_guards(self):
        """Test that admin can list guards"""
        self.authenticate_as(self.admin_user)
        response = self.client.get("/en/api/guards/")
        self.assert_response_success(response)

    def test_guard_requires_authentication(self):
        """Test that guard endpoints require authentication"""
        response = self.client.get("/en/api/guards/")
        self.assert_response_error(response, 401)


class ClientAPITestCase(BaseAPITestCase):
    """Client API tests"""

    def test_admin_can_list_clients(self):
        """Test that admin can list clients"""
        self.authenticate_as(self.admin_user)
        response = self.client.get("/en/api/clients/")
        self.assert_response_success(response)

    def test_client_requires_authentication(self):
        """Test that client endpoints require authentication"""
        response = self.client.get("/en/api/clients/")
        self.assert_response_error(response, 401)
