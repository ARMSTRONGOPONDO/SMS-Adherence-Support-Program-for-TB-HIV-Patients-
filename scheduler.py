import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import pytz
from typing import List, Dict, Any

from database import DatabaseManager
from messaging import message_templates, response_processor
from sms_service import sms_service
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Manages scheduling and sending of medication reminders."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = Config()
        self.scheduler = BackgroundScheduler()
        self.timezone = pytz.timezone(self.config.TIMEZONE)
        
        # Start the scheduler
        try:
            self.scheduler.start()
            logger.info("Reminder scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def schedule_daily_reminders(self):
        """Schedule daily reminder checks."""
        # Schedule reminder checks every minute during typical medication hours
        # This allows for flexible medication times while being efficient
        for hour in range(6, 22):  # 6 AM to 10 PM
            for minute in [0, 15, 30, 45]:  # Every 15 minutes
                self.scheduler.add_job(
                    func=self.send_scheduled_reminders,
                    trigger=CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
                    id=f"reminder_check_{hour}_{minute}",
                    replace_existing=True,
                    max_instances=1
                )
        
        logger.info("Daily reminder schedule configured")
    
    def send_scheduled_reminders(self):
        """Send reminders to patients whose medication time has arrived."""
        try:
            current_time = datetime.now(self.timezone).strftime("%H:%M")
            patients = self.db_manager.get_patients_for_reminder(current_time)
            
            if patients:
                logger.info(f"Sending reminders to {len(patients)} patients at {current_time}")
            
            for patient in patients:
                self.send_reminder_to_patient(patient)
                
        except Exception as e:
            logger.error(f"Error in send_scheduled_reminders: {e}")
    
    def send_reminder_to_patient(self, patient: Dict[str, Any]):
        """Send a reminder message to a specific patient."""
        try:
            # Get the reminder message in patient's language
            message = message_templates.get_message(
                'daily_reminder', 
                patient['language']
            )
            
            # Send SMS
            result = sms_service.send_sms(patient['phone_number'], message)
            
            # Log the message in database
            message_data = {
                'patient_id': patient['patient_id'],
                'message_type': 'daily_reminder',
                'content': message,
                'language': patient['language'],
                'scheduled_time': datetime.now(self.timezone)
            }
            
            message_id = self.db_manager.add_message(message_data)
            
            # Update message status based on SMS result
            if result['success']:
                self.db_manager.update_message_status(
                    message_id, 
                    'sent', 
                    result['timestamp']
                )
                logger.info(f"Reminder sent successfully to {patient['name']} ({patient['phone_number']})")
            else:
                self.db_manager.update_message_status(message_id, 'failed')
                logger.error(f"Failed to send reminder to {patient['name']}: {result['error']}")
                
                # Create alert for failed message
                self.create_failed_message_alert(patient, result['error'])
            
            # Schedule missed dose check
            self.schedule_missed_dose_check(patient, message_id)
            
        except Exception as e:
            logger.error(f"Error sending reminder to {patient['patient_id']}: {e}")
    
    def schedule_missed_dose_check(self, patient: Dict[str, Any], message_id: int):
        """Schedule a check for missed doses after a delay."""
        check_time = datetime.now(self.timezone) + timedelta(
            hours=self.config.MISSED_DOSE_ALERT_DELAY_HOURS
        )
        
        job_id = f"missed_dose_check_{patient['patient_id']}_{message_id}"
        
        self.scheduler.add_job(
            func=self.check_for_missed_dose,
            trigger=DateTrigger(run_date=check_time, timezone=self.timezone),
            args=[patient['patient_id'], message_id],
            id=job_id,
            replace_existing=True,
            max_instances=1
        )
        
        logger.info(f"Scheduled missed dose check for {patient['name']} at {check_time}")
    
    def check_for_missed_dose(self, patient_id: str, message_id: int):
        """Check if patient responded to reminder, create alert if not."""
        try:
            # Check if patient responded to the specific message
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM responses 
                    WHERE patient_id = ? AND message_id = ?
                    AND response_type IN ('dose_taken', 'need_help')
                ''', (patient_id, message_id))
                
                response_count = cursor.fetchone()[0]
            
            if response_count == 0:
                # No response received, create missed dose alert
                patient = self.db_manager.get_patient(patient_id)
                if patient:
                    alert_data = {
                        'patient_id': patient_id,
                        'alert_type': 'missed_dose',
                        'message': f"Patient {patient['name']} ({patient['phone_number']}) may have missed their medication dose.",
                        'severity': 'high'
                    }
                    
                    self.db_manager.add_alert(alert_data)
                    logger.warning(f"Created missed dose alert for patient {patient['name']}")
                    
                    # Send follow-up message to patient
                    self.send_missed_dose_warning(patient)
                    
                    # Notify caregiver if configured
                    if patient.get('caregiver_phone'):
                        self.notify_caregiver_missed_dose(patient)
            
        except Exception as e:
            logger.error(f"Error checking for missed dose (patient: {patient_id}, message: {message_id}): {e}")
    
    def send_missed_dose_warning(self, patient: Dict[str, Any]):
        """Send a follow-up warning message for missed dose."""
        try:
            message = message_templates.get_message(
                'missed_dose_warning', 
                patient['language']
            )
            
            result = sms_service.send_sms(patient['phone_number'], message)
            
            # Log the message
            message_data = {
                'patient_id': patient['patient_id'],
                'message_type': 'missed_dose_warning',
                'content': message,
                'language': patient['language'],
                'scheduled_time': datetime.now(self.timezone)
            }
            
            message_id = self.db_manager.add_message(message_data)
            
            if result['success']:
                self.db_manager.update_message_status(message_id, 'sent', result['timestamp'])
                logger.info(f"Missed dose warning sent to {patient['name']}")
            else:
                self.db_manager.update_message_status(message_id, 'failed')
                logger.error(f"Failed to send missed dose warning to {patient['name']}")
                
        except Exception as e:
            logger.error(f"Error sending missed dose warning to {patient['patient_id']}: {e}")
    
    def notify_caregiver_missed_dose(self, patient: Dict[str, Any]):
        """Notify caregiver about patient's missed dose."""
        try:
            if not patient.get('caregiver_phone'):
                return
            
            message = f"ALERT: {patient['name']} may have missed their medication. Please check on them. - {self.config.CLINIC_NAME}"
            
            result = sms_service.send_sms(patient['caregiver_phone'], message)
            
            if result['success']:
                logger.info(f"Caregiver notification sent for patient {patient['name']}")
            else:
                logger.error(f"Failed to notify caregiver for patient {patient['name']}")
                
        except Exception as e:
            logger.error(f"Error notifying caregiver for patient {patient['patient_id']}: {e}")
    
    def create_failed_message_alert(self, patient: Dict[str, Any], error: str):
        """Create alert for failed message delivery."""
        alert_data = {
            'patient_id': patient['patient_id'],
            'alert_type': 'message_failed',
            'message': f"Failed to send message to {patient['name']} ({patient['phone_number']}): {error}",
            'severity': 'medium'
        }
        
        self.db_manager.add_alert(alert_data)
        logger.info(f"Created failed message alert for patient {patient['name']}")
    
    def process_patient_response(self, phone_number: str, response_text: str) -> Dict[str, Any]:
        """Process an incoming SMS response from a patient."""
        try:
            # Find patient by phone number
            patient = self.db_manager.get_patient_by_phone(phone_number)
            
            if not patient:
                logger.warning(f"Received response from unknown number: {phone_number}")
                return {
                    'success': False,
                    'error': 'Unknown patient phone number'
                }
            
            # Process the response
            response_data = response_processor.process_response(response_text, patient)
            
            # Log the response
            self.db_manager.add_response(response_data)
            
            # Take appropriate action based on response
            action = response_data['action_required']
            
            if action == 'log_adherence':
                logger.info(f"Patient {patient['name']} confirmed dose taken")
                
            elif action == 'create_alert':
                alert_data = {
                    'patient_id': patient['patient_id'],
                    'alert_type': 'missed_dose_reported',
                    'message': f"Patient {patient['name']} reported missing their dose",
                    'severity': 'high'
                }
                self.db_manager.add_alert(alert_data)
                
            elif action == 'create_urgent_alert':
                alert_data = {
                    'patient_id': patient['patient_id'],
                    'alert_type': 'help_requested',
                    'message': f"Patient {patient['name']} requested help: '{response_text}'",
                    'severity': 'urgent'
                }
                self.db_manager.add_alert(alert_data)
                
                # Notify admin/healthcare worker immediately
                self.notify_admin_urgent_help(patient, response_text)
            
            # Send follow-up message if needed
            if response_data['follow_up_message']:
                follow_up_result = sms_service.send_sms(
                    patient['phone_number'], 
                    response_data['follow_up_message']
                )
                
                if follow_up_result['success']:
                    logger.info(f"Follow-up message sent to {patient['name']}")
                else:
                    logger.error(f"Failed to send follow-up message to {patient['name']}")
            
            return {
                'success': True,
                'patient': patient,
                'response_data': response_data
            }
            
        except Exception as e:
            logger.error(f"Error processing response from {phone_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_admin_urgent_help(self, patient: Dict[str, Any], response_text: str):
        """Send urgent notification to admin when patient requests help."""
        try:
            if not self.config.ADMIN_PHONE:
                logger.warning("Admin phone not configured for urgent notifications")
                return
            
            message = f"URGENT: Patient {patient['name']} ({patient['phone_number']}) needs help. Response: '{response_text}' - {self.config.CLINIC_NAME}"
            
            result = sms_service.send_sms(self.config.ADMIN_PHONE, message)
            
            if result['success']:
                logger.info(f"Urgent admin notification sent for patient {patient['name']}")
            else:
                logger.error(f"Failed to send urgent admin notification for patient {patient['name']}")
                
        except Exception as e:
            logger.error(f"Error sending urgent admin notification for patient {patient['patient_id']}: {e}")
    
    def shutdown(self):
        """Safely shut down the scheduler."""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Reminder scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

# Function to create and configure scheduler
def create_reminder_scheduler(db_manager: DatabaseManager) -> ReminderScheduler:
    """Create and configure the reminder scheduler."""
    scheduler = ReminderScheduler(db_manager)
    scheduler.schedule_daily_reminders()
    return scheduler