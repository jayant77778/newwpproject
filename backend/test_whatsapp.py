import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.whatsapp.bot import WhatsAppBot
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_whatsapp_integration():
    """
    Test WhatsApp integration step by step
    """
    print("🚀 Starting WhatsApp Order Automation Test")
    print("=" * 50)
    
    bot = WhatsAppBot()
    
    try:
        # Step 1: Connect to WhatsApp
        print("\n📱 Step 1: Connecting to WhatsApp Web...")
        success = await bot.connect()
        
        if not success:
            print("❌ Failed to connect to WhatsApp Web")
            print("Please make sure:")
            print("1. Chrome browser is installed")
            print("2. WhatsApp Web is accessible")
            print("3. You can scan the QR code")
            return
        
        print("✅ Connected to WhatsApp Web successfully!")
        
        # Step 2: Get available groups
        print("\n📋 Step 2: Getting available WhatsApp groups...")
        groups = await bot.get_groups()
        
        if not groups:
            print("❌ No WhatsApp groups found")
            print("Please:")
            print("1. Create a test WhatsApp group")
            print("2. Add some contacts to the group")
            print("3. Try again")
            return
        
        print(f"✅ Found {len(groups)} WhatsApp groups:")
        for i, group in enumerate(groups):
            print(f"  {i+1}. {group['name']}")
        
        # Step 3: Select first group for testing
        if groups:
            test_group = groups[0]
            print(f"\n🎯 Step 3: Selecting group '{test_group['name']}' for testing...")
            
            success = await bot.select_group(test_group['name'])
            if success:
                print(f"✅ Successfully selected group: {test_group['name']}")
            else:
                print(f"❌ Failed to select group: {test_group['name']}")
                return
        
        # Step 4: Get recent messages
        print("\n📨 Step 4: Getting recent messages...")
        messages = await bot.get_messages(limit=20)
        
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Step 5: Analyze messages for orders
        print("\n🔍 Step 5: Analyzing messages for orders...")
        order_messages = [msg for msg in messages if msg.get("is_order", False)]
        
        print(f"✅ Found {len(order_messages)} potential order messages:")
        
        for i, order_msg in enumerate(order_messages[:5]):  # Show first 5
            print(f"\n  Order {i+1}:")
            print(f"    From: {order_msg['sender']}")
            print(f"    Time: {order_msg['timestamp']}")
            print(f"    Content: {order_msg['content'][:100]}...")
            
            if order_msg.get('order_data'):
                items = order_msg['order_data'].get('items', [])
                print(f"    Extracted Items: {len(items)}")
                for item in items:
                    print(f"      - {item['item']}: {item['quantity']}")
        
        # Step 6: Test export functionality
        print(f"\n📤 Step 6: Testing chat export...")
        export_path = await bot.export_chat(test_group['name'], days=1)
        
        if export_path:
            print(f"✅ Chat exported successfully to: {export_path}")
        else:
            print("❌ Failed to export chat")
        
        # Step 7: Instructions for testing
        print("\n🧪 Step 7: Testing Instructions")
        print("=" * 30)
        print(f"Now you can test by sending order messages to '{test_group['name']}' group:")
        print("\nExample messages to send:")
        print("1. 'Hi, I want cotton shirt 3 pieces'")
        print("2. 'Please book for me: formal shirt 2, jeans 1 piece'")
        print("3. 'मुझे चाहिए कॉटन शर्ट 5 पीस'")
        print("\nThe system will automatically:")
        print("- Detect these as order messages")
        print("- Extract customer and item information")
        print("- Process them in the backend API")
        
        # Keep monitoring for a short time
        print(f"\n🔄 Monitoring '{test_group['name']}' for 30 seconds...")
        print("Send some test order messages now!")
        
        # Simple monitoring loop
        start_time = asyncio.get_event_loop().time()
        last_message_count = len(messages)
        
        while (asyncio.get_event_loop().time() - start_time) < 30:
            await asyncio.sleep(2)
            current_messages = await bot.get_messages(limit=10)
            
            if len(current_messages) > last_message_count:
                new_messages = current_messages[last_message_count:]
                for msg in new_messages:
                    if msg.get("is_order"):
                        print(f"\n🆕 New order detected!")
                        print(f"   From: {msg['sender']}")
                        print(f"   Content: {msg['content']}")
                        if msg.get('order_data'):
                            items = msg['order_data'].get('items', [])
                            print(f"   Items: {items}")
                
                last_message_count = len(current_messages)
        
        print("\n✅ WhatsApp integration test completed successfully!")
        print("\nNext steps:")
        print("1. Start the FastAPI backend: python main.py")
        print("2. Use the frontend to connect and manage orders")
        print("3. The system is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome browser is installed")
        print("2. Check internet connection")
        print("3. Ensure WhatsApp Web is working in browser")
        print("4. Try running the test again")
        
    finally:
        print("\n🛑 Closing WhatsApp bot...")
        await bot.close()
        print("✅ Test completed")

if __name__ == "__main__":
    try:
        asyncio.run(test_whatsapp_integration())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
