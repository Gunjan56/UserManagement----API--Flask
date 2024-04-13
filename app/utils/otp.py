import random
from twilio.rest import Client
from flask import current_app
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_otp(email):
    otp = ''.join(random.choice('0123456789') for _ in range(6))
    message = client.messages.create(
        body=f"Your OTP for account activation is: {otp}",
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=email
    )
    return message 