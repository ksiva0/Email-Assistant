
# Email Assistant 📧🤖

**Email Assistant** is a Python-based application designed to automate email management, integrate with Google Calendar, and send notifications via Slack. It fetches emails, generates intelligent replies, schedules meetings, and keeps you updated in real-time.

---

## Features 🌟
- **Automated Email Replies**: Dynamically generates replies based on email content using AI.
- **Gmail Integration**: Fetches and processes emails directly from your Gmail inbox.
- **Google Calendar Support**: Schedules meetings based on email content.
- **Slack Notifications**: Sends real-time updates to Slack channels for important events.
- **Secure Communication**: Uses OAuth2 for secure authentication with Google APIs.

---

## Prerequisites 🛠️
1. **Python**: Install Python 3.9 or higher.
2. **Google Cloud Credentials**:
   - Create credentials for Gmail and Google Calendar APIs in the [Google Cloud Console](https://console.cloud.google.com/).
   - Download the credentials JSON files and save them as:
     - credentials_gmail.json
     - credentials_gcal.json
3. **Slack Bot Token**:
   - Create a Slack app and generate a bot token.
   - Set the `SLACK_BOT_TOKEN` environment variable.

---

## Installation 🚀

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/email-assistant.git
cd email-assistant
```

### 2. Set Up a Virtual Environment
```bash
python -m venv myenv
myenv\Scripts\activate  # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory and add the following:
```
SLACK_BOT_TOKEN=your-slack-bot-token
```

---

## Usage 🖥️

### 1. Start the Application
Run the following command to start the Flask application:
```bash
python -m src.main
```

### 2. Authenticate with Gmail
- Open your browser and navigate to `https://localhost/`.
- Follow the prompts to authenticate with Gmail.

### 3. Authenticate with Google Calendar
- Navigate to `https://localhost/gcal_authenticate`.
- Follow the prompts to authenticate with Google Calendar.

### 4. View Logs
Logs are stored in email_processor.log. You can monitor the logs for email processing and error details.

---

## Key Files 📄

### 1. main.py
- Entry point for the application.
- Handles Flask routes for Gmail and Google Calendar authentication.

### 2. gmail_service.py
- Manages Gmail API integration for fetching and sending emails.

### 3. gcal_service.py
- Handles Google Calendar API integration for scheduling meetings.

### 4. slack_service.py
- Sends notifications to Slack channels.

### 5. llm_service.py
- Generates intelligent email replies using AI.

---

## Deployment 🌐

### Running Locally
1. Activate your virtual environment:
   ```bash
   myenv\Scripts\activate  # On Windows
   # OR
   source myenv/bin/activate  # On macOS/Linux
   ```
2. Start the Flask application:
   ```bash
   python -m src.main
   ```
3. Open your browser and navigate to `https://localhost/`.

---

## Contributing 🤝
Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

---

## License 📜
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgments 🙌
- [Google APIs](https://developers.google.com/)
- [Slack SDK](https://slack.dev/python-slack-sdk/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)

---

Let me know if you need further assistance!
