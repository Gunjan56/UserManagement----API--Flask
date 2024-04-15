from flask import current_app
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()
from twilio.rest import Client
client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])


def send_otp_sms(phone_number, otp):
    try:
        message = client.messages.create(
            body=f'Your OTP for account activation is: {otp}',
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=phone_number
        )
        print(f"OTP sent to {phone_number} successfully.")
        return message
    except Exception as e:
        print(f"Failed to send OTP to {phone_number}: {str(e)}")


