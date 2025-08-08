import smtplib, asyncio
import os
from dotenv import load_dotenv
from email.message import EmailMessage
from email.utils import formataddr
from .email_content import GetEmailContent
import asyncio
from functools import wraps
# Load environment variables from .env file
load_dotenv()


async def send_email(subject, receiver_email, content=None, html_content=None, timeout=10):
    try:
        if os.environ['EMAIL_SEND_ENABLED']:
            # Create the base text message.
            email_server = os.environ['EMAIL_SERVER']
            port = os.environ['PORT']
            sender_email = os.environ['SENDER_EMAIL']
            password_email = os.environ['PASSWORD_EMAIL']
            timeout = int(os.environ['TIME_OUT'])
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = formataddr(("noreply", f"{sender_email}"))
            msg["To"] = receiver_email
            msg["BCC"] = sender_email            

            msg.set_content(
                f"""\
                {content}
                """
            )

            msg.add_alternative(
                f"""\
            <html>
            <body>
                {html_content}
            </body>
            </html>
            """,
                subtype="html",
            )

            with smtplib.SMTP(email_server, port, timeout=timeout) as server:
                server.starttls()
                server.login(sender_email, password_email)
                server.sendmail(sender_email, receiver_email, msg.as_string())
    except smtplib.SMTPConnectError as e:
        print(f"Error faced to connect to the SMTP server: {e}")
    except smtplib.SMTPException as e:
        print(f"Error for SMTP : {e}")
    except Exception as e:
        print(f"Error sending email: {e}")



def sync_send_email(subject, receiver_email, html_content=None, content=None):
    """Synchronous wrapper for send_email"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(send_email(subject=subject, receiver_email=receiver_email, html_content=html_content))
    finally:
        loop.close()