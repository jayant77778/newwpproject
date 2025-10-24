"""
Simple AI Service for testing - processes WhatsApp messages
"""
import re
from typing import Dict, Any


class AIOrderExtractor:
    def __init__(self):
        self.ai_enabled = False  # Disabled for testing
    
    def extract_order_from_message(self, message: str, sender_name: str = "") -> Dict[str, Any]:
        """Extract order information from WhatsApp message using basic patterns"""
        return {
            "is_order": False,
            "items": [],
            "order_time": None,
            "notes": "Basic pattern extraction",
            "extraction_method": "pattern"
        }
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean order data"""
        return {
            "customer_name": str(order_data.get("customer_name", "")).strip(),
            "items": order_data.get("items", []),
            "order_time": order_data.get("order_time"),
            "special_instructions": str(order_data.get("special_instructions", "")).strip(),
            "is_order": bool(order_data.get("is_order", False)),
            "extraction_method": order_data.get("extraction_method", "pattern")
        }


# Initialize the extractor
ai_extractor = AIOrderExtractor()


def extract_order_info(message: str, sender_name: str = "") -> Dict[str, Any]:
    """Main function to extract order information"""
    return ai_extractor.extract_order_from_message(message, sender_name)


def validate_order_data(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate order data"""
    return ai_extractor.validate_order_data(order_data)
