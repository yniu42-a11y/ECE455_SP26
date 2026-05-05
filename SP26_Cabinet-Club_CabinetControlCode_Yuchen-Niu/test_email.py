#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 4B Vending Machine - Email Notification Module
Sends email alerts to administrator using SendGrid API
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# SendGrid Configuration
SENDGRID_API_KEY = "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"
FROM_EMAIL = "yniu42@wisc.edu"
TO_EMAIL = "enso4881@gmail.com"
EMAIL_SUBJECT = "test"

def send_email(message_text="This is a test"):
    """
    Send email to administrator using SendGrid API
    
    Args:
        message_text (str): Email body content, default is "This is a test"
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create email message
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAIL,
            subject=EMAIL_SUBJECT,
            plain_text_content=message_text
        )
        
        # Send email via SendGrid
        print("Connecting to SendGrid API...")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Check response status
        if response.status_code == 202:
            print("Email sent successfully!")
            print(f"Status Code: {response.status_code}")
            return True
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response body: {response.body}")
            print(f"Response headers: {response.headers}")
            return False
            
    except Exception as e:
        print(f"Error sending email: {e}")
        # Try to get more details if available
        if hasattr(e, 'body'):
            print(f"Error details: {e.body}")
        if hasattr(e, 'to_dict'):
            print(f"Full error: {e.to_dict}")
        return False

def main():
    """
    Main function - Send test email
    """
    print("=" * 50)
    print("Raspberry Pi Vending Machine - Email Test")
    print("=" * 50)
    print()
    
    # Send test email
    send_email("3/3/2026 - This is a test for email notification from Raspberry Pi Vending Machine.")

if __name__ == "__main__":
    main()