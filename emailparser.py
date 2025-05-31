def extract_headers(header_list):
    headers = {}
    for h in header_list:
        headers[h['name']] = h['value']
    return headers

def parse_gmail_payload(gmail_json):
    headers = extract_headers(gmail_json['payload']['headers'])
    encoded_body = gmail_json['payload']['body'].get('data', '')

    if not encoded_body:
        # Handle multipart later if needed (e.g., parts[0]['body']['data'])
        return None

    decoded = decode_email(encoded_body)  # base64 decoding
    cleaned = strip_html(decoded)  # optional, safe even for plain text

    return {
        "from": headers.get("From", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "body": cleaned
    }
