import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    filename="smtp_log.txt",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def send_email():
    try:
        # SMTP server details (example: Gmail)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "sprakashsmartian@gmail.com"
        sender_password = "apir tnaw ulak gonj"  # APP password
        recipient_email = "prakash.shu2005@gmail.com"

        # Create email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = "Test Email - assignment 2 test of smtp"
        body = "This is a test email sent via Python SMTP to check the server connections building u can delete it."
        message.attach(MIMEText(body, "plain"))

        # Connect to server
        logging.info("Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        logging.info("Connection secured with TLS.")

        # Login
        server.login(sender_email, sender_password)
        logging.info("Logged in successfully.")

        # Send email
        server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info(f"Email sent successfully to {recipient_email}")
        
        server.quit()
        logging.info("Connection closed.")

    except Exception as e:
        logging.error(f"Error: {e}")
        print("Something went wrong, check smtp_log.txt for details.")

if __name__ == "__main__":
    send_email()
