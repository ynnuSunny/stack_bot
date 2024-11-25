import os
from flask import Flask, request, jsonify
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Initialize Slack client
slack_client = WebClient(token=os.environ["SLACK_TOKEN"])
signature_verifier = SignatureVerifier(os.environ["SINGING_SECRET"])

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
        
        if event["type"] == "message" and event.get("channel_type") == "im":
            user_id = event["user"]
            text = event["text"]
            channel = event["channel"]

            print(f"Received DM from user {user_id}: {text}")

            # Optionally, reply to the DM
            slack_client.chat_postMessage(channel=channel, text="Thanks for your message!")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()

