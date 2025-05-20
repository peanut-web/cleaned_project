import smtplib
from email.message import EmailMessage

# Replace these with your Gmail app credentials
EMAIL_ADDRESS = "reddyvikas73@gmail.com"
EMAIL_APP_PASSWORD = "akdv bhsz stki sxah"#uqexsxbmrwvtthie" # App password generated from Gmail
receiver_email="reddyvikas73@gmail.com"
def send_email(receiver_email,subject, message_body):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = receiver_email
        msg.set_content(message_body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)

        print("Email sent successfully.")
        return True

    except Exception as e:
        print("Failed to send email:", str(e))
        return False    
