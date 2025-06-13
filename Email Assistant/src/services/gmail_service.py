# src/services/gmail_service.py

import sys
import base64
import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import url_for, session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ..utils.helper_functions import is_automated_email, decode_base64



SCOPES_GMAIL = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE_GMAIL = 'credentials_gmail.json'
TOKEN_FILE_GMAIL = 'token_gmail.json'

def load_credentials():
    """Loads or refreshes Gmail credentials."""
    creds = None
    if os.path.exists(TOKEN_FILE_GMAIL):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE_GMAIL, SCOPES_GMAIL)
            logging.info(f"Loaded Gmail credentials from '{TOKEN_FILE_GMAIL}'.")
        except Exception as e:
            logging.error(f"Error loading Gmail token file '{TOKEN_FILE_GMAIL}': {e}. Re-authenticating Gmail.")
            os.remove(TOKEN_FILE_GMAIL)
            creds = None
    return creds

def start_auth_flow(redirect_uri):
    """Starts the Gmail authentication flow."""
    if not os.path.exists(CREDENTIALS_FILE_GMAIL):
        logging.critical(f"Error: Gmail credentials file '{CREDENTIALS_FILE_GMAIL}' not found.")
        logging.critical("Please download it from Google Cloud Console and place it here.")
        return None, "Gmail credentials file missing."
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE_GMAIL, SCOPES_GMAIL, redirect_uri=redirect_uri
        )
        authorization_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        session['gmail_state'] = state
        return authorization_url, None
    except Exception as e:
        logging.error(f"Error starting Gmail authentication: {e}")
        return None, "Gmail authentication error."

def fetch_token(authorization_response, state):
    """Fetches the authentication token from the callback."""
    if session.get('gmail_state') != state:
        logging.error("Gmail state mismatch! Authentication failed.")
        return None, "Gmail authentication failed: State mismatch"
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE_GMAIL, SCOPES_GMAIL, redirect_uri=url_for('gmail_callback', _external=True),
            state=state
        )
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        with open(TOKEN_FILE_GMAIL, 'w') as token:
            token.write(creds.to_json())
        logging.info("Gmail authentication successful.")
        return creds, None
    except Exception as e:
        logging.error(f"Error during Gmail callback: {e}")
        return None, "Gmail authentication failed."

def get_service(creds):
    """Builds and returns the Gmail API service object."""
    try:
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        logging.error(f"Error building Gmail service: {e}")
        return None

def fetch_emails(service, query='is:inbox'):
    """Fetches emails from Gmail based on the query."""
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        return messages
    except HttpError as error:
        logging.error(f'An HTTP error occurred while fetching emails: {error}')
        return None
    except Exception as error:
        logging.exception(f'An unexpected error occurred while fetching emails: {error}')
        return None

def get_email_details(service, msg_id):
    """Gets detailed information about a specific email."""
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])

        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), None)
        recipient = next((header['value'] for header in headers if header['name'].lower() == 'to'), None)
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), ' (No Subject)')
        timestamp_ms = message.get('internalDate')
        timestamp = int(timestamp_ms) / 1000 if timestamp_ms else None
        thread_id = message.get('threadId')

        body = ""
        has_attachment = False

        def find_parts(parts):
            nonlocal body
            nonlocal has_attachment
            plain_body = ""
            html_body = ""
            found_body = False

            for part in parts:
                mime_type = part.get('mimeType', '').lower()
                part_body_data = part.get('body')

                if part.get('filename'):
                    has_attachment = True

                if found_body and has_attachment:
                    continue
                if not part_body_data:
                    if 'parts' in part:
                        nested_plain, nested_html, nested_found = find_parts(part['parts'])
                        if not found_body and nested_found:
                            plain_body = nested_plain
                            html_body = nested_html
                            found_body = nested_found
                    continue

                if mime_type == 'text/plain' and not plain_body:
                    plain_body = decode_base64(part_body_data.get('data'))
                    found_body = True
                elif mime_type == 'text/html' and not html_body:
                    html_body = decode_base64(part_body_data.get('data'))

                if 'parts' in part:
                    nested_plain, nested_html, nested_found = find_parts(part['parts'])
                    if not found_body and nested_found:
                        plain_body = nested_plain
                        html_body = nested_html
                        found_body = nested_found

            return plain_body, html_body, found_body

        if 'parts' in payload:
            plain, html, found = find_parts(payload['parts'])
            body = plain if plain else html
        elif payload.get('body') and payload.get('mimeType', '').startswith('text/'):
            body = decode_base64(payload['body'].get('data'))
            if payload.get('filename'):
                has_attachment = True
        elif payload.get('filename'):
            has_attachment = True

        return {
            'message_id': msg_id,
            'thread_id': thread_id,
            'sender': sender,
            'recipient': recipient,
            'subject': subject,
            'timestamp': timestamp,
            'body': body.strip() if body else "",
            'has_attachment': has_attachment,
        }
    except HttpError as error:
        logging.error(f'An HTTP error occurred while fetching details for message ID {msg_id}: {error}')
        return None
    except Exception as error:
        logging.exception(f'An unexpected error occurred while fetching email details for message ID {msg_id}: {error}')
        return None

def send_reply(service, original_message_id, recipient, subject, reply_body, thread_id):
    """Sends a reply to an email."""
    logging.info(f"Attempting to send reply to {recipient} for message ID: {original_message_id}, subject: {subject}, thread ID: {thread_id}")
    try:
        original_message = service.users().messages().get(userId='me', id=original_message_id, format='metadata', metadataHeaders=['Message-ID']).execute()
        original_message_id_header = next((header['value'] for header in original_message.get('payload', {}).get('headers', []) if header['name'].lower() == 'message-id'), None)

        headers = f"From: me\r\n"
        headers += f"To: {recipient}\r\n"
        headers += f"Subject: {subject}\r\n"
        if original_message_id_header:
            headers += f"In-Reply-To: {original_message_id_header}\r\n"
            headers += f"References: {original_message_id_header}\r\n"
        headers += "\r\n"
        headers += f"{reply_body}"

        message = {
            'raw': base64.urlsafe_b64encode(headers.encode()).decode(),
            'threadId': thread_id
        }
        service.users().messages().send(userId='me', body=message).execute()
        logging.info(f"Reply sent to {recipient} for message ID: {original_message_id}, subject: {subject}, thread ID: {thread_id}")
    except HttpError as error:
        logging.error(f'An HTTP error occurred while sending reply to {recipient}, subject: {subject}: {error}')
    except Exception as error:
        logging.exception(f'An unexpected error occurred while sending reply to {recipient}, subject: {subject}: {error}')
