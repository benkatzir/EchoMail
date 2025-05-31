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

# Load environment variables
load_dotenv()

def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

app = Flask(__name__)

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
        response = await self.agent.run(prompt)
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

@app.route('/test', methods=['GET'])
def test_endpoint():
    return {
        'status': 'success',
        'message': 'Test endpoint is working!'
    }

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
        
        if not email_body:
            return jsonify({
                'status': 'error',
                'message': 'email_body is required'
            }), 400

        result = await analyzer.analyze(email_body)
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

if __name__ == '__main__':
    app.run(debug=True) 