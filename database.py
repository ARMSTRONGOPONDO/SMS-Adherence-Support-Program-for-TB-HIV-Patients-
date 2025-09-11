import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Patients table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE NOT NULL,
                    phone_number TEXT NOT NULL,
                    name TEXT NOT NULL,
                    language TEXT DEFAULT 'swahili',
                    treatment_type TEXT NOT NULL,
                    medication_time TEXT DEFAULT '08:00',
                    start_date DATE NOT NULL,
                    end_date DATE,
                    is_active BOOLEAN DEFAULT 1,
                    caregiver_phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    scheduled_time TIMESTAMP NOT NULL,
                    sent_time TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
                )
            ''')
            
            # Responses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    message_id INTEGER,
                    response_text TEXT NOT NULL,
                    response_code TEXT,
                    response_type TEXT NOT NULL,
                    received_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    is_resolved BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
                )
            ''')
            
            conn.commit()
    
    def add_patient(self, patient_data: Dict[str, Any]) -> str:
        """Add a new patient to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate patient ID
            patient_id = self._generate_patient_id(patient_data['phone_number'])
            
            cursor.execute('''
                INSERT INTO patients 
                (patient_id, phone_number, name, language, treatment_type, 
                 medication_time, start_date, end_date, caregiver_phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                patient_data['phone_number'],
                patient_data['name'],
                patient_data.get('language', 'swahili'),
                patient_data['treatment_type'],
                patient_data.get('medication_time', '08:00'),
                patient_data['start_date'],
                patient_data.get('end_date'),
                patient_data.get('caregiver_phone')
            ))
            
            conn.commit()
            return patient_id
    
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient information by patient ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_patient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get patient information by phone number."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients WHERE phone_number = ?', (phone_number,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_active_patients(self) -> List[Dict[str, Any]]:
        """Get all active patients."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients WHERE is_active = 1')
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def add_message(self, message_data: Dict[str, Any]) -> int:
        """Add a message to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages 
                (patient_id, message_type, content, language, scheduled_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                message_data['patient_id'],
                message_data['message_type'],
                message_data['content'],
                message_data['language'],
                message_data['scheduled_time']
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def update_message_status(self, message_id: int, status: str, sent_time: Optional[datetime] = None):
        """Update message status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if sent_time:
                cursor.execute('''
                    UPDATE messages 
                    SET status = ?, sent_time = ?
                    WHERE id = ?
                ''', (status, sent_time, message_id))
            else:
                cursor.execute('''
                    UPDATE messages 
                    SET status = ?
                    WHERE id = ?
                ''', (status, message_id))
            
            conn.commit()
    
    def add_response(self, response_data: Dict[str, Any]) -> int:
        """Add a patient response to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO responses 
                (patient_id, message_id, response_text, response_code, response_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                response_data['patient_id'],
                response_data.get('message_id'),
                response_data['response_text'],
                response_data.get('response_code'),
                response_data['response_type']
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def add_alert(self, alert_data: Dict[str, Any]) -> int:
        """Add an alert to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts 
                (patient_id, alert_type, message, severity)
                VALUES (?, ?, ?, ?)
            ''', (
                alert_data['patient_id'],
                alert_data['alert_type'],
                alert_data['message'],
                alert_data.get('severity', 'medium')
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_unresolved_alerts(self) -> List[Dict[str, Any]]:
        """Get all unresolved alerts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.*, p.name, p.phone_number 
                FROM alerts a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.is_resolved = 0
                ORDER BY a.created_at DESC
            ''')
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def _generate_patient_id(self, phone_number: str) -> str:
        """Generate a unique patient ID based on phone number."""
        # Create a hash of the phone number and timestamp for uniqueness
        hash_input = f"{phone_number}_{datetime.now().isoformat()}"
        hash_object = hashlib.md5(hash_input.encode())
        return f"PAT_{hash_object.hexdigest()[:8].upper()}"
    
    def get_patients_for_reminder(self, current_time: str) -> List[Dict[str, Any]]:
        """Get patients who should receive reminders at the current time."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM patients 
                WHERE is_active = 1 
                AND medication_time = ?
            ''', (current_time,))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]