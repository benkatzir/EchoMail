import os
import subprocess
import requests
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# 1. Twilio credentials and phone numbers
TWILIO_ACCOUNT_SID = "ACed2b59bb3c29bf204ba5b3dbd28a0120"
TWILIO_AUTH_TOKEN  = "14f9148e4ebffdac9f515e7a3f3f8442"
TWILIO_NUMBER      = "+18449594676"   # Your Twilio phone number in E.164 format
USER_NUMBER        = "+14085072051"  # e.g. "+1XXXXXXXXXX"

# 2. OpenAI/DeepSeek credentials
os.environ["OPENAI_API_KEY"] = "your_openai_key_here"

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "fake"),
    base_url="https://strategic-jellyfish-onlyreesh-e1b6a486.koyeb.app/v1",
)

# 3. Incoming email text
email_text = """
Dear Professor,
My lab experiment failed again and I need your immediate assistance before tomorrow morning.
Please let me know as soon as possible.
Best,
Jane Doe
"""

# 4. Classify the email
chat_completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": (
            "You are a strict classifier. Given an incoming email, reply with EXACTLY ONE WORD from:\n"
            "URGENT\nRESEARCH APPLICATIONS\nSTUDENT DOUBTS\nUNI EMAILS\nPUBLICATIONS\n"
            "Do not output anything else."
        )},
        {"role": "user", "content": email_text},
    ],
    model="/models/DeepSeek-R1-Distill-Llama-8B",
    max_tokens=1,
    temperature=0.0,
)

category = 'URGENT'
#chat_completion.choices[0].message.content.strip().upper()

# 5. If URGENT, place a Twilio call with TTS
if category == "URGENT":
    announcement = f"URGENT email received. Content: {email_text}"

    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    twilio_client.calls.create(
        to=USER_NUMBER,
        from_=TWILIO_NUMBER,
        twiml=f"<Response><Say voice='Polly.Joanna'>{announcement}</Say></Response>"
    )
