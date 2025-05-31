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
user_credentials = {}


app = Flask(__name__)
app.secret_key = os.getenv("GOOGLE_CLIENT_SECRET")
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # ONLY for local dev

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOPIC_NAME = f"projects/{os.getenv("GOOGLE_PROJECT_ID")}/topics/{os.getenv("GOOGLE_TOPIC_ID")}"

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
    # session['flow'] = flow.credentials_to_dict()
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
    print("TOKEN",creds.token)
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
def gmail_notify():
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
