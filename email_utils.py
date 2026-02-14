import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_reset_email(to_email: str, reset_link: str):
    try:
        message = Mail(
            from_email="tushnik.tech@finigenie.co.in",  # MUST match verified sender
            to_emails=to_email,
            subject="Reset Your Rajneeti Password",
            html_content=f"""
            <h3>Password Reset</h3>
            <p>Click below to reset your password:</p>
            <a href="{reset_link}">{reset_link}</a>
            """
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print("Email status:", response.status_code)

    except Exception as e:
        print("Email error:", str(e))
