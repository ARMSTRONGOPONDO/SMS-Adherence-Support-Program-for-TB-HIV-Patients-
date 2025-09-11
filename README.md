# SMS Adherence Support Program for TB & HIV Patients

A comprehensive SMS-based medication adherence support system designed to help TB and HIV patients in Kenya maintain their treatment schedules through automated reminders, two-way messaging, and healthcare provider alerts.

## 🎯 Project Overview

### The Problem
TB and HIV require strict daily treatment, but many patients in Kenya miss doses due to:
- Forgetfulness or busy schedules
- Travel and distance from clinics
- Stigma around medication
- Side effects and treatment fatigue
- Lack of family support

### Our Solution
A simple, low-cost SMS reminder system that:
- Sends daily medication reminders in local languages
- Enables two-way communication (confirmations, help requests)
- Alerts healthcare workers about missed doses
- Protects patient privacy with discrete messaging
- Works on basic phones without internet

## ✨ Key Features

- **📱 Multi-language SMS Support**: Swahili, English, Kikuyu, and extensible to other local languages
- **⏰ Flexible Scheduling**: Customizable reminder times for each patient
- **🔄 Two-way Messaging**: Patients can confirm doses or request help
- **🚨 Automated Alerts**: Healthcare workers notified of missed doses or help requests
- **👥 Caregiver Support**: Emergency contacts for critical alerts
- **🔒 Privacy Protection**: Discrete messages that don't mention specific conditions
- **📊 Web Dashboard**: Easy patient management and monitoring interface
- **📈 Reporting**: Adherence statistics and response tracking

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │  SMS Scheduler   │    │  SMS Provider   │
│   (Flask App)   │◄──►│   (APScheduler)  │◄──►│ (Twilio/Africa's│
└─────────────────┘    └──────────────────┘    │    Talking)     │
         │                       │              └─────────────────┘
         ▼                       ▼                       ▲
┌─────────────────┐    ┌──────────────────┐              │
│   SQLite DB     │    │ Message Templates│              │
│ (Patient Data)  │    │ (Multi-language) │              │
└─────────────────┘    └──────────────────┘              │
                                │                        │
                                ▼                        │
                       ┌──────────────────┐              │
                       │ Response Handler │──────────────┘
                       │ (Process Replies)│
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite (included with Python)
- SMS Provider Account (Twilio recommended for testing)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ARMSTRONGOPONDO/SMS-Adherence-Support-Program-for-TB-HIV-Patients-.git
   cd SMS-Adherence-Support-Program-for-TB-HIV-Patients-
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your SMS provider credentials
   ```

4. **Initialize the database**:
   ```bash
   python -c "from database import DatabaseManager; DatabaseManager('sms_adherence.db').init_database()"
   ```

5. **Start the application**:
   ```bash
   python app.py
   ```

6. **Access the dashboard**:
   Open http://localhost:5000 in your web browser

### Development Mode (No SMS)
The system includes a mock SMS service for development and testing. Messages will be logged to the console instead of being sent.

## 📋 Usage Guide

### Adding Patients

1. Navigate to "Add Patient" from the dashboard
2. Fill in patient information:
   - Name and phone number (international format: +254...)
   - Treatment type (TB, HIV, or TB-HIV co-infection)
   - Preferred language
   - Daily medication time
   - Treatment start/end dates
   - Optional caregiver contact

### Managing Messages

**Automatic Reminders**: The system automatically sends daily reminders based on each patient's medication schedule.

**Manual Messages**: Send custom messages or use predefined templates:
- Daily reminders
- Dose confirmations
- Missed dose warnings
- Appointment reminders
- Treatment completion congratulations

### Handling Responses

Patients can reply to reminders:
- **"1"** or **"ndio"** (Swahili: yes) → Dose taken confirmation
- **"2"** or **"msaada"** (Swahili: help) → Help request
- **Custom text** → Processed automatically

### Alert Management

The system creates alerts for:
- **Missed Doses**: No response after 2 hours
- **Help Requests**: Patient requests assistance
- **Failed Messages**: SMS delivery failures

Healthcare workers receive notifications and can mark alerts as resolved.

## 🌍 Multi-language Support

### Supported Languages
- **Swahili** (Primary): Standard Swahili messages
- **English**: For English-speaking patients
- **Kikuyu**: For Kikuyu-speaking communities

### Sample Messages

**Daily Reminder (Swahili)**:
> "Habari za asubuhi! Wakati wa kuchukua dawa zako. Jibu '1' ikiwa umechukua, au '2' ikiwa unahitaji msaada."

**Daily Reminder (English)**:
> "Good morning! Time to take your medicine. Reply '1' if taken, or '2' if you need help."

**Confirmation (Swahili)**:
> "Asante! Umerekodiwa kwamba umechukua dawa zako leo."

### Adding New Languages
1. Edit `messaging.py`
2. Add new language dictionary to `MESSAGES`
3. Update response codes in `ResponseProcessor`

## 🔧 Configuration

### Environment Variables
```bash
# SMS Provider (Twilio example)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Database
DATABASE_URL=sqlite:///sms_adherence.db

# Application Settings
SECRET_KEY=your_secret_key
DEFAULT_LANGUAGE=swahili
TIMEZONE=Africa/Nairobi

# Admin Contact
ADMIN_PHONE=+254700000000
CLINIC_NAME=Your Clinic Name
```

### Reminder Schedule
- Default medication time: 8:00 AM
- Missed dose alert delay: 2 hours
- Message character limit: 160 (standard SMS)

## 🔗 SMS Provider Integration

### Twilio (Recommended for Global Use)
1. Sign up at https://www.twilio.com
2. Get Account SID, Auth Token, and phone number
3. Add credentials to `.env` file

### Africa's Talking (Recommended for Kenya)
The system is structured to support Africa's Talking:
1. Sign up at https://africastalking.com
2. Add integration code to `sms_service.py`
3. Update configuration

### Webhook Setup
For receiving SMS responses, configure your SMS provider webhook to:
```
POST /api/webhook/sms
```

## 📊 Database Schema

### Tables
- **patients**: Patient information and treatment details
- **messages**: Sent messages and delivery status
- **responses**: Patient SMS responses
- **alerts**: System alerts and their resolution status

### Key Fields
- Patient ID: Auto-generated unique identifier
- Phone number: International format (+254...)
- Language: Patient's preferred language
- Treatment type: TB, HIV, or TB-HIV
- Medication time: Daily reminder schedule

## 🛡️ Privacy & Security

### Privacy Protection
- Messages are discrete and don't mention specific conditions
- Generic reminders: "Time to take your medicine"
- No medical details in SMS content
- Patient data encrypted in transit

### Security Features
- Input validation and sanitization
- SQL injection prevention
- Phone number format validation
- Rate limiting for API endpoints

### Compliance Considerations
- Designed for healthcare use in Kenya
- Follows SMS privacy best practices
- Secure storage of patient information
- Audit trail for all messages and responses

## 🔧 Development

### Project Structure
```
├── app.py                  # Flask web application
├── database.py            # Database models and operations
├── messaging.py           # Message templates and processing
├── sms_service.py         # SMS provider integrations
├── scheduler.py           # Reminder scheduling system
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
├── static/               # CSS and JavaScript files
└── README.md             # This file
```

### Running Tests
```bash
# Add sample patient for testing
python -c "from app import app; app.cli.run_command('add_sample_patient')"

# Test SMS functionality
curl -X POST http://localhost:5000/api/test_sms \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+254700000000", "message": "Test message"}'
```

### Adding Features
1. **New Message Types**: Add to `messaging.py` MESSAGES dictionary
2. **New Languages**: Extend language support in `messaging.py`
3. **SMS Providers**: Implement new providers in `sms_service.py`
4. **Custom Alerts**: Extend alert types in `scheduler.py`

## 📈 Deployment

### Production Deployment
1. Use production WSGI server (Gunicorn, uWSGI)
2. Set up reverse proxy (Nginx)
3. Use PostgreSQL/MySQL for production database
4. Configure SSL certificates
5. Set up monitoring and logging
6. Configure SMS provider webhooks

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### Environment Variables for Production
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/sms_db
SECRET_KEY=your_production_secret_key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow Python PEP 8 style guide
- Add docstrings to all functions
- Include tests for new features
- Update documentation for changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please:
1. Check the [Issues](https://github.com/ARMSTRONGOPONDO/SMS-Adherence-Support-Program-for-TB-HIV-Patients-/issues) page
2. Create a new issue with detailed description
3. Contact the development team

## 🙏 Acknowledgments

- Designed for healthcare workers supporting TB and HIV patients in Kenya
- Built with consideration for low-resource settings
- Inspired by the need for accessible healthcare technology
- Thanks to the open-source community for tools and libraries

## 📞 Emergency Contacts

For urgent issues related to patient care:
- Configure `ADMIN_PHONE` in environment variables
- System will send urgent alerts for help requests
- Healthcare workers should monitor the dashboard regularly

---

**Note**: This system is designed to support, not replace, professional medical care. Always consult healthcare providers for medical decisions.