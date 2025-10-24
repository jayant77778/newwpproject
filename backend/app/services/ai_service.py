"""
AI Service for processing WhatsApp messages and extracting order information
"""
import os
import re
import json
# import openai  # Commented out for testing
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIOrderExtractor:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.3"))
        self.ai_enabled = os.getenv("AI_ENABLE", "false").lower() == "true"  # Disabled for testing
        
        if self.ai_enabled and self.openai_api_key:
            # openai.api_key = self.openai_api_key  # Commented for testing
            pass
    
    def extract_order_from_message(self, message: str, sender_name: str = "") -> Dict[str, Any]:
        """
        Extract order information from WhatsApp message using AI and regex patterns
        """
        try:
            # First try pattern-based extraction
            pattern_result = self._extract_with_patterns(message, sender_name)
            
            # If AI is enabled and pattern extraction didn't find complete order, use AI
            if self.ai_enabled and self.openai_api_key and not pattern_result.get("items"):
                ai_result = self._extract_with_ai(message, sender_name)
                if ai_result.get("items"):
                    return ai_result
            
            return pattern_result
            
        except Exception as e:
            logger.error(f"Error extracting order from message: {e}")
            return {"is_order": False, "items": [], "error": str(e)}
    
    def _extract_with_patterns(self, message: str, sender_name: str) -> Dict[str, Any]:
        """
        Extract order using regex patterns
        """
        message_lower = message.lower().strip()
        
        # Common order indicators
        order_indicators = [
            r'\border\b', r'\bbook\b', r'\breserve\b', r'\bwant\b', 
            r'\bneed\b', r'\btake\b', r'\bget\b', r'\bbuy\b',
            r'\bpcs?\b', r'\bpiece\b', r'\bkg\b', r'\bliter\b', r'\bpack\b'
        ]
        
        # Check if message contains order indicators
        has_order_indicator = any(re.search(pattern, message_lower) for pattern in order_indicators)
        
        # Extract items with quantities
        items = self._extract_items_with_quantities(message)
        
        # Extract time if mentioned
        time_match = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', message_lower)
        order_time = None
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            period = time_match.group(3)
            if period:
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            order_time = f"{hour:02d}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"
        
        # Determine if this is likely an order
        is_order = has_order_indicator and len(items) > 0
        
        return {
            "is_order": is_order,
            "customer_name": sender_name,
            "items": items,
            "order_time": order_time,
            "raw_message": message,
            "extraction_method": "pattern"
        }
    
    def _extract_items_with_quantities(self, message: str) -> List[Dict[str, Any]]:
        """
        Extract items with quantities from message
        """
        items = []
        
        # Pattern for quantity + item (e.g., "2 pizza", "1kg rice", "3 pieces chicken")
        patterns = [
            r'(\d+)\s*(kg|kgs|kilogram|kilograms)\s+([a-zA-Z\s]+)',
            r'(\d+)\s*(liter|liters|l|lit)\s+([a-zA-Z\s]+)',
            r'(\d+)\s*(pcs?|pieces?|piece)\s+([a-zA-Z\s]+)',
            r'(\d+)\s*(pack|packs|packet|packets)\s+([a-zA-Z\s]+)',
            r'(\d+)\s*([a-zA-Z\s]{2,})',  # General pattern: number + item name
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:  # Pattern with unit
                    quantity, unit, item_name = match
                    items.append({
                        "name": f"{item_name.strip()}",
                        "quantity": int(quantity),
                        "unit": unit.lower(),
                        "notes": f"{quantity} {unit} {item_name.strip()}"
                    })
                elif len(match) == 2:  # General pattern
                    quantity, item_name = match
                    # Skip if item_name is too short or looks like a time/date
                    if len(item_name.strip()) < 3 or re.match(r'^\d', item_name.strip()):
                        continue
                    items.append({
                        "name": item_name.strip(),
                        "quantity": int(quantity),
                        "unit": "pcs",
                        "notes": f"{quantity} {item_name.strip()}"
                    })
        
        # Also look for items mentioned without explicit quantities
        if not items:
            food_keywords = [
                'pizza', 'burger', 'sandwich', 'rice', 'chicken', 'fish', 'meat',
                'bread', 'cake', 'coffee', 'tea', 'juice', 'water', 'milk',
                'egg', 'flour', 'sugar', 'oil', 'salt', 'vegetable', 'fruit'
            ]
            
            for keyword in food_keywords:
                if keyword in message.lower():
                    items.append({
                        "name": keyword,
                        "quantity": 1,
                        "unit": "pcs",
                        "notes": f"1 {keyword} (inferred)"
                    })
                    break  # Only add one inferred item
        
        return items
    
    def _extract_with_ai(self, message: str, sender_name: str) -> Dict[str, Any]:
        """
        Extract order using OpenAI API
        """
        try:
            prompt = f"""
            Analyze the following WhatsApp message and determine if it contains a food/product order.
            
            Message from {sender_name}: "{message}"
            
            Extract the following information in JSON format:
            {{
                "is_order": boolean (true if this is an order, false otherwise),
                "customer_name": "{sender_name}",
                "items": [
                    {{
                        "name": "item name",
                        "quantity": number,
                        "unit": "pcs/kg/liter/pack/etc",
                        "notes": "any additional notes about the item"
                    }}
                ],
                "order_time": "time if mentioned (HH:MM AM/PM format)" or null,
                "special_instructions": "any special instructions or notes",
                "extraction_method": "ai"
            }}
            
            Rules:
            1. Only mark as order if the message clearly indicates wanting to buy/order something
            2. Extract all items mentioned with their quantities
            3. If no quantity is specified, assume 1
            4. Use appropriate units (pcs for countable items, kg for weight, etc.)
            5. If no time is mentioned, set order_time to null
            """            
            # response = openai.ChatCompletion.create(  # Commented for testing
            #     model=self.model,
            #     messages=[
            #         {"role": "system", "content": "You are an AI assistant that extracts order information from WhatsApp messages. Always respond with valid JSON."},
            #         {"role": "user", "content": prompt}
            #     ],
            #     max_tokens=self.max_tokens,
            #     temperature=self.temperature
            # )
            
            # For testing, return empty result
            return {
                "is_order": False,
                "items": [],
                "order_time": None,
                "notes": "AI service disabled for testing"
            }
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                extracted_data = json.loads(result)
                extracted_data["raw_message"] = message
                return extracted_data
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from AI: {result}")
                return {"is_order": False, "items": [], "error": "Invalid AI response"}
                
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return {"is_order": False, "items": [], "error": f"AI extraction failed: {str(e)}"}
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted order data
        """
        try:
            # Ensure required fields exist
            validated = {
                "is_order": bool(order_data.get("is_order", False)),
                "customer_name": str(order_data.get("customer_name", "")).strip(),
                "items": [],
                "order_time": order_data.get("order_time"),
                "special_instructions": str(order_data.get("special_instructions", "")).strip(),
                "raw_message": str(order_data.get("raw_message", "")).strip(),
                "extraction_method": order_data.get("extraction_method", "pattern")
            }
            
            # Validate and clean items
            for item in order_data.get("items", []):
                if isinstance(item, dict) and item.get("name"):
                    validated_item = {
                        "name": str(item["name"]).strip(),
                        "quantity": max(1, int(item.get("quantity", 1))),
                        "unit": str(item.get("unit", "pcs")).lower().strip(),
                        "notes": str(item.get("notes", "")).strip()
                    }
                    # Skip empty or invalid items
                    if len(validated_item["name"]) >= 2:
                        validated["items"].append(validated_item)
            
            # If no valid items, mark as not an order
            if not validated["items"]:
                validated["is_order"] = False
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating order data: {e}")
            return {
                "is_order": False,
                "items": [],
                "error": f"Validation failed: {str(e)}"
            }


# Singleton instance
ai_extractor = AIOrderExtractor()
