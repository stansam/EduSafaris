"""
Notification utilities for sending various types of notifications
"""

def send_notification(recipient_id, sender_id, type, title, message, data=None):
    """
    Send a notification to a user
    
    Args:
        recipient_id: ID of the user to receive the notification
        sender_id: ID of the user sending the notification
        type: Type of notification (e.g., 'booking_request', 'trip_update')
        title: Notification title
        message: Notification message
        data: Optional additional data as dict
    """
    # This is a placeholder implementation
    # In a real application, you would:
    # 1. Create a Notification model record
    # 2. Send email notifications
    # 3. Send SMS notifications if configured
    # 4. Send push notifications if supported
    
    print(f"Notification sent to user {recipient_id}: {title}")
    return True