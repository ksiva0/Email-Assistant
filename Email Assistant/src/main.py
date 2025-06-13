# src/main.py

import os
import ssl
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, url_for, session, request
from .controllers import email_controller
from .services import gmail_service, gcal_service
from .services.gmail_service import fetch_emails, get_email_details, send_reply
from .llm.llm_service import generate_reply, is_recent_email
from .llm.llm_service import REPLY_SUBJECT_PREFIX



FLASK_PORT = 8501
LOG_FILE = 'logs/email_processor.log'

# Logging Setup
handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3) 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Gmail Authentication Routes
@app.route('/gmail_authenticate')
def gmail_authenticate():
    redirect_uri = url_for('gmail_callback', _external=True)
    authorization_url, error = gmail_service.start_auth_flow(redirect_uri)
    if authorization_url:
        logging.info(f"Redirecting to Gmail authorization URL: {redirect_uri}")
        return redirect(authorization_url)
    else:
        logging.error(f"Gmail authentication failed: {error}")
        return f"Gmail authentication failed: {error}"

@app.route('/gmail_callback')
def gmail_callback():
    try:
        state = request.args.get('state')
        code = request.args.get('code')
        if state is None or code is None:
            logging.error("Gmail authentication failed: Missing state or code.")
            return "Gmail authentication failed: Missing state or code."
        
        creds, error = gmail_service.fetch_token(request.url, state)
        if creds:
            logging.info("Gmail authentication successful.")
            return redirect(url_for('fetch_and_store_gmail'))
        else:
            logging.error(f"Gmail authentication failed: {error}")
            return f"Gmail authentication failed: {error}"
    except Exception as e:
        logging.exception("An unexpected error occurred in /gmail_callback:")
        return "An unexpected error occurred. Please check the logs for details."

# Google Calendar Authentication Routes
@app.route('/gcal_authenticate')
def gcal_authenticate():
    redirect_uri = url_for('gcal_callback', _external=True)
    authorization_url, error = gcal_service.start_auth_flow(redirect_uri)
    if authorization_url:
        return redirect(authorization_url)
    else:
        return f"Google Calendar authentication failed: {error}"

@app.route('/gcal_callback')
def gcal_callback():
    state = request.args.get('state')
    code = request.args.get('code')
    if session.get('gcal_state') != state:
        return "Google Calendar authentication failed: State mismatch"
    creds, error = gcal_service.fetch_token(request.url, state)
    if creds:
        session['gcal_authenticated'] = True
        return redirect(url_for('fetch_and_store_gmail'))
    else:
        return f"Google Calendar authentication failed: {error}"

# Main Processing Route
@app.route('/fetch_and_store_gmail')
def fetch_and_store_gmail():
    service = gmail_service.get_service(gmail_service.load_credentials())
    if not service:
        logging.error("Failed to initialize Gmail service.")
        return "Failed to initialize Gmail service."

    # Fetch emails
    emails = gmail_service.fetch_emails(service)
    if not emails:
        logging.info("No emails found.")
        return "No emails found."

    for email in emails:
        try:
            email_details = gmail_service.get_email_details(service, email['id'])
            if not email_details:
                continue

            # Generate a reply based on the email content
            reply_body = generate_reply(email_details['body'])

            # Send the reply
            gmail_service.send_reply(
                service=service,
                original_message_id=email_details['message_id'],
                recipient=email_details['sender'],
                subject=REPLY_SUBJECT_PREFIX + email_details['subject'],
                reply_body=reply_body,
                thread_id=email_details['thread_id']
            )
        except Exception as e:
            logging.exception(f"An error occurred while processing email ID {email['id']}: {e}")

    logging.info("Emails processed and replies sent.")
    return "Emails processed and replies sent."

# Index Route
@app.route('/')
def index():
    return redirect(url_for('gmail_authenticate'))

def main():
    logging.info("Starting email fetching, storage, and auto-reply process with Google Calendar and Slack integration...")
    email_controller.create_email_table()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(r"C:\Program Files\OpenSSL-Win64\bin\PEM\cert.pem",
                            r"C:\Program Files\OpenSSL-Win64\bin\PEM\privkey.pem")

    app.run(port=FLASK_PORT, ssl_context=context)

if __name__ == '__main__':
    main()
