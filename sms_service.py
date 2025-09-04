import logging
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSService:
    """Abstract SMS service interface."""
    
    def __init__(self):
        self.config = Config()
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS to a phone number. Returns status dictionary."""
        raise NotImplementedError("Subclasses must implement send_sms")
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format."""
        # Basic validation - starts with + and contains only digits and +
        if not phone_number.startswith('+'):
            return False
        
        # Remove + and check if remaining characters are digits
        digits_only = phone_number[1:].replace(' ', '').replace('-', '')
        return digits_only.isdigit() and len(digits_only) >= 10

class TwilioSMSService(SMSService):
    """SMS service using Twilio API."""
    
    def __init__(self):
        super().__init__()
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twilio client if credentials are available."""
        try:
            if self.config.TWILIO_ACCOUNT_SID and self.config.TWILIO_AUTH_TOKEN:
                from twilio.rest import Client
                self._client = Client(
                    self.config.TWILIO_ACCOUNT_SID, 
                    self.config.TWILIO_AUTH_TOKEN
                )
                logger.info("Twilio SMS service initialized successfully")
            else:
                logger.warning("Twilio credentials not configured")
        except ImportError:
            logger.error("Twilio package not installed. Run: pip install twilio")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio."""
        if not self._client:
            return {
                'success': False,
                'error': 'Twilio client not initialized',
                'message_id': None,
                'timestamp': datetime.now()
            }
        
        if not self.validate_phone_number(to_number):
            return {
                'success': False,
                'error': 'Invalid phone number format',
                'message_id': None,
                'timestamp': datetime.now()
            }
        
        try:
            # Truncate message if too long
            if len(message) > self.config.MAX_MESSAGE_LENGTH:
                message = message[:self.config.MAX_MESSAGE_LENGTH-3] + "..."
            
            twilio_message = self._client.messages.create(
                body=message,
                from_=self.config.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}, SID: {twilio_message.sid}")
            
            return {
                'success': True,
                'error': None,
                'message_id': twilio_message.sid,
                'timestamp': datetime.now(),
                'status': twilio_message.status
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_id': None,
                'timestamp': datetime.now()
            }

class MockSMSService(SMSService):
    """Mock SMS service for development and testing."""
    
    def __init__(self):
        super().__init__()
        self.sent_messages = []
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending - logs message instead of sending."""
        if not self.validate_phone_number(to_number):
            return {
                'success': False,
                'error': 'Invalid phone number format',
                'message_id': None,
                'timestamp': datetime.now()
            }
        
        # Generate mock message ID
        message_id = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.sent_messages)}"
        
        # Store the message
        sent_message = {
            'to_number': to_number,
            'message': message,
            'message_id': message_id,
            'timestamp': datetime.now(),
            'status': 'sent'
        }
        
        self.sent_messages.append(sent_message)
        
        # Log the message
        logger.info(f"[MOCK SMS] To: {to_number}")
        logger.info(f"[MOCK SMS] Message: {message}")
        logger.info(f"[MOCK SMS] ID: {message_id}")
        
        return {
            'success': True,
            'error': None,
            'message_id': message_id,
            'timestamp': datetime.now(),
            'status': 'sent'
        }
    
    def get_sent_messages(self) -> list:
        """Get list of all sent messages (for testing)."""
        return self.sent_messages.copy()
    
    def clear_sent_messages(self):
        """Clear the sent messages list (for testing)."""
        self.sent_messages.clear()

class AfricasTalkingSMSService(SMSService):
    """SMS service using Africa's Talking API (popular in Kenya)."""
    
    def __init__(self):
        super().__init__()
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Africa's Talking client if credentials are available."""
        try:
            # Africa's Talking would be configured here if credentials exist
            # This is a placeholder for the actual implementation
            logger.info("Africa's Talking SMS service placeholder initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking client: {e}")
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Africa's Talking (placeholder implementation)."""
        # This would contain the actual Africa's Talking implementation
        # For now, falling back to mock behavior
        logger.info(f"[AFRICAS TALKING PLACEHOLDER] Would send SMS to {to_number}: {message}")
        
        return {
            'success': True,
            'error': None,
            'message_id': f"at_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now(),
            'status': 'sent'
        }

class SMSServiceFactory:
    """Factory to create appropriate SMS service based on configuration."""
    
    @staticmethod
    def create_sms_service() -> SMSService:
        """Create and return appropriate SMS service based on configuration."""
        config = Config()
        
        # Check for Twilio configuration
        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
            logger.info("Using Twilio SMS service")
            return TwilioSMSService()
        
        # Default to mock service for development
        logger.info("Using Mock SMS service (development mode)")
        return MockSMSService()

# Global SMS service instance
sms_service = SMSServiceFactory.create_sms_service()