import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_emails(email_threads):
    formatted = "\n\n---\n\n".join(email_threads)

    prompt = f"""
    You are a helpful assistant. Here's a set of emails from today. Write a concise, professional summary:

    {formatted}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message['content']

def generate_replies(email_threads):
    replies = []
    for thread in email_threads:
        prompt = f"""
        You are drafting a polite and relevant reply to the following email:

        {thread}

        Reply:
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )

        replies.append(response.choices[0].message['content'])
    return replies

def run_agent(tasks):
    results = {}
    if 'summarize' in tasks:
        results['summary'] = summarize_emails(tasks['summarize'])
    if 'reply' in tasks:
        results['replies'] = generate_replies(tasks['reply'])
    return results
