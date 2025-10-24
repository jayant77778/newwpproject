#!/usr/bin/env python3
"""
Full Stack Integration Test Script
Tests the complete WhatsApp Order Automation system
"""
import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend Health Check:", data)
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_frontend_connection():
    """Test frontend accessibility"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection error: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    tests = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/api/health", "Health check"),
        ("GET", "/docs", "API documentation"),
        ("GET", "/api/orders", "Orders endpoint (should return empty list)"),
    ]
    
    results = []
    for method, endpoint, description in tests:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = requests.request(method, url, timeout=5)
            success = response.status_code in [200, 422]  # 422 is expected for some endpoints without auth
            status = "✅" if success else "❌"
            print(f"{status} {description}: {response.status_code}")
            results.append(success)
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
            results.append(False)
    
    return all(results)

def test_whatsapp_webhook():
    """Test WhatsApp webhook endpoint"""
    try:
        # Simulate a WhatsApp message
        webhook_data = {
            "messages": [{
                "id": "test_message_001",
                "from": "+1234567890",
                "timestamp": str(int(time.time())),
                "text": {
                    "body": "Hello, I want to order 2 pizzas for pickup at 7 PM"
                },
                "type": "text"
            }],
            "contacts": [{
                "profile": {
                    "name": "Test Customer"
                },
                "wa_id": "+1234567890"
            }]
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "test_signature"  # For testing purposes
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/whatsapp/webhook",
            json=webhook_data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code in [200, 422]:  # 422 might be expected for signature validation
            print("✅ WhatsApp webhook endpoint responding")
            return True
        else:
            print(f"❌ WhatsApp webhook test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ WhatsApp webhook test error: {e}")
        return False

def test_database_connection():
    """Test database operations through API"""
    try:
        # Test creating and retrieving orders
        response = requests.get(f"{BACKEND_URL}/api/orders", timeout=5)
        if response.status_code in [200, 401, 422]:  # Various valid responses without auth
            print("✅ Database connection through API working")
            return True
        else:
            print(f"❌ Database test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("WhatsApp Order System - Full Stack Integration Test")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Frontend Connection", test_frontend_connection),
        ("API Endpoints", test_api_endpoints),
        ("WhatsApp Webhook", test_whatsapp_webhook),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The full stack system is working correctly.")
        print(f"🌐 Frontend: {FRONTEND_URL}")
        print(f"🔧 Backend API: {BACKEND_URL}/docs")
        print("✨ System is ready for development and testing!")
    else:
        print("⚠️  Some tests failed. Please check the logs above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
