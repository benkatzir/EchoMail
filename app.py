from flask import Flask, redirect, url_for, session, request
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import json
import pathlib
import requests
load_dotenv()  # Load variables from .env
import base64

import os
from typing import Literal
from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
import re
import asyncio
from functools import wraps
import subprocess
import requests
from openai import OpenAI
from twilio.rest import Client as TwilioClient


user_credentials = {}


app = Flask(__name__)
app.secret_key = os.getenv("GOOGLE_CLIENT_SECRET")
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # ONLY for local dev

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOPIC_NAME = f"projects/{os.getenv("GOOGLE_PROJECT_ID")}/topics/{os.getenv("GOOGLE_TOPIC_ID")}"

# 1. Twilio credentials and phone numbers
TWILIO_ACCOUNT_SID = "ACed2b59bb3c29bf204ba5b3dbd28a0120"
TWILIO_AUTH_TOKEN  = "1d61ce90c9bdb0ef05d59d7f19081861"
TWILIO_NUMBER      = "+18449594676"   # Your Twilio phone number in E.164 format
USER_NUMBER        = "+14085072051"  # e.g. "+1XXXXXXXXXX"

# 2. OpenAI/DeepSeek credentials
os.environ["OPENAI_API_KEY"] = "your_openai_key_here"

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "fake"),
    base_url="https://strategic-jellyfish-onlyreesh-e1b6a486.koyeb.app/v1",
)


def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Define the structured output model
class EmailAnalysis(BaseModel):
    category: Literal[
        "URGENT",
        "Research Applications",
        "Student Queries",
        "University Affairs",
        "Publications",
        "Other"
    ]
    summary: str

# Configure the custom OpenAI-compatible provider
provider = OpenAIProvider(
    api_key=os.getenv("OPENAI_API_KEY", "fake"),
    base_url="https://strategic-jellyfish-onlyreesh-e1b6a486.koyeb.app/v1"
)

# Initialize the OpenAIModel with the custom provider
model = OpenAIModel(
    model_name="/models/DeepSeek-R1-Distill-Llama-8B",
    provider=provider
)

# Create an Agent with the custom model
agent = Agent(model)

class EmailAnalyzer:
    def __init__(self, agent: Agent):
        self.agent = agent

    async def analyze(self, email_body: str) -> EmailAnalysis:
        prompt = (
            "You are an AI assistant that classifies emails into categories and provides a brief summary.\n"
            "Categories and their usage:\n"
            "- URGENT: Time-sensitive matters requiring immediate attention, especially those with deadlines or critical issues\n"
            "- Research Applications: Applications for research positions, grants, or funding requests\n"
            "- Student Queries: Questions about courses, thesis, assignments, or academic progress\n"
            "- University Affairs: Administrative matters, policies, or institutional procedures\n"
            "- Publications: Matters related to academic publications, papers, or journal submissions\n"
            "- Other: Anything that doesn't fit the above categories\n\n"
            f"Email Body:\n{email_body}\n\n"
            "Include a JSON response with category and summary. Note that the category MUST be one of: URGENT, Research Applications, Student Queries, University Affairs, Publications, Other."
        )
        print("Calling agent now")
        response = await self.agent.run(prompt)
        print(f"Agent call succeded: {response}")
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        print("Debug - Raw response:", response_text)  # Debug print
        
        try:
            # First try to find JSON in markdown code blocks
            code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', response_text, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1).strip()
            else:
                # If no code block found, try to find raw JSON object
                json_match = re.search(r'\{[\s\S]*?"category"[\s\S]*?"summary"[\s\S]*?\}', response_text)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON object found in response")

            # Clean the JSON string - handle all common escape sequences
            json_str = (json_str
                       .replace('\\n', '')  # Remove newlines
                       .replace('\\"', '"')  # Fix escaped quotes
                       .replace("\\'", "'")  # Fix escaped apostrophes
                       .replace('\\\\', '\\')  # Fix escaped backslashes
                       .strip())
            print("Debug - Cleaned JSON string:", json_str)  # Debug print
            
            # Parse and validate the JSON
            import json
            parsed_data = json.loads(json_str)
            
            # Ensure the category is valid
            valid_categories = [
                "URGENT",
                "Research Applications",
                "Student Queries",
                "University Affairs",
                "Publications",
                "Other"
            ]
            
            if parsed_data["category"] not in valid_categories:
                raise ValueError(f"Invalid category: {parsed_data['category']}. Must be one of: {', '.join(valid_categories)}")
            
            # Create and validate the EmailAnalysis object
            result = EmailAnalysis(**parsed_data)
            return result
            
        except Exception as e:
            print("Debug - Processing failed:", str(e))
            print("Attempted to parse:", json_str if 'json_str' in locals() else "No JSON string found")
            raise ValueError(f"Failed to process response: {str(e)}")

# Initialize the analyzer
analyzer = EmailAnalyzer(agent)

@app.route('/call', methods=['POST'])
def call_user():
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400

        data = request.get_json()
        email_body = data.get('email_body')
        
        if not email_body:
            return jsonify({
                'status': 'error',
                'message': 'email_body is required'
            }), 400

        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        announcement = f"URGENT email received. Content: {email_body}"
        
        call = twilio_client.calls.create(
            to=USER_NUMBER,
            from_=TWILIO_NUMBER,
            twiml=f"<Response><Say voice='Polly.Joanna'>{announcement}</Say></Response>"
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Call initiated successfully',
            'call_sid': call.sid
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/categorize', methods=['POST'])
@async_route
async def categorize_email():
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400

        data = request.get_json()
        email_body = data.get('email_body')
        
        await categorize(email_body=email_body)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

async def categorize(email_body):
    try:
        
        if not email_body:
            return jsonify({
                'status': 'error',
                'message': 'email_body is required'
            }), 400

        print("waiting for response")
        result = await analyzer.analyze(email_body)
        print("response recieved")

        if (result.category == "URGENT"):
            call_user()
        return jsonify({
            'status': 'success',
            'category': result.category,
            'summary': result.summary
        })
        

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 

@app.route('/')
def index():
    if 'credentials' not in session:
        return '<a href="/authorize">Login with Google</a>'
    return 'Logged in. Gmail watch active. <a href="/logout">Logout</a>'

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    # Save credentials in user session
    session['credentials'] = credentials_to_dict(creds)


    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    email_address = profile['emailAddress']
    user_credentials[email_address] = creds  # Store creds mapped to email

    print(f"Authenticated: {email_address}")

    # Call Gmail API to set up watch
    service = build('gmail', 'v1', credentials=creds)
    watch_request = {
        'topicName': TOPIC_NAME,
        'labelIds': ['INBOX'],
        'labelFilterAction': 'include'
    }
    response = service.users().watch(userId='me', body=watch_request).execute()
    print("Gmail watch response:", response)

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/gmail-webhook', methods=['POST'])
@async_route
async def gmail_notify():
    data = request.get_json()
    print("Received Gmail notification:", data)

    try:
        encoded_data = data['message']['data']
        decoded_data = base64.urlsafe_b64decode(encoded_data).decode('utf-8')
        payload = json.loads(decoded_data)

        user_email = payload.get("emailAddress")
        history_id = payload.get("historyId")  # optional for future use

        creds = user_credentials.get(user_email)
        if not creds:
            print(f"No credentials found for {user_email}")
            return '', 200

        # Rebuild service and get latest messages
        service = build('gmail', 'v1', credentials=creds)
        messages = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX']).execute().get('messages', [])

        if not messages:
            print("No new messages found.")
            return '', 200

        msg_id = messages[0]['id']
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        # Extract the body
        snippet = msg.get("snippet")
        print(f"New email: {snippet}")

        # Run categorization in background
        await categorize(email_body=snippet)
        


    except Exception as e:
        print("Error processing Gmail notification:", e)

    return '', 200

# Utility to convert Flow creds to dict
def credentials_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)
