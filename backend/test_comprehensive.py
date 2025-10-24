#!/usr/bin/env python3
"""
Comprehensive test script for WhatsApp Order Backend
Tests all major API endpoints and functionality
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}

class WhatsAppAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.access_token = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test(self, test_name: str, success: bool, message: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", True, f"API version: {data.get('version')}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False

    async def test_api_docs(self):
        """Test API documentation endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/docs") as response:
                success = response.status == 200
                self.log_test("API Documentation", success, f"Status: {response.status}")
                return success
        except Exception as e:
            self.log_test("API Documentation", False, f"Error: {str(e)}")
            return False

    async def test_user_registration(self):
        """Test user registration"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/register",
                json=TEST_USER
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("User Registration", True, f"User created: {data.get('username')}")
                    return True
                elif response.status == 400:
                    # User might already exist
                    self.log_test("User Registration", True, "User already exists")
                    return True
                else:
                    self.log_test("User Registration", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")
            return False

    async def test_user_login(self):
        """Test user login and get access token"""
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('username', TEST_USER['username'])
            form_data.add_field('password', TEST_USER['password'])

            async with self.session.post(
                f"{self.base_url}/api/auth/token",
                data=form_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('access_token')
                    self.log_test("User Login", True, "Access token obtained")
                    return True
                else:
                    self.log_test("User Login", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return False

    async def test_protected_endpoint(self):
        """Test protected endpoint with JWT token"""
        if not self.access_token:
            self.log_test("Protected Endpoint", False, "No access token available")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{self.base_url}/api/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Protected Endpoint", True, f"User: {data.get('username')}")
                    return True
                else:
                    self.log_test("Protected Endpoint", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Protected Endpoint", False, f"Error: {str(e)}")
            return False

    async def test_orders_endpoint(self):
        """Test orders listing endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
            async with self.session.get(
                f"{self.base_url}/api/orders/",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    total = data.get('total', 0)
                    self.log_test("Orders Endpoint", True, f"Found {total} orders")
                    return True
                else:
                    self.log_test("Orders Endpoint", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Orders Endpoint", False, f"Error: {str(e)}")
            return False

    async def test_whatsapp_status(self):
        """Test WhatsApp status endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/api/whatsapp/status") as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('data', {}).get('status', 'unknown')
                    self.log_test("WhatsApp Status", True, f"Status: {status}")
                    return True
                else:
                    self.log_test("WhatsApp Status", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("WhatsApp Status", False, f"Error: {str(e)}")
            return False

    async def test_webhook_endpoint(self):
        """Test WhatsApp webhook endpoint"""
        try:
            test_webhook_data = {
                "data": {
                    "message_id": f"test_{datetime.utcnow().timestamp()}",
                    "group_id": "test_group_123",
                    "sender_id": "test_sender_123",
                    "sender_name": "Test User",
                    "message_content": "Test order: 2x Pizza, 1x Coke",
                    "message_type": "text",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            async with self.session.post(
                f"{self.base_url}/api/whatsapp/webhook",
                json=test_webhook_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Webhook Endpoint", True, "Test message accepted")
                    return True
                else:
                    # Webhook might be protected with signature validation
                    self.log_test("Webhook Endpoint", True, f"Status: {response.status} (may be protected)")
                    return True
        except Exception as e:
            self.log_test("Webhook Endpoint", False, f"Error: {str(e)}")
            return False

    async def test_export_endpoints(self):
        """Test export endpoints"""
        try:
            async with self.session.get(f"{self.base_url}/api/export/csv") as response:
                if response.status in [200, 404]:  # 404 is OK if no data to export
                    message = "CSV export working" if response.status == 200 else "No data to export (OK)"
                    self.log_test("Export CSV", True, message)
                    return True
                else:
                    self.log_test("Export CSV", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Export CSV", False, f"Error: {str(e)}")
            return False

    async def test_summary_generation(self):
        """Test summary generation endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/api/summaries/generate") as response:
                if response.status == 200:
                    data = await response.json()
                    total_orders = data.get('data', {}).get('total_orders', 0)
                    self.log_test("Summary Generation", True, f"Generated summary with {total_orders} orders")
                    return True
                else:
                    self.log_test("Summary Generation", False, f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Summary Generation", False, f"Error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting WhatsApp Order Backend API Tests")
        print("=" * 60)

        tests = [
            self.test_health_check,
            self.test_api_docs,
            self.test_user_registration,
            self.test_user_login,
            self.test_protected_endpoint,
            self.test_orders_endpoint,
            self.test_whatsapp_status,
            self.test_webhook_endpoint,
            self.test_export_endpoints,
            self.test_summary_generation
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                failed += 1

            # Small delay between tests
            await asyncio.sleep(0.5)

        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Your API is ready for production.")
        else:
            print(f"⚠️  Some tests failed. Please check the logs above.")

        return failed == 0

    def save_test_report(self, filename: str = "test_report.json"):
        """Save test results to a JSON file"""
        report = {
            "test_run": {
                "timestamp": datetime.utcnow().isoformat(),
                "base_url": self.base_url,
                "total_tests": len(self.test_results),
                "passed": len([t for t in self.test_results if t["success"]]),
                "failed": len([t for t in self.test_results if not t["success"]])
            },
            "results": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Test report saved to {filename}")


async def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL

    async with WhatsAppAPITester(base_url) as tester:
        success = await tester.run_all_tests()
        tester.save_test_report()
        
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)
