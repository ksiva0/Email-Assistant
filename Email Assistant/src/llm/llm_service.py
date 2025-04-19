import logging
import logging

REPLY_SUBJECT_PREFIX = "Re: "
REPLY_SIGNATURE = "Best regards,\nYour Assistant"

def generate_reply(email_body):
    """
    Generates a reply based on the email content.
    """
    email_lower = email_body.lower()

    # Specific cases for common email topics
    if "hello" in email_lower or "hi" in email_lower:
        return "Hello! How can I assist you today?" + f"\n\n{REPLY_SIGNATURE}"
    elif "how are you" in email_lower or "health" in email_lower:
        return "I'm doing well, thank you for asking. How are you?" + f"\n\n{REPLY_SIGNATURE}"
    elif "congratulations" in email_lower and "internship" in email_lower:
        return "Thank you for the opportunity! I'm excited to continue my internship." + f"\n\n{REPLY_SIGNATURE}"
    elif "task" in email_lower and "assigned" in email_lower:
        return "I have received the task assignment. I will review it and provide updates soon." + f"\n\n{REPLY_SIGNATURE}"
    elif "urgent" in email_lower:
        return "Thank you for marking this as urgent. I will prioritize it and get back to you shortly." + f"\n\n{REPLY_SIGNATURE}"
    elif "meeting" in email_lower or "schedule" in email_lower:
        return "Thank you for your meeting request. I will review my schedule and get back to you with availability." + f"\n\n{REPLY_SIGNATURE}"
    elif "thank you" in email_lower or "thanks" in email_lower:
        return "You're welcome! Let me know if there's anything else I can assist you with." + f"\n\n{REPLY_SIGNATURE}"
    elif "follow up" in email_lower:
        return "Thank you for following up. I will review the details and respond shortly." + f"\n\n{REPLY_SIGNATURE}"
    elif "help" in email_lower or "support" in email_lower:
        return "Thank you for reaching out. Please let me know how I can assist you further." + f"\n\n{REPLY_SIGNATURE}"
    elif "deadline" in email_lower:
        return "Thank you for the update on the deadline. I will ensure to meet it on time." + f"\n\n{REPLY_SIGNATURE}"

    # Fallback response for unrecognized content
    logging.warning(f"Unrecognized email content: {email_body}")
    return "Thank you for your email. I will review it and get back to you soon." + f"\n\n{REPLY_SIGNATURE}"
