import os
import time
import requests
from flask import Flask, request, jsonify
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def get_openai_response(user_message: str):
    # OpenAI API endpoint
    url = "https://api.openai.com/v1/chat/completions"

    # Request payload
    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": user_message}]
    }

    # Request headers
    headers = {
        "Authorization": f"Bearer {os.environ['PUBLIC_OPENAI_KEY']}",
        "Content-Type": "application/json"
    }

    # Make the request
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raise an error for HTTP failures

    # Parse the response
    response_data = response.json()
    return response_data["choices"][0]["message"]["content"]

app = Flask(__name__)

# Initialize Slack client
slack_client = WebClient(token=os.environ["SLACK_TOKEN"])
signature_verifier = SignatureVerifier(os.environ["SINGING_SECRET"])
processed_events = {}

@app.route("/slack/events", methods=["POST"])
def slack_events():
    # Parse the request from Slack
    event_data = request.json

    # Handle the URL verification challenge
    if event_data.get("type") == "url_verification":
        challenge = event_data["challenge"]
        print(challenge)
        return jsonify({"challenge": challenge})

    # Handle other event types (e.g., DMs)
    if "event" in event_data:
        event = event_data["event"]
        print("event: ")
        print(event)

        if "bot_id" in event:
            print("Ignored bot message.")
            return jsonify({"status": "ignored"})
        # Check if this event has already been processed
        event_id = event_data.get("event_id")
        current_time = time.time()
        if event_id in processed_events:
            print(f"Ignoring duplicate event: {event_id}")
            return jsonify({"status": "duplicate"})

        # Add event_id to processed events with a timestamp
        processed_events[event_id] = current_time

        # Clean up old events from the store (e.g., older than 60 seconds)
        for old_event_id in list(processed_events):
            if current_time - processed_events[old_event_id] > 60:
                del processed_events[old_event_id]
        
        if event["type"] == "message" and event.get("channel_type") == "im":
            user_id = event["user"]
            text = event["text"]
            channel = event["channel"]

            print(f"Received DM from user {user_id}: {text}")

            # Optionally, reply to the DM
            response_test = get_openai_response(text)
            slack_client.chat_postMessage(channel=channel, text=response_test)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()

