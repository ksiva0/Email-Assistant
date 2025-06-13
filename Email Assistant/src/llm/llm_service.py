# src/llm/llm_service.py

import logging
from transformers import pipeline, AutoTokenizer
import datetime
import pytz

REPLY_SUBJECT_PREFIX = "Re: "
REPLY_SIGNATURE = "Best regards,\nYour Assistant"

MODEL_NAME = 'google/flan-t5-base'

# Initialize the pipeline for text2text generation (Flan-T5 is encoder-decoder)
try:
    generator = pipeline("text2text-generation", model=MODEL_NAME)
    tokenizer = generator.tokenizer
    logging.info(f"Successfully loaded the '{MODEL_NAME}' model from Hugging Face.")
except Exception as e:
    generator = None
    tokenizer = None
    logging.error(f"Error loading the '{MODEL_NAME}' model: {e}")
    logging.warning("Falling back to basic keyword-based replies.")

def generate_reply(email_body):
    """
    Generates a reply based on the email content using a Hugging Face Transformer model
    with a prompt tailored for understanding the email's intent. Falls back to basic
    keyword replies if the model fails to load.
    """
    if generator:
        try:
            prompt = f"""You are a helpful email assistant. Reply politely and professionally to the following email:

Email:
{email_body}
"""

            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

            response = generator(prompt, max_new_tokens=50, do_sample=True)

            reply_content = response[0]['generated_text'].strip()
            return reply_content + f"\n\n{REPLY_SIGNATURE}"
        except Exception as e:
            logging.error(f"Error generating reply with '{MODEL_NAME}': {e}")
            return _generate_keyword_reply(email_body)  # fallback
    else:
        return _generate_keyword_reply(email_body)

def _generate_keyword_reply(email_body):
    email_lower = email_body.lower()
    if "job application" in email_lower or ("resume" in email_lower and "position" in email_lower):
        return "Thank you for your application. We will review it carefully and be in touch if your qualifications match our requirements." + f"\n\n{REPLY_SIGNATURE}"
    elif "hello" in email_lower or "hi" in email_lower:
        return "Hello! How can I assist you today?" + f"\n\n{REPLY_SIGNATURE}"
    elif "how are you" in email_lower or "health" in email_lower:
        return "I'm doing well, thank you for asking. How are you?" + f"\n\n{REPLY_SIGNATURE}"
    else:
        logging.warning(f"Unrecognized email content (keyword fallback): {email_body}")
        return "Thank you for your email. I will review it and get back to you soon." + f"\n\n{REPLY_SIGNATURE}"

def is_recent_email(email_date_str):
    """
    Checks if an email is recent (within the last 1 day).
    """
    try:
        email_date = datetime.datetime.strptime(email_date_str, "%A, %d %B %Y %H:%M %Z")
        email_date_ist = email_date.astimezone(pytz.timezone('Asia/Kolkata'))
        now_ist = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        return (now_ist - email_date_ist) <= datetime.timedelta(days=1)
    except ValueError as e:
        logging.error(f"Error parsing date string: {email_date_str}. Error: {e}")
        return False
