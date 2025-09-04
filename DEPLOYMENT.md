# SMS Adherence Support Program - Deployment Guide

## Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone <repository-url>
cd SMS-Adherence-Support-Program-for-TB-HIV-Patients-

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your SMS provider credentials
```

### 2. Initialize Database
```bash
python cli.py init-db
```

### 3. Start Application
```bash
# Web interface
python app.py

# Command line interface
python cli.py --help
```

## Production Deployment

### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### Using Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables for Production
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/sms_db
SECRET_KEY=your_secure_secret_key
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
ADMIN_PHONE=+254700000000
```

## SMS Provider Setup

### Twilio
1. Sign up at https://www.twilio.com
2. Get Account SID, Auth Token, and phone number
3. Configure webhook URL: `https://yourdomain.com/api/webhook/sms`

### Africa's Talking (Kenya)
1. Sign up at https://africastalking.com
2. Implement provider in `sms_service.py`
3. Configure credentials in `.env`

## CLI Commands

```bash
# System status
python cli.py status

# Patient management
python cli.py add-patient
python cli.py list-patients

# Messaging
python cli.py send-message
python cli.py test-sms

# Alerts
python cli.py list-alerts
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Restrict database access
- [ ] Configure SMS provider webhooks
- [ ] Set up monitoring and logging
- [ ] Regular backup of patient data

## Troubleshooting

### Database Issues
```bash
# Reset database
rm sms_adherence.db
python cli.py init-db
```

### SMS Not Sending
1. Check SMS provider credentials
2. Verify phone number format (+254...)
3. Check provider account balance
4. Review webhook configuration

### Web Interface Issues
1. Check Flask logs
2. Verify static files are accessible
3. Check database connections
4. Review error logs