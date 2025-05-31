#FastAPI MCP server
# FastAPI MCP server for Gmail actions
# mcp_gmail_server.py, May, 31 Koyeb Tenstorrent.

from fastapi import FastAPI, Request
from pydantic import BaseModel
from gmail_api import get_emails_by_category
from pydantic import BaseModel
import requests
import openai
import os
from mcp.server.fastmcp import FastMCP

openai.api_key = os.getenv("OPENAI_API_KEY")

# Create MCP server
mcp = FastMCP("Gmail Server")

app = FastAPI()

class ReadEmailPayload(BaseModel):
    action: str
    filters: dict


@app.post("/")
@mcp.tool()
async def handle_mcp_action(payload: ReadEmailPayload):
    # 1. Send payload to AI agent for commentary or instruction
    ai_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an email assistant helping decide what to do with Gmail actions."},
            {"role": "user", "content": f"Payload received: {payload}. What should the system do?"}
        ]
    )
    agent_thought = ai_response["choices"][0]["message"]["content"]

    if payload.action == "read_email":
        category = payload.filters.get("category", "CATEGORY_PERSONAL")
        max_results = payload.filters.get("max_results", 5)
        emails = get_emails_by_category(category, max_results)
        return {"emails": emails, "agent_interpretation": agent_thought}
    return {"error": "Unsupported action"}, 400

# Run the server if the script is executed directly
if __name__ == "__main__":  
    mcp.run()
