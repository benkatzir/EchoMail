import requests
from email.message import EmailMessage
from base64 import urlsafe_b64encode
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Gmail Server")

# ====== CONFIGURE THIS ======
access_token = "ya29.A0ARrdaM..."  # Replace with your access token
sender = "me"  # or a specific email if you are sending on behalf
to = "recipient@example.com"
subject = "Test Email from Access Token"
body = "Hello, this is a test sent using Gmail API with access token."
# ============================

@mcp.tool()
def create_message(to, subject, body_text):
    message = EmailMessage()
    message.set_content(body_text)
    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject

    raw_message = urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw_message}

@mcp.tool()
def send_email():
    url = f"https://gmail.googleapis.com/gmail/v1/users/{sender}/messages/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    message = create_message(to, subject, body)
    response = requests.post(url, headers=headers, json=message)

    if response.status_code == 200:
        print("✅ Email sent successfully.")
        print("Message ID:", response.json()["id"])
    else:
        print("❌ Failed to send email.")
        print(response.status_code, response.text)

if __name__ == "__main__":
    mcp.run()


