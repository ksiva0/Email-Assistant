# src/services/slack_service.py
import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#general" 

def get_client():
    """Returns a Slack WebClient instancmyenv\Scripts\activate."""
    if not SLACK_BOT_TOKEN:
        logging.error("SLACK_BOT_TOKEN environment variable not set.")
        return None
    return WebClient(token=SLACK_BOT_TOKEN)

def send_message(client, message, channel=SLACK_CHANNEL):
    """Sends a message to a Slack channel."""
    if not client:
        logging.error("Slack client is not initialized.")
        return None

    try:
        response = client.chat_postMessage(channel=channel, text=message)
        logging.info(f"Slack message sent to {channel}: {response['message']['text']}")
        return response
    except SlackApiError as e:
        logging.error(f"Slack API error: {e.response['error']}")
    except Exception as e:
        logging.error(f"Unexpected error sending Slack message: {e}")
    return None
