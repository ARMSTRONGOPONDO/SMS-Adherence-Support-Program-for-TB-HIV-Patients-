from typing import Dict, Any

# Message templates in different languages
MESSAGES = {
    'swahili': {
        'daily_reminder': "Habari za asubuhi! Wakati wa kuchukua dawa zako. Jibu '1' ikiwa umechukua, au '2' ikiwa unahitaji msaada.",
        'confirmation': "Asante! Umerekodiwa kwamba umechukua dawa zako leo.",
        'help_received': "Tumepokea ombi lako la msaada. Mfanyakazi wa afya atakupigia hivi karibuni.",
        'missed_dose_warning': "Hujachukua dawa zako leo. Tafadhali chukua sasa na jibu '1' au '2' ikiwa unahitaji msaada.",
        'treatment_completed': "Hongera! Umemaliza matibabu yako kwa ufanisi. Endelea kuwa na afya njema!",
        'appointment_reminder': "Ukumbusho: Una miadi ya kliniki kesho. Tafadhali hakikisha unafika kwa wakati.",
        'medication_refill': "Wakati wa kujaza upya dawa zako. Tembelea kliniki hii wiki au piga simu kwa msaada.",
    },
    'english': {
        'daily_reminder': "Good morning! Time to take your medicine. Reply '1' if taken, or '2' if you need help.",
        'confirmation': "Thank you! We have recorded that you took your medicine today.",
        'help_received': "We received your help request. A healthcare worker will call you soon.",
        'missed_dose_warning': "You haven't taken your medicine today. Please take it now and reply '1' or '2' if you need help.",
        'treatment_completed': "Congratulations! You have successfully completed your treatment. Stay healthy!",
        'appointment_reminder': "Reminder: You have a clinic appointment tomorrow. Please make sure to attend on time.",
        'medication_refill': "Time to refill your medication. Visit the clinic this week or call for assistance.",
    },
    'kikuyu': {
        'daily_reminder': "Githomo kia ruciinii! Ihinda rietu ria kuoya mathata maku. Cuka '1' angikoria woyete, kana '2' angikoria wendaga utethio.",
        'confirmation': "Ngatho! Nitwandikite ati woyete mathata maku umuthi.",
        'help_received': "Nitunyitete ithaithana riaku. Muthuri wa gathitu na mbere akan gukuonia.",
        'missed_dose_warning': "Ndwoyete mathata maku umuthi. Ta oya riumwe ucuke '1' kana '2' angikoria wendaga utethio.",
        'treatment_completed': "Kugenia! Wariu githuti giaku na ma. Ikara una ugima mwega!",
        'appointment_reminder': "Kiririkania: Uri na ciiko ya thibitari ruciu. Ta menya uri na nene ihinda-ini.",
        'medication_refill': "Ihinda ria kwonjoria mathata maku ringi. Thi kinyiga thibitari wiki ii kana guthinia itethio.",
    }
}

class MessageTemplateManager:
    def __init__(self):
        self.messages = MESSAGES
    
    def get_message(self, message_type: str, language: str = 'swahili', **kwargs) -> str:
        """Get a message template in the specified language."""
        # Default to Swahili if language not available
        if language not in self.messages:
            language = 'swahili'
        
        # Default to English if message type not available in specified language
        if message_type not in self.messages[language]:
            if message_type in self.messages['english']:
                language = 'english'
            else:
                return f"Message template '{message_type}' not found."
        
        message = self.messages[language][message_type]
        
        # Format message with any additional parameters
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    
    def get_available_languages(self) -> list:
        """Get list of available languages."""
        return list(self.messages.keys())
    
    def get_available_message_types(self) -> list:
        """Get list of available message types."""
        return list(self.messages['swahili'].keys())
    
    def add_language(self, language: str, messages: Dict[str, str]):
        """Add a new language with message templates."""
        self.messages[language] = messages
    
    def update_message_template(self, language: str, message_type: str, template: str):
        """Update a specific message template."""
        if language not in self.messages:
            self.messages[language] = {}
        self.messages[language][message_type] = template

class ResponseProcessor:
    """Process patient responses and determine appropriate actions."""
    
    RESPONSE_CODES = {
        '1': 'dose_taken',
        '2': 'need_help',
        'yes': 'dose_taken',
        'no': 'missed_dose',
        'help': 'need_help',
        'ndio': 'dose_taken',  # Swahili for yes
        'hapana': 'missed_dose',  # Swahili for no
        'msaada': 'need_help',  # Swahili for help
        'ii': 'dose_taken',  # Kikuyu for yes
        'aca': 'missed_dose',  # Kikuyu for no
        'utethio': 'need_help',  # Kikuyu for help
    }
    
    def __init__(self):
        self.template_manager = MessageTemplateManager()
    
    def process_response(self, response_text: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a patient's SMS response and return appropriate action."""
        response_text = response_text.strip().lower()
        
        # Check for exact matches first
        if response_text in self.RESPONSE_CODES:
            response_type = self.RESPONSE_CODES[response_text]
        else:
            # Check for partial matches
            response_type = 'unknown'
            for code, type_name in self.RESPONSE_CODES.items():
                if code in response_text:
                    response_type = type_name
                    break
        
        result = {
            'patient_id': patient_data['patient_id'],
            'response_text': response_text,
            'response_code': self._get_response_code(response_text),
            'response_type': response_type,
            'action_required': self._determine_action(response_type),
            'follow_up_message': self._get_follow_up_message(response_type, patient_data['language'])
        }
        
        return result
    
    def _get_response_code(self, response_text: str) -> str:
        """Extract the response code from the text."""
        for code in self.RESPONSE_CODES:
            if code in response_text.lower():
                return code
        return 'unknown'
    
    def _determine_action(self, response_type: str) -> str:
        """Determine what action should be taken based on response type."""
        action_map = {
            'dose_taken': 'log_adherence',
            'missed_dose': 'create_alert',
            'need_help': 'create_urgent_alert',
            'unknown': 'request_clarification'
        }
        return action_map.get(response_type, 'no_action')
    
    def _get_follow_up_message(self, response_type: str, language: str) -> str:
        """Get appropriate follow-up message based on response type."""
        if response_type == 'dose_taken':
            return self.template_manager.get_message('confirmation', language)
        elif response_type == 'need_help':
            return self.template_manager.get_message('help_received', language)
        elif response_type == 'missed_dose':
            return self.template_manager.get_message('missed_dose_warning', language)
        else:
            return self.template_manager.get_message('daily_reminder', language)

# Initialize global instances
message_templates = MessageTemplateManager()
response_processor = ResponseProcessor()