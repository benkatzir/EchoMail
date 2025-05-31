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
    print("TOKEN", creds.token)
    print("REFRESH TOKEN", creds.refresh_token)


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

from email.utils import parseaddr

@app.route('/gmail-webhook', methods=['POST'])
def gmail_notify():
    data = request.get_json()
    print("Received Gmail notification:", data)

    try:
        encoded_data = data['message']['data']
        decoded_data = base64.urlsafe_b64decode(encoded_data).decode('utf-8')
        payload = json.loads(decoded_data)

        user_email = payload.get("emailAddress")
        creds = user_credentials.get(user_email)
        if not creds:
            print(f"No credentials found for {user_email}")
            return '', 200

        service = build('gmail', 'v1', credentials=creds)

        # Get the latest message
        messages = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX']).execute().get('messages', [])
        if not messages:
            print("No new messages found.")
            return '', 200

        msg_id = messages[0]['id']
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

        headers = msg['payload'].get('headers', [])
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        subject_header = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')

        # Extract plain text body
        body = ''
        payload = msg['payload']
        if payload.get('mimeType') == 'text/plain':
            body = payload['body'].get('data', '')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    body = part['body'].get('data', '')
                    break

        # Ensure body is decoded if not already
        if body:
            body_bytes = base64.urlsafe_b64decode(body + '==')  # add padding if needed
            encoded_body = base64.b64encode(body_bytes).decode('utf-8')
        else:
            encoded_body = ''

        # Print final JSON
        email_json = {
            "token": "ya29.a0AW4XtxgBj6qbVemA5LDXLntG3K9J5fce-_lAUsNVlw7PY-yFKjQ9qGDEqj0uhn_gx2_wHmYJZaHsV_-15WG-_wtWpZUo1ZSFSYWTw4zUIOOfdFjInIZebk9BDPzq4v8hRuhvQZfoVOzdjywGe8TQRi9pQ_dYyT_j0q-NCXVgaCgYKAcUSARYSFQHGX2MiL0BlyldVOy2fDqM48TXq6w0175",
            "refresh_token": "1//06khMOaO6Nw88CgYIARAAGAYSNwF-L9IrEBO6rY5uRVa8hOC1_Bx7d1wVo9pU5A5P0C11dIvBUpnq1LEmFojjx7K3BDS9PLMBbPE",
            "body": encoded_body
        }

        print(json.dumps(email_json, indent=2))

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
