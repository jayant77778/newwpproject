import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class WhatsAppBot:
    def __init__(self):
        self.driver = None
        self.session_path = os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_sessions")
        self.headless = os.getenv("WHATSAPP_HEADLESS", "true").lower() == "true"
        self.is_connected = False
        self.current_group = None
        self.message_handlers = []
        
        # Create session directory
        os.makedirs(self.session_path, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Setup Chrome WebDriver with WhatsApp Web options"""
        chrome_options = Options()
        
        # Add user data directory for session persistence
        chrome_options.add_argument(f"--user-data-dir={self.session_path}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # User agent
        user_agent = os.getenv("WHATSAPP_USER_AGENT", 
                              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        self.logger.info("Chrome WebDriver initialized")

    async def connect(self):
        """Connect to WhatsApp Web"""
        try:
            if not self.driver:
                self.setup_driver()
            
            self.logger.info("Connecting to WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for QR code or main interface
            try:
                # Check if already logged in
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='chat-list']"))
                )
                self.is_connected = True
                self.logger.info("✅ Already logged in to WhatsApp Web")
                return True
                
            except TimeoutException:
                # Need to scan QR code
                self.logger.info("🔄 Please scan the QR code in your browser")
                
                # Wait for successful login (up to 60 seconds)
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='chat-list']"))
                )
                
                self.is_connected = True
                self.logger.info("✅ Successfully connected to WhatsApp Web")
                return True
                
        except TimeoutException:
            self.logger.error("❌ Failed to connect: QR code not scanned in time")
            return False
        except Exception as e:
            self.logger.error(f"❌ Connection error: {e}")
            return False

    async def get_groups(self) -> List[Dict]:
        """Get list of available WhatsApp groups"""
        if not self.is_connected:
            await self.connect()
        
        try:
            groups = []
            
            # Find all chat elements
            chat_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "div[data-testid='chat-list'] > div"
            )
            
            for chat in chat_elements:
                try:
                    # Get chat name
                    name_element = chat.find_element(By.CSS_SELECTOR, "span[title]")
                    group_name = name_element.get_attribute("title")
                    
                    # Check if it's a group (has group icon)
                    try:
                        chat.find_element(By.CSS_SELECTOR, "span[data-testid='default-group']")
                        is_group = True
                    except NoSuchElementException:
                        is_group = False
                    
                    if is_group:
                        groups.append({
                            "name": group_name,
                            "element": chat,
                            "id": f"group_{len(groups)}"
                        })
                        
                except Exception as e:
                    continue
            
            self.logger.info(f"Found {len(groups)} groups")
            return groups
            
        except Exception as e:
            self.logger.error(f"Error getting groups: {e}")
            return []

    async def select_group(self, group_name: str) -> bool:
        """Select a specific WhatsApp group"""
        try:
            # Find and click the group
            group_element = self.driver.find_element(
                By.XPATH, 
                f"//span[@title='{group_name}']"
            )
            group_element.click()
            
            # Wait for chat to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='conversation-panel-messages']"))
            )
            
            self.current_group = group_name
            self.logger.info(f"✅ Selected group: {group_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error selecting group {group_name}: {e}")
            return False

    async def get_messages(self, limit: int = 50) -> List[Dict]:
        """Get recent messages from current group"""
        if not self.current_group:
            self.logger.error("No group selected")
            return []
        
        try:
            messages = []
            
            # Scroll to load more messages
            message_container = self.driver.find_element(
                By.CSS_SELECTOR, 
                "div[data-testid='conversation-panel-messages']"
            )
            
            # Get message elements
            message_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "div[data-testid='msg-container']"
            )
            
            for msg_element in message_elements[-limit:]:
                try:
                    message_data = await self._parse_message(msg_element)
                    if message_data:
                        messages.append(message_data)
                except Exception as e:
                    continue
            
            self.logger.info(f"Retrieved {len(messages)} messages")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error getting messages: {e}")
            return []

    async def _parse_message(self, message_element) -> Optional[Dict]:
        """Parse individual message element"""
        try:
            # Get sender name
            try:
                sender_element = message_element.find_element(
                    By.CSS_SELECTOR, 
                    "span[data-testid='author']"
                )
                sender = sender_element.text
            except NoSuchElementException:
                sender = "Unknown"
            
            # Get message content
            try:
                content_element = message_element.find_element(
                    By.CSS_SELECTOR, 
                    "span.selectable-text"
                )
                content = content_element.text
            except NoSuchElementException:
                return None
            
            # Get timestamp
            try:
                time_element = message_element.find_element(
                    By.CSS_SELECTOR, 
                    "span[data-testid='msg-meta'] span"
                )
                timestamp = time_element.text
            except NoSuchElementException:
                timestamp = datetime.now().strftime("%H:%M")
            
            # Check if message looks like an order
            is_order = self._is_order_message(content)
            
            message_data = {
                "id": f"msg_{datetime.now().timestamp()}",
                "sender": sender,
                "content": content,
                "timestamp": timestamp,
                "datetime": datetime.now(),
                "is_order": is_order,
                "group": self.current_group
            }
            
            # Extract order data if it's an order
            if is_order:
                message_data["order_data"] = self._extract_order_data(content, sender)
            
            return message_data
            
        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None

    def _is_order_message(self, content: str) -> bool:
        """Determine if message contains an order"""
        # Order indicators
        order_keywords = [
            "order", "मंगवाना", "चाहिए", "want", "need", "book", 
            "shirt", "jeans", "saree", "kurti", "dress", "पैंट", "शर्ट"
        ]
        
        # Quantity indicators
        quantity_pattern = r'\b\d+\s*(piece|pc|pcs|पीस|pieces?)\b'
        
        content_lower = content.lower()
        
        # Check for order keywords
        has_order_keyword = any(keyword in content_lower for keyword in order_keywords)
        
        # Check for quantity patterns
        has_quantity = bool(re.search(quantity_pattern, content_lower))
        
        # Check for product + quantity pattern
        product_quantity_pattern = r'\b\w+\s+\d+\b'
        has_product_quantity = bool(re.search(product_quantity_pattern, content))
        
        return has_order_keyword or has_quantity or has_product_quantity

    def _extract_order_data(self, content: str, sender: str) -> Dict:
        """Extract structured order data from message"""
        order_data = {
            "customer_name": sender,
            "items": [],
            "raw_message": content
        }
        
        # Common product patterns
        product_patterns = [
            # Pattern: "cotton shirt 5 pieces"
            r'(\w+\s+\w+)\s+(\d+)\s*(?:piece|pc|pcs|पीस|pieces?)',
            # Pattern: "5 cotton shirts"
            r'(\d+)\s+(\w+\s+\w+)',
            # Pattern: "shirt - 5"
            r'(\w+)\s*[-:]\s*(\d+)',
            # Pattern: "5x shirts"
            r'(\d+)x?\s*(\w+)',
        ]
        
        items_found = []
        
        for pattern in product_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    if match.group(1).isdigit():
                        quantity = int(match.group(1))
                        item = match.group(2).strip()
                    else:
                        item = match.group(1).strip()
                        quantity = int(match.group(2))
                    
                    items_found.append({
                        "item": item.title(),
                        "quantity": quantity
                    })
        
        # If no structured pattern found, try to extract manually
        if not items_found:
            # Look for any numbers and nearby words
            words = content.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    qty = int(word)
                    # Look for item names around the quantity
                    item_words = []
                    if i > 0:
                        item_words.append(words[i-1])
                    if i < len(words) - 1:
                        item_words.append(words[i+1])
                    
                    if item_words:
                        item = " ".join(item_words).strip(".,!?")
                        items_found.append({
                            "item": item.title(),
                            "quantity": qty
                        })
                        break
        
        order_data["items"] = items_found
        return order_data

    async def export_chat(self, group_name: str, days: int = 7) -> Optional[str]:
        """Export chat data for a group"""
        try:
            if not await self.select_group(group_name):
                return None
            
            # Get messages
            messages = await self.get_messages(limit=1000)
            
            # Filter messages by date if needed
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            recent_messages = [
                msg for msg in messages 
                if msg["datetime"].timestamp() > cutoff_date
            ]
            
            # Create export data
            export_data = {
                "group_name": group_name,
                "export_date": datetime.now().isoformat(),
                "message_count": len(recent_messages),
                "order_count": len([msg for msg in recent_messages if msg["is_order"]]),
                "messages": recent_messages
            }
            
            # Save to file
            export_filename = f"whatsapp_export_{group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_path = os.path.join("./exports", export_filename)
            
            os.makedirs("./exports", exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
            
            self.logger.info(f"✅ Chat exported to: {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"Error exporting chat: {e}")
            return None

    async def start_monitoring(self, group_name: str, callback=None):
        """Start monitoring a group for new messages"""
        if not await self.select_group(group_name):
            return False
        
        self.logger.info(f"🔄 Started monitoring group: {group_name}")
        
        last_message_count = 0
        
        while self.is_connected:
            try:
                # Get current messages
                messages = await self.get_messages(limit=10)
                current_count = len(messages)
                
                # Check for new messages
                if current_count > last_message_count:
                    new_messages = messages[last_message_count:]
                    
                    for message in new_messages:
                        if message["is_order"] and callback:
                            await callback(message)
                    
                    last_message_count = current_count
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring: {e}")
                await asyncio.sleep(10)
        
        return True

    async def close(self):
        """Close the WhatsApp bot"""
        if self.driver:
            self.driver.quit()
            self.is_connected = False
            self.logger.info("✅ WhatsApp bot closed")

# Example usage and testing
async def test_whatsapp_bot():
    """Test function for WhatsApp bot"""
    bot = WhatsAppBot()
    
    try:
        # Connect to WhatsApp
        if await bot.connect():
            print("✅ Connected to WhatsApp")
            
            # Get available groups
            groups = await bot.get_groups()
            print(f"📱 Found {len(groups)} groups:")
            for group in groups:
                print(f"  - {group['name']}")
            
            # Select first group if available
            if groups:
                group_name = groups[0]["name"]
                if await bot.select_group(group_name):
                    print(f"✅ Selected group: {group_name}")
                    
                    # Get recent messages
                    messages = await bot.get_messages(limit=20)
                    print(f"📨 Retrieved {len(messages)} messages")
                    
                    # Show order messages
                    order_messages = [msg for msg in messages if msg["is_order"]]
                    print(f"🛒 Found {len(order_messages)} order messages:")
                    
                    for order_msg in order_messages:
                        print(f"  From: {order_msg['sender']}")
                        print(f"  Content: {order_msg['content'][:50]}...")
                        print(f"  Items: {order_msg.get('order_data', {}).get('items', [])}")
                        print("  ---")
                    
                    # Export chat
                    export_path = await bot.export_chat(group_name, days=1)
                    if export_path:
                        print(f"✅ Chat exported to: {export_path}")
            
        else:
            print("❌ Failed to connect to WhatsApp")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_whatsapp_bot())
