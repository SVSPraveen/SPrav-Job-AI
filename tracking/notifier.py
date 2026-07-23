import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_email_notification(job_title: str, company: str, job_url: str, pdf_path: str):
    """
    Sends an email to the user with the tailored resume attached and the job link,
    so the user can manually apply to complex portals directly from their phone.
    """
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    if not sender or not password or not receiver:
        print(f"[Notifier] Email credentials not found in .env. Skipping notification for {company}.")
        return False

    msg = EmailMessage()
    msg['Subject'] = f"Action Required: Apply to {job_title} at {company}"
    msg['From'] = sender
    msg['To'] = receiver

    body = f"""
AutoJob AI has prepared a highly tailored, 90+ ATS-scoring resume for a job that requires manual interaction.

Company: {company}
Title: {job_title}
Apply Link: {job_url}

Please find your custom resume attached. Download it and apply using the link above!
    """
    msg.set_content(body)

    # Attach the custom PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
            msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(pdf_path))
    else:
        print(f"[Notifier] Warning: PDF not found at {pdf_path}")

    try:
        # Assuming Gmail SMTP. Adjust if using another provider.
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print(f"[Notifier] Successfully sent email for {company} to {receiver}.")
        return True
    except Exception as e:
        print(f"[Notifier] Failed to send email: {e}")
        return False
