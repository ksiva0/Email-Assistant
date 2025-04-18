import os
import logging
import time
from google.oauth2.service_account import Credentials as GCalServiceAccountCredentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build as build_gcal
from googleapiclient.errors import HttpError
from flask import url_for, session

SCOPES_GCAL = ['https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_FILE_GCAL = 'credentials_gcal.json'
TOKEN_FILE_GCAL = 'token_gcal.json'

def load_credentials():
    """Loads or refreshes Google Calendar credentials."""
    creds = None
    if os.path.exists(TOKEN_FILE_GCAL):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE_GCAL, SCOPES_GCAL)
            logging.info(f"Loaded Google Calendar credentials from '{TOKEN_FILE_GCAL}'.")
        except Exception as e:
            logging.error(f"Error loading Google Calendar token file '{TOKEN_FILE_GCAL}': {e}. Re-authenticating Google Calendar.")
            os.remove(TOKEN_FILE_GCAL)
            creds = None
    return creds

def start_auth_flow(redirect_uri):
    """Starts the Google Calendar authentication flow."""
    if not os.path.exists(CREDENTIALS_FILE_GCAL):
        logging.critical(f"Error: Google Calendar credentials file '{CREDENTIALS_FILE_GCAL}' not found.")
        logging.critical("Please download it from Google Cloud Console and place it here.")
        return None, "Google Calendar credentials file missing."
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE_GCAL, SCOPES_GCAL, redirect_uri=redirect_uri
        )
        authorization_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        session['gcal_state'] = state
        return authorization_url, None
    except Exception as e:
        logging.error(f"Error starting Google Calendar authentication: {e}")
        return None, "Google Calendar authentication error."

def fetch_token(authorization_response, state):
    """Fetches the authentication token from the callback."""
    if session.get('gcal_state') != state:
        logging.error("Google Calendar state mismatch! Authentication failed.")
        return None, "Google Calendar authentication failed: State mismatch"
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE_GCAL, SCOPES_GCAL, redirect_uri=url_for('gcal_callback', _external=True),
            state=state
        )
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        with open(TOKEN_FILE_GCAL, 'w') as token:
            token.write(creds.to_json())
        logging.info("Google Calendar authentication successful.")
        session['gcal_authenticated'] = True
        return creds, None
    except Exception as e:
        logging.error(f"Error during Google Calendar callback: {e}")
        return None, "Google Calendar authentication failed."

def get_service(creds):
    """Builds and returns the Google Calendar API service object."""
    try:
        return build_gcal('calendar', 'v3', credentials=creds)
    except Exception as e:
        logging.error(f"Error building Google Calendar service: {e}")
        return None

def create_event(service, event_details, calendar_id='primary'):
    """Creates an event on Google Calendar."""
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event_details).execute()
        logging.info(f"Google Calendar event created: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as error:
        logging.error(f'An error occurred while creating Google Calendar event: {error}')
        return None
    except Exception as e:
        logging.error(f'An unexpected error occurred during Google Calendar event creation: {e}')
        return None

def format_event_details(sender, subject, body):
    """Formats event details for Google Calendar."""
    start_time = time.strftime('%Y-%m-%dT%H:%S%z', time.localtime(time.time() + 7200))
    end_time = time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime(time.time() + 7200))
    time_zone = 'Asia/Kolkata'

    return {
        'summary': f"Meeting Request from {sender}",
        'description': f"Meeting requested based on email: {subject}\n\n{body}",
        'start': {'dateTime': start_time, 'timeZone': time_zone},
        'end': {'dateTime': end_time, 'timeZone': time_zone},
        'attendees': [{'email': sender}],
    }
