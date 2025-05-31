import json
from email_parser import parse_gmail_payload

with open('gmail_payloads.json', 'r') as f:
    raw_payloads = json.load(f)

processed_emails = []
for payload in raw_payloads:
    parsed = parse_gmail_payload(payload)
    if parsed:
        formatted = f"From: {parsed['from']}\nSubject: {parsed['subject']}\nDate: {parsed['date']}\n\n{parsed['body']}"
        processed_emails.append(formatted)

# Run the summarizer + reply generator
results = run_agent({
    'summarize': processed_emails,
    'reply': processed_emails
})

print("\n=== DAILY SUMMARY ===\n")
print(results['summary'])

print("\n=== SUGGESTED REPLIES ===\n")
for i, reply in enumerate(results['replies']):
    print(f"\n--- Reply #{i+1} ---\n{reply}")
