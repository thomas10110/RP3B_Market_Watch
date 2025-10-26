import smtplib
from email.mime.text import MIMEText
import config

def send_email(to_email, subject, body):
    """Sends an email using the configured SMTP settings."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config.SENDER_EMAIL
    msg['To'] = to_email

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, [to_email], msg.as_string())
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_admin_notification(subject, body):
    """Sends a notification email to the admin."""
    send_email(config.ADMIN_EMAIL, subject, body)
