from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date
import os
from database import DatabaseManager
from scheduler import create_reminder_scheduler
from messaging import message_templates
from sms_service import sms_service
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database and scheduler
db_manager = DatabaseManager(Config.DATABASE_URL.replace('sqlite:///', ''))
reminder_scheduler = create_reminder_scheduler(db_manager)

@app.route('/')
def dashboard():
    """Main dashboard showing system overview."""
    try:
        # Get active patients count
        active_patients = db_manager.get_active_patients()
        
        # Get unresolved alerts
        alerts = db_manager.get_unresolved_alerts()
        
        # Get recent messages (last 10)
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, p.name, p.phone_number 
                FROM messages m
                JOIN patients p ON m.patient_id = p.patient_id
                ORDER BY m.created_at DESC
                LIMIT 10
            ''')
            recent_messages = [dict(row) for row in cursor.fetchall()]
        
        # Get response statistics for today
        today = date.today().isoformat()
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT response_type, COUNT(*) as count
                FROM responses
                WHERE DATE(received_time) = ?
                GROUP BY response_type
            ''', (today,))
            
            response_stats = dict(cursor.fetchall())
        
        return render_template('dashboard.html', 
                             active_patients=len(active_patients),
                             alerts=alerts,
                             recent_messages=recent_messages,
                             response_stats=response_stats)
    
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'error')
        return render_template('dashboard.html', 
                             active_patients=0,
                             alerts=[],
                             recent_messages=[],
                             response_stats={})

@app.route('/patients')
def patients():
    """List all patients."""
    try:
        patients_list = db_manager.get_active_patients()
        return render_template('patients.html', patients=patients_list)
    except Exception as e:
        flash(f'Error loading patients: {e}', 'error')
        return render_template('patients.html', patients=[])

@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
    """Add a new patient."""
    if request.method == 'POST':
        try:
            patient_data = {
                'phone_number': request.form['phone_number'],
                'name': request.form['name'],
                'language': request.form.get('language', 'swahili'),
                'treatment_type': request.form['treatment_type'],
                'medication_time': request.form.get('medication_time', '08:00'),
                'start_date': request.form['start_date'],
                'end_date': request.form.get('end_date') or None,
                'caregiver_phone': request.form.get('caregiver_phone') or None
            }
            
            # Validate phone number
            if not sms_service.validate_phone_number(patient_data['phone_number']):
                flash('Invalid phone number format. Please use international format (+254...)', 'error')
                return render_template('add_patient.html', 
                                     languages=message_templates.get_available_languages())
            
            # Check if patient already exists
            existing_patient = db_manager.get_patient_by_phone(patient_data['phone_number'])
            if existing_patient:
                flash('Patient with this phone number already exists', 'error')
                return render_template('add_patient.html', 
                                     languages=message_templates.get_available_languages())
            
            patient_id = db_manager.add_patient(patient_data)
            flash(f'Patient added successfully! Patient ID: {patient_id}', 'success')
            return redirect(url_for('patients'))
            
        except Exception as e:
            flash(f'Error adding patient: {e}', 'error')
    
    return render_template('add_patient.html', 
                         languages=message_templates.get_available_languages())

@app.route('/patients/<patient_id>')
def patient_detail(patient_id):
    """Show patient details and history."""
    try:
        patient = db_manager.get_patient(patient_id)
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        # Get patient's messages
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM messages 
                WHERE patient_id = ?
                ORDER BY created_at DESC
                LIMIT 50
            ''', (patient_id,))
            messages = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT * FROM responses 
                WHERE patient_id = ?
                ORDER BY received_time DESC
                LIMIT 50
            ''', (patient_id,))
            responses = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT * FROM alerts 
                WHERE patient_id = ?
                ORDER BY created_at DESC
                LIMIT 20
            ''', (patient_id,))
            alerts = [dict(row) for row in cursor.fetchall()]
        
        return render_template('patient_detail.html',
                             patient=patient,
                             messages=messages,
                             responses=responses,
                             alerts=alerts)
    
    except Exception as e:
        flash(f'Error loading patient details: {e}', 'error')
        return redirect(url_for('patients'))

@app.route('/alerts')
def alerts():
    """Show all unresolved alerts."""
    try:
        alerts_list = db_manager.get_unresolved_alerts()
        return render_template('alerts.html', alerts=alerts_list)
    except Exception as e:
        flash(f'Error loading alerts: {e}', 'error')
        return render_template('alerts.html', alerts=[])

@app.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved."""
    try:
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET is_resolved = 1, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE id = ?
            ''', ('Admin', alert_id))
            conn.commit()
        
        flash('Alert resolved successfully', 'success')
    except Exception as e:
        flash(f'Error resolving alert: {e}', 'error')
    
    return redirect(url_for('alerts'))

@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    """Send a custom message to a patient."""
    if request.method == 'POST':
        try:
            patient_id = request.form['patient_id']
            message_type = request.form['message_type']
            custom_message = request.form.get('custom_message', '')
            
            patient = db_manager.get_patient(patient_id)
            if not patient:
                flash('Patient not found', 'error')
                return redirect(url_for('send_message'))
            
            # Get message content
            if message_type == 'custom':
                message_content = custom_message
            else:
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
                flash(f'Message sent successfully to {patient["name"]}', 'success')
            else:
                db_manager.update_message_status(message_id, 'failed')
                flash(f'Failed to send message: {result["error"]}', 'error')
                
        except Exception as e:
            flash(f'Error sending message: {e}', 'error')
    
    # Get all active patients for the form
    try:
        patients_list = db_manager.get_active_patients()
        message_types = message_templates.get_available_message_types()
    except Exception as e:
        flash(f'Error loading data: {e}', 'error')
        patients_list = []
        message_types = []
    
    return render_template('send_message.html', 
                         patients=patients_list,
                         message_types=message_types)

@app.route('/api/webhook/sms', methods=['POST'])
def sms_webhook():
    """Webhook endpoint for receiving SMS responses."""
    try:
        # This would typically receive data from SMS provider webhook
        # For Twilio, the format would be different
        phone_number = request.form.get('From') or request.json.get('phone_number')
        message_text = request.form.get('Body') or request.json.get('message')
        
        if not phone_number or not message_text:
            return jsonify({'error': 'Missing phone number or message'}), 400
        
        # Process the response
        result = reminder_scheduler.process_patient_response(phone_number, message_text)
        
        if result['success']:
            return jsonify({'status': 'success', 'message': 'Response processed'})
        else:
            return jsonify({'status': 'error', 'message': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_sms', methods=['POST'])
def test_sms():
    """Test SMS sending (development endpoint)."""
    try:
        phone_number = request.json.get('phone_number')
        message = request.json.get('message', 'Test message from SMS Adherence System')
        
        if not phone_number:
            return jsonify({'error': 'Phone number required'}), 400
        
        result = sms_service.send_sms(phone_number, message)
        
        return jsonify({
            'success': result['success'],
            'message_id': result['message_id'],
            'error': result['error']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

# CLI Commands
@app.cli.command()
def init_db():
    """Initialize the database."""
    try:
        db_manager.init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")

@app.cli.command()
def add_sample_patient():
    """Add a sample patient for testing."""
    try:
        sample_patient = {
            'phone_number': '+254700000001',
            'name': 'John Doe',
            'language': 'swahili',
            'treatment_type': 'TB',
            'medication_time': '08:00',
            'start_date': date.today().isoformat(),
            'caregiver_phone': '+254700000002'
        }
        
        patient_id = db_manager.add_patient(sample_patient)
        print(f"Sample patient added successfully! Patient ID: {patient_id}")
    except Exception as e:
        print(f"Error adding sample patient: {e}")

if __name__ == '__main__':
    try:
        # Ensure templates directory exists
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('static/js', exist_ok=True)
        
        print("SMS Adherence Support System starting...")
        print(f"Dashboard will be available at http://localhost:5000")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        reminder_scheduler.shutdown()
    except Exception as e:
        print(f"Error starting application: {e}")
        reminder_scheduler.shutdown()