import sqlite3
import logging
from flask import redirect, url_for
import sys
import os
from src.services import gmail_service, gcal_service
from src.llm import llm_service
from src.tools import calendar_tool

# create a database
DATABASE_NAME = 'emails.db'

def create_email_table():
    """Creates the email table in the database if it doesn't exist."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                thread_id TEXT,
                sender TEXT,
                recipient TEXT,
                subject TEXT,
                timestamp INTEGER,
                body TEXT,
                has_attachment BOOLEAN DEFAULT 0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_message_id ON emails (message_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_thread_id ON emails (thread_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_timestamp ON emails (timestamp);")
        conn.commit()
        logging.info(f"Database '{DATABASE_NAME}' checked/created successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error creating/checking database table: {e}")
    finally:
        if conn:
            conn.close()

def store_email(email_data):
    """Stores email data in the database."""
    if not email_data or not email_data.get('message_id'):
        logging.warning("Skipping storing email: Invalid email data provided.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO emails (message_id, thread_id, sender, recipient, subject, timestamp, body, has_attachment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email_data['message_id'],
                email_data.get('thread_id'),
                email_data.get('sender'),
                email_data.get('recipient'),
                email_data.get('subject'),
                email_data.get('timestamp'),
                email_data.get('body'),
                1 if email_data.get('has_attachment') else 0,
            ),
        )
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Stored email with Message ID: '{email_data['message_id']}'")
        else:
            logging.info(f"Email with Message ID: '{email_data['message_id']}' already exists or failed to insert.")

    except sqlite3.Error as e:
        logging.error(f"Error storing email with Message ID '{email_data['message_id']}': {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logging.exception(
            f"An unexpected error occurred during storing email with Message ID '{email_data['message_id']}': {e}"
        )
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def fetch_and_process_emails():
    """Fetches emails, stores them, generates replies, and integrates tools."""
    creds_gmail = gmail_service.load_credentials()
    creds_gcal = gcal_service.load_credentials()

    if not creds_gmail or not creds_gmail.valid:
        return redirect(url_for('gmail_authenticate'))

    gmail_srv = gmail_service.get_service(creds_gmail)
    if not gmail_srv:
        return "Failed to initialize Gmail service."

    messages = gmail_service.fetch_emails(gmail_srv)
    if messages:
        for message in messages:
            email_details = gmail_service.get_email_details(gmail_srv, message['id'])
            if email_details:
                logging.info(f"Processing Gmail: {email_details['subject']}, from: {email_details['sender']}")
                store_email(email_details)
                reply_message = llm_service.generate_reply(email_details['body'])
                if reply_message:
                    logging.info(f"Sending reply to: {email_details['sender']}, message_id: {email_details['message_id']}, thread_id: {email_details['thread_id']}")
                    gmail_service.send_reply(
                        gmail_srv, email_details['message_id'], email_details['sender'],
                        f"{llm_service.REPLY_SUBJECT_PREFIX}{email_details['subject']}", reply_message,
                        email_details['thread_id']
                    )

                # Schedule meeting and notify on Slack if certain keywords are present
                if "schedule meeting" in email_details['body'].lower():
                    calendar_tool.schedule_meeting_and_notify(email_details, creds_gcal)

            else:
                logging.warning(f"email_details is None for Gmail message ID: {message['id']}")
        return "Fetched, stored, and processed replies for Gmail emails."
    else:
        return "No new Gmail emails to fetch."
