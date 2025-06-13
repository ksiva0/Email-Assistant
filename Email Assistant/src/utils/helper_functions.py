# src/utils/helper_functions.py
import base64
import logging

def is_automated_email(headers, sender):
    """
    Checks if an email is automated based on headers and sender.
    """
    header_values = {header['name'].lower(): header['value'] for header in headers}
    return ("auto-submitted" in header_values or
            "x-autoreply" in header_values or
            ("precedence" in header_values and "bulk" in header_values["precedence"].lower()) or
            "list-unsubscribe" in header_values or
            "noreply@" in sender or
            "mailer-daemon@" in sender)

def decode_base64(data):
    """
    Decodes a base64 URL safe string.
    """
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        except Exception as e:
            logging.warning(f"Error decoding base64: {e}")
            return ""
    return ""
