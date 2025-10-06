#!/usr/bin/env python3
"""
JWT Authentication Demo
Demonstrates login, token usage, and API access with the new JWT system
"""

import json
import time
from datetime import datetime

import requests


class JWTAuthDemo:
    """Demonstration of JWT authentication features"""

    def __init__(self, base_url: str = "http://localhost:8011"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None

    def print_response(self, response, title="Response"):
        """Pretty print response"""
        print(f"\n📋 {title}")
        print(f"Status: {response.status_code}")
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                data = response.json()
                print(f"Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Text: {response.text}")
        else:
            print(f"Text: {response.text}")

    def demo_health_check(self):
        """Demo: Check API health"""
        print("\n🏥 DEMO: Health Check")
        print("-" * 40)

        response = self.session.get(f"{self.base_url}/health")
        self.print_response(response, "Health Check")

    def demo_registration(self):
        """Demo: User registration"""
        print("\n📝 DEMO: User Registration")
        print("-" * 40)

        user_data = {
            "username": "demouser",
            "email": "demo@example.com",
            "password": "DemoPass123!",
            "full_name": "Demo User",
        }

        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=user_data)
        self.print_response(response, "Registration")

    def demo_login(self):
        """Demo: User login and token acquisition"""
        print("\n🔑 DEMO: User Login")
        print("-" * 40)

        # Try with demo user first, fallback to admin
        login_data = {"username": "demouser", "password": "DemoPass123!", "remember_me": True}

        response = self.session.post(f"{self.base_url}/api/v1/auth/login", json=login_data)

        if response.status_code != 200:
            print("Demo user login failed, trying admin...")
            login_data = {"username": "admin", "password": "admin123", "remember_me": True}
            response = self.session.post(f"{self.base_url}/api/v1/auth/login", json=login_data)

        self.print_response(response, "Login")

        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            print("\n✅ Login successful! Token acquired.")
            print(f"Token expires in: {data['expires_in']} seconds")

            # Store token for future requests
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        else:
            print("❌ Login failed!")

    def demo_profile_access(self):
        """Demo: Access user profile with JWT token"""
        print("\n👤 DEMO: Profile Access")
        print("-" * 40)

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return

        response = self.session.get(f"{self.base_url}/api/v1/auth/profile")
        self.print_response(response, "Profile")

    def demo_protected_endpoints(self):
        """Demo: Access protected endpoints"""
        print("\n🛡️ DEMO: Protected Endpoints")
        print("-" * 40)

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return

        # Test agents endpoint
        print("Testing agents endpoint...")
        response = self.session.get(f"{self.base_url}/api/v1/agents")
        self.print_response(response, "Agents List")

        # Test conversations endpoint
        print("\nTesting conversation creation...")
        conv_data = {
            "agent_id": "code_architect",
            "user_message": "Hello, I need help with system architecture.",
            "context": {"demo": True},
        }
        response = self.session.post(f"{self.base_url}/api/v1/conversations", json=conv_data)
        self.print_response(response, "Create Conversation")

    def demo_admin_endpoints(self):
        """Demo: Access admin-only endpoints"""
        print("\n👑 DEMO: Admin Endpoints")
        print("-" * 40)

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return

        # Test admin stats
        response = self.session.get(f"{self.base_url}/api/v1/admin/stats")
        self.print_response(response, "Admin Stats")

        # Test system status
        response = self.session.get(f"{self.base_url}/api/v1/system/status")
        self.print_response(response, "System Status")

    def demo_api_key_management(self):
        """Demo: API key creation and management"""
        print("\n🗝️ DEMO: API Key Management")
        print("-" * 40)

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return

        # Create API key
        api_key_data = {
            "name": "Demo API Key",
            "permissions": ["agent:view", "chat:create"],
            "expires_in_days": 30,
            "rate_limit": 100,
        }

        response = self.session.post(f"{self.base_url}/api/v1/auth/api-keys", json=api_key_data)
        self.print_response(response, "Create API Key")

        # List API keys
        response = self.session.get(f"{self.base_url}/api/v1/auth/api-keys")
        self.print_response(response, "List API Keys")

    def demo_unauthorized_access(self):
        """Demo: Show what happens without authentication"""
        print("\n🚫 DEMO: Unauthorized Access")
        print("-" * 40)

        # Temporarily remove auth header
        auth_header = self.session.headers.pop("Authorization", None)

        # Try to access protected endpoint
        response = self.session.get(f"{self.base_url}/api/v1/auth/profile")
        self.print_response(response, "Profile (No Auth)")

        # Try to create conversation
        conv_data = {"agent_id": "test", "user_message": "This should fail", "context": {}}
        response = self.session.post(f"{self.base_url}/api/v1/conversations", json=conv_data)
        self.print_response(response, "Create Conversation (No Auth)")

        # Restore auth header
        if auth_header:
            self.session.headers["Authorization"] = auth_header

    def demo_token_expiry_simulation(self):
        """Demo: Simulate token expiry handling"""
        print("\n⏰ DEMO: Token Expiry Simulation")
        print("-" * 40)

        print("In a real scenario, tokens expire after the configured time.")
        print("When a token expires, the API returns 401 Unauthorized.")
        print("The client should then:")
        print("1. Use refresh token to get a new access token, OR")
        print("2. Redirect user to login again")
        print("\nFor this demo, we'll show how to handle expired tokens...")

        # Simulate expired token by using invalid token
        original_token = self.session.headers.get("Authorization")
        self.session.headers["Authorization"] = "Bearer expired_or_invalid_token"

        response = self.session.get(f"{self.base_url}/api/v1/auth/profile")
        self.print_response(response, "Profile (Expired Token)")

        # Restore original token
        if original_token:
            self.session.headers["Authorization"] = original_token

    def demo_logout(self):
        """Demo: User logout"""
        print("\n👋 DEMO: User Logout")
        print("-" * 40)

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return

        response = self.session.post(f"{self.base_url}/api/v1/auth/logout")
        self.print_response(response, "Logout")

        # Clear token
        self.access_token = None
        self.session.headers.pop("Authorization", None)

        # Verify token is invalidated
        print("\nVerifying token invalidation...")
        response = self.session.get(f"{self.base_url}/api/v1/auth/profile")
        self.print_response(response, "Profile After Logout")

    def run_full_demo(self):
        """Run complete JWT authentication demonstration"""
        print("🚀 JWT Authentication System Demo")
        print("=" * 50)
        print(f"Backend URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        demos = [
            ("Health Check", self.demo_health_check),
            ("User Registration", self.demo_registration),
            ("User Login", self.demo_login),
            ("Profile Access", self.demo_profile_access),
            ("Protected Endpoints", self.demo_protected_endpoints),
            ("Admin Endpoints", self.demo_admin_endpoints),
            ("API Key Management", self.demo_api_key_management),
            ("Unauthorized Access", self.demo_unauthorized_access),
            ("Token Expiry Simulation", self.demo_token_expiry_simulation),
            ("User Logout", self.demo_logout),
        ]

        for title, demo_func in demos:
            try:
                demo_func()
                time.sleep(1)  # Brief pause between demos
            except Exception as e:
                print(f"\n❌ Demo '{title}' failed: {e}")

        print("\n" + "=" * 50)
        print("🎉 JWT Authentication Demo Complete!")
        print("\nKey Features Demonstrated:")
        print("✅ User registration and login")
        print("✅ JWT token issuance and validation")
        print("✅ Protected endpoint access")
        print("✅ Role-based access control (admin endpoints)")
        print("✅ API key management")
        print("✅ Token expiry handling")
        print("✅ User logout and session invalidation")


def main():
    """Main demo function"""
    print("JWT Authentication Demo")
    print("Make sure the backend server is running on http://localhost:8011")
    print("Press Ctrl+C to exit at any time")
    print()

    try:
        demo = JWTAuthDemo()
        demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except requests.exceptions.ConnectionError:
        print(
            "\n❌ Cannot connect to backend server. Make sure it's running on http://localhost:8011"
        )
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")


if __name__ == "__main__":
    main()
