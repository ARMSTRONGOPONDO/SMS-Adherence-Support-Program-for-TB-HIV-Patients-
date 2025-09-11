#!/usr/bin/env python3
"""
SMS Adherence Support System - Command Line Interface

Provides command-line tools for managing the SMS adherence system.
Usage: python cli.py [command] [options]
"""

import click
import sys
import os
from datetime import date, datetime
from database import DatabaseManager
from config import Config
from sms_service import sms_service
from messaging import message_templates

# Initialize database
db_manager = DatabaseManager(Config.DATABASE_URL.replace('sqlite:///', ''))

@click.group()
def cli():
    """SMS Adherence Support System CLI"""
    pass

@cli.command()
def init_db():
    """Initialize the database with required tables."""
    try:
        db_manager.init_database()
        click.echo("✓ Database initialized successfully!")
    except Exception as e:
        click.echo(f"✗ Error initializing database: {e}")
        sys.exit(1)

@cli.command()
@click.option('--name', prompt='Patient name', help='Full name of the patient')
@click.option('--phone', prompt='Phone number', help='Phone number in international format (+254...)')
@click.option('--treatment', type=click.Choice(['TB', 'HIV', 'TB-HIV']), prompt='Treatment type', help='Type of treatment')
@click.option('--language', default='swahili', help='Preferred language for messages')
@click.option('--med-time', default='08:00', help='Daily medication time (HH:MM format)')
@click.option('--start-date', default=None, help='Treatment start date (YYYY-MM-DD)')
@click.option('--caregiver', default=None, help='Caregiver phone number (optional)')
def add_patient(name, phone, treatment, language, med_time, start_date, caregiver):
    """Add a new patient to the system."""
    try:
        # Validate phone number
        if not sms_service.validate_phone_number(phone):
            click.echo("✗ Invalid phone number format. Use international format (+254...)")
            sys.exit(1)
        
        # Use today's date if no start date provided
        if not start_date:
            start_date = date.today().isoformat()
        
        patient_data = {
            'phone_number': phone,
            'name': name,
            'language': language,
            'treatment_type': treatment,
            'medication_time': med_time,
            'start_date': start_date,
            'caregiver_phone': caregiver
        }
        
        patient_id = db_manager.add_patient(patient_data)
        click.echo(f"✓ Patient added successfully!")
        click.echo(f"  Patient ID: {patient_id}")
        click.echo(f"  Name: {name}")
        click.echo(f"  Phone: {phone}")
        click.echo(f"  Treatment: {treatment}")
        click.echo(f"  Language: {language}")
        
    except Exception as e:
        click.echo(f"✗ Error adding patient: {e}")
        sys.exit(1)

@cli.command()
def list_patients():
    """List all active patients."""
    try:
        patients = db_manager.get_active_patients()
        
        if not patients:
            click.echo("No active patients found.")
            return
        
        click.echo(f"\n{len(patients)} active patients:")
        click.echo("-" * 80)
        
        for patient in patients:
            click.echo(f"ID: {patient['patient_id']}")
            click.echo(f"Name: {patient['name']}")
            click.echo(f"Phone: {patient['phone_number']}")
            click.echo(f"Treatment: {patient['treatment_type']} | Language: {patient['language']}")
            click.echo(f"Medication Time: {patient['medication_time']}")
            click.echo(f"Start Date: {patient['start_date']}")
            click.echo("-" * 80)
            
    except Exception as e:
        click.echo(f"✗ Error listing patients: {e}")
        sys.exit(1)

@cli.command()
@click.option('--patient-id', prompt='Patient ID', help='Patient ID to send message to')
@click.option('--message-type', type=click.Choice(['daily_reminder', 'confirmation', 'missed_dose_warning', 'appointment_reminder']), 
              prompt='Message type', help='Type of message to send')
def send_message(patient_id, message_type):
    """Send a message to a specific patient."""
    try:
        # Get patient information
        patient = db_manager.get_patient(patient_id)
        if not patient:
            click.echo(f"✗ Patient not found: {patient_id}")
            sys.exit(1)
        
        # Get message content
        message_content = message_templates.get_message(message_type, patient['language'])
        
        # Send SMS
        result = sms_service.send_sms(patient['phone_number'], message_content)
        
        # Log the message
        message_data = {
            'patient_id': patient_id,
            'message_type': message_type,
            'content': message_content,
            'language': patient['language'],
            'scheduled_time': datetime.now()
        }
        
        message_id = db_manager.add_message(message_data)
        
        if result['success']:
            db_manager.update_message_status(message_id, 'sent', result['timestamp'])
            click.echo(f"✓ Message sent successfully to {patient['name']}")
            click.echo(f"  Message: {message_content}")
        else:
            db_manager.update_message_status(message_id, 'failed')
            click.echo(f"✗ Failed to send message: {result['error']}")
            
    except Exception as e:
        click.echo(f"✗ Error sending message: {e}")
        sys.exit(1)

@cli.command()
def list_alerts():
    """List all unresolved alerts."""
    try:
        alerts = db_manager.get_unresolved_alerts()
        
        if not alerts:
            click.echo("No unresolved alerts.")
            return
        
        click.echo(f"\n{len(alerts)} unresolved alerts:")
        click.echo("-" * 80)
        
        for alert in alerts:
            severity_icon = "🚨" if alert['severity'] == 'urgent' else "⚠️" if alert['severity'] == 'high' else "ℹ️"
            click.echo(f"{severity_icon} [{alert['severity'].upper()}] {alert['alert_type'].replace('_', ' ').title()}")
            click.echo(f"Patient: {alert['name']} ({alert['phone_number']})")
            click.echo(f"Message: {alert['message']}")
            click.echo(f"Created: {alert['created_at']}")
            click.echo("-" * 80)
            
    except Exception as e:
        click.echo(f"✗ Error listing alerts: {e}")
        sys.exit(1)

@cli.command()
@click.option('--phone', prompt='Phone number', help='Phone number that sent the response')
@click.option('--response', prompt='Response text', help='The SMS response text')
def simulate_response(phone, response):
    """Simulate receiving an SMS response (for testing)."""
    try:
        from scheduler import create_reminder_scheduler
        
        # Create scheduler instance
        scheduler = create_reminder_scheduler(db_manager)
        
        # Process the response
        result = scheduler.process_patient_response(phone, response)
        
        if result['success']:
            click.echo(f"✓ Response processed successfully")
            click.echo(f"  Patient: {result['patient']['name']}")
            click.echo(f"  Response: {response}")
            click.echo(f"  Type: {result['response_data']['response_type']}")
            click.echo(f"  Action: {result['response_data']['action_required']}")
        else:
            click.echo(f"✗ Error processing response: {result['error']}")
            
    except Exception as e:
        click.echo(f"✗ Error simulating response: {e}")
        sys.exit(1)

@cli.command()
@click.option('--phone', prompt='Test phone number', help='Phone number to test SMS sending')
def test_sms(phone):
    """Test SMS sending functionality."""
    try:
        test_message = "Test message from SMS Adherence Support System. This is a connectivity test."
        
        result = sms_service.send_sms(phone, test_message)
        
        if result['success']:
            click.echo(f"✓ Test SMS sent successfully")
            click.echo(f"  To: {phone}")
            click.echo(f"  Message ID: {result['message_id']}")
            click.echo(f"  Status: {result.get('status', 'sent')}")
        else:
            click.echo(f"✗ Failed to send test SMS: {result['error']}")
            
    except Exception as e:
        click.echo(f"✗ Error testing SMS: {e}")
        sys.exit(1)

@cli.command()
def status():
    """Show system status and statistics."""
    try:
        # Get patient count
        patients = db_manager.get_active_patients()
        patient_count = len(patients)
        
        # Get alert count
        alerts = db_manager.get_unresolved_alerts()
        alert_count = len(alerts)
        
        # Get today's response stats
        today = date.today().isoformat()
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Count today's responses
            cursor.execute('''
                SELECT response_type, COUNT(*) as count
                FROM responses
                WHERE DATE(received_time) = ?
                GROUP BY response_type
            ''', (today,))
            
            response_stats = dict(cursor.fetchall())
        
        click.echo("\n📊 SMS Adherence System Status")
        click.echo("=" * 40)
        click.echo(f"👥 Active Patients: {patient_count}")
        click.echo(f"🚨 Unresolved Alerts: {alert_count}")
        click.echo(f"✅ Doses Confirmed Today: {response_stats.get('dose_taken', 0)}")
        click.echo(f"🆘 Help Requests Today: {response_stats.get('need_help', 0)}")
        click.echo(f"❓ Unknown Responses Today: {response_stats.get('unknown', 0)}")
        click.echo("=" * 40)
        
        # Show SMS service status
        sms_class_name = sms_service.__class__.__name__
        if 'Mock' in sms_class_name:
            click.echo("📱 SMS Service: Mock (Development Mode)")
        else:
            click.echo(f"📱 SMS Service: {sms_class_name}")
        
    except Exception as e:
        click.echo(f"✗ Error getting system status: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()