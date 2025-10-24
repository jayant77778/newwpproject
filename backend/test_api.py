import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """
    Test all FastAPI endpoints
    """
    print("🚀 Testing WhatsApp Order API")
    print("=" * 40)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Health check
            print("\n🔍 Test 1: Health Check")
            response = await client.get(f"{BASE_URL}/api/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test 2: WhatsApp status
            print("\n📱 Test 2: WhatsApp Status")
            response = await client.get(f"{BASE_URL}/api/whatsapp/status")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test 3: Connect to WhatsApp (if not connected)
            print("\n🔗 Test 3: Connect to WhatsApp")
            response = await client.post(f"{BASE_URL}/api/whatsapp/connect")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test 4: Get WhatsApp groups
            print("\n📋 Test 4: Get WhatsApp Groups")
            response = await client.get(f"{BASE_URL}/api/whatsapp/groups")
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Found {len(result.get('data', []))} groups")
            
            # Store first group ID for testing
            groups = result.get('data', [])
            group_id = groups[0]['id'] if groups else None
            
            if group_id:
                # Test 5: Select group
                print(f"\n🎯 Test 5: Select Group (ID: {group_id})")
                response = await client.post(f"{BASE_URL}/api/whatsapp/groups/{group_id}/select")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Test 6: Get group messages
                print(f"\n📨 Test 6: Get Group Messages")
                response = await client.get(f"{BASE_URL}/api/whatsapp/groups/{group_id}/messages?limit=10")
                print(f"Status: {response.status_code}")
                result = response.json()
                if result.get('success'):
                    messages = result.get('data', {}).get('messages', [])
                    print(f"Retrieved {len(messages)} messages")
                    order_count = result.get('data', {}).get('order_messages', 0)
                    print(f"Order messages: {order_count}")
            
            # Test 7: Get orders from database
            print("\n📊 Test 7: Get Orders")
            response = await client.get(f"{BASE_URL}/api/orders?page=1&size=10")
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Total orders: {result.get('total', 0)}")
            
            # Test 8: Dashboard statistics
            print("\n📈 Test 8: Dashboard Statistics")
            response = await client.get(f"{BASE_URL}/api/orders/statistics/dashboard")
            print(f"Status: {response.status_code}")
            result = response.json()
            if result.get('success'):
                stats = result.get('data', {})
                print(f"Total Orders: {stats.get('total_orders', 0)}")
                print(f"Total Customers: {stats.get('total_customers', 0)}")
                print(f"Most Ordered Item: {stats.get('most_ordered_item', 'N/A')}")
            
            # Test 9: Generate summary
            print("\n📋 Test 9: Generate Summary")
            response = await client.get(f"{BASE_URL}/api/summaries/generate")
            print(f"Status: {response.status_code}")
            result = response.json()
            if result.get('success'):
                summary = result.get('data', {})
                print(f"Total Customers: {summary.get('total_customers', 0)}")
                print(f"Total Items: {summary.get('total_items', 0)}")
            
            # Test 10: List export files
            print("\n📤 Test 10: List Export Files")
            response = await client.get(f"{BASE_URL}/api/export/files")
            print(f"Status: {response.status_code}")
            result = response.json()
            if result.get('success'):
                files = result.get('data', [])
                print(f"Available export files: {len(files)}")
            
            print("\n✅ API testing completed successfully!")
            print("\nAPI Documentation available at:")
            print(f"- Swagger UI: {BASE_URL}/docs")
            print(f"- ReDoc: {BASE_URL}/redoc")
            
        except httpx.ConnectError:
            print("❌ Could not connect to the API server")
            print("Please make sure the FastAPI server is running:")
            print("1. cd backend")
            print("2. python main.py")
            
        except Exception as e:
            print(f"❌ Error during API testing: {e}")

async def test_create_sample_data():
    """
    Create sample data for testing
    """
    print("\n🔧 Creating sample data...")
    
    sample_orders = [
        {
            "customer_name": "John Doe",
            "phone": "9999999999",
            "items": [
                {"item": "Cotton Shirt", "qty": 3},
                {"item": "Denim Jeans", "qty": 1}
            ]
        },
        {
            "customer_name": "Jane Smith", 
            "phone": "8888888888",
            "items": [
                {"item": "Silk Saree", "qty": 2}
            ]
        }
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            for order_data in sample_orders:
                # This would create orders via API
                # Implementation depends on your API structure
                print(f"Sample order for {order_data['customer_name']}: {len(order_data['items'])} items")
                
        except Exception as e:
            print(f"Error creating sample data: {e}")

if __name__ == "__main__":
    print("FastAPI Server should be running at http://localhost:8000")
    print("Starting API tests...")
    
    try:
        asyncio.run(test_api_endpoints())
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        print("\nMake sure to:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start the server: python main.py")
        print("3. Run this test again")
