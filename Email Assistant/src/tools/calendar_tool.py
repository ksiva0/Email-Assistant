import logging
import sys
import os
from src.services import gcal_service, slack_service


def schedule_meeting_and_notify(gmail_details, gcal_creds):
    """Schedules a meeting on Google Calendar and notifies on Slack."""
    if gcal_creds and gcal_service.get_service(gcal_creds):
        gcal_srv = gcal_service.get_service(gcal_creds)
        event_details = gcal_service.format_event_details(
            gmail_details['sender'], gmail_details['subject'], gmail_details['body']
        )
        created_event = gcal_service.create_event(gcal_srv, event_details)
        if created_event:
            slack_client = slack_service.get_client()
            if slack_client:
                slack_message = f"Meeting scheduled with {gmail_details['sender']}: {created_event.get('htmlLink')}"
                slack_service.send_message(slack_client, slack_message)
            return True
        else:
            logging.error("Failed to create Google Calendar event.")
            return False
    else:
        logging.warning("Google Calendar not authenticated. Cannot schedule meeting.")
        slack_client = slack_service.get_client()
        if slack_client:
            slack_service.send_message(slack_client, "Received a meeting request but Google Calendar is not authenticated.")
        return False
