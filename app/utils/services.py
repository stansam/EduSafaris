from app.utils.utils import send_email, send_sms

class EmergencyNotificationService:
    """Service for handling emergency notifications"""
    
    @staticmethod
    def send_emergency_alert(emergency, recipients):
        """Send emergency alert to multiple recipients"""
        subject = f"EMERGENCY ALERT: {emergency.title}"
        
        # Send emails
        for recipient in recipients:
            if recipient.email:
                send_email(
                    to=recipient.email,
                    subject=subject,
                    template='emergency_alert',
                    emergency=emergency,
                    recipient=recipient
                )
            
            # Send SMS for critical emergencies
            if emergency.severity in ['high', 'critical'] and recipient.phone:
                sms_message = f"EMERGENCY: {emergency.title}. Location: {emergency.location_description or 'Location TBD'}. Contact: {emergency.reporter_phone or 'N/A'}"
                send_sms(recipient.phone, sms_message)