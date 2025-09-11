import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///sms_adherence.db')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # SMS Provider Configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Application Settings
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'swahili')
    TIMEZONE = os.getenv('TIMEZONE', 'Africa/Nairobi')
    
    # Admin Configuration
    ADMIN_PHONE = os.getenv('ADMIN_PHONE')
    CLINIC_NAME = os.getenv('CLINIC_NAME', 'Health Clinic')
    
    # Reminder Settings
    DEFAULT_REMINDER_TIME = "08:00"  # 8 AM
    MISSED_DOSE_ALERT_DELAY_HOURS = 2  # Alert after 2 hours of no response
    
    # Message Settings
    MAX_MESSAGE_LENGTH = 160  # Standard SMS length
    ENABLE_LOGGING = True