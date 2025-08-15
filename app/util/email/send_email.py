import smtplib, asyncio
import dns.resolver
from email_validator import validate_email, EmailNotValidError
import os
from dotenv import load_dotenv
from email.message import EmailMessage
from email.utils import formataddr
from .email_content import GetEmailContent
import asyncio
from functools import wraps
import socket
# Load environment variables from .env file
load_dotenv()


def email_exists(email):
    # Step 1: Validate format
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        print(f"error to check email: {e}")
        return False

    # Step 2: Check MX records
    domain = email.split('@')[1]
    try:
        records = dns.resolver.resolve(domain, 'MX')
    except dns.resolver.NXDOMAIN:
        return False
    except Exception as e:
        print(f"error to check email: {e}")
        return False

    # Step 3: SMTP verification
    mx_record = str(records[0].exchange)
    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mx_record)
        server.helo(server.local_hostname)
        server.mail('test@example.com')
        code, _ = server.rcpt(email)
        server.quit()
        return code == 250
    except Exception as e:
        print(f"error to check email: {e}")
        return False


def check_email_exists_and_send_email(subject, receiver_email, content=None, html_content=None, timeout=10):
    """Check if an email exists by sending a test email via your SMTP configuration."""
    try:
        if not os.environ.get('EMAIL_SEND_ENABLED'):
            print("EMAIL_SEND_ENABLED is not set or is False — skipping check.")
            return True
        email_server = os.environ['EMAIL_SERVER']
        port = int(os.environ['PORT'])
        sender_email = os.environ['SENDER_EMAIL']
        password_email = os.environ['PASSWORD_EMAIL']
        timeout = int(os.environ.get('TIME_OUT', 10))

        content = "This is a test to verify if the email address exists."

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr(("noreply", sender_email))
        msg["To"] = receiver_email
        msg["BCC"] = sender_email
        msg.set_content(content)
        msg.add_alternative(html_content, subtype="html")

        with smtplib.SMTP(email_server, port, timeout=timeout) as server:
            server.starttls()
            server.login(sender_email, password_email)
            # Try sending the email
            response = server.sendmail(sender_email, [receiver_email], msg.as_string())

        # If response is empty dict, email was accepted by SMTP server
        if not response:
            print(f"✅ Email {receiver_email} seems valid (SMTP accepted).")
            return True
        else:
            print(f"❌ Email {receiver_email} rejected: {response}")
            return False

    except smtplib.SMTPRecipientsRefused:
        print(f"❌ Email {receiver_email} was refused by server.")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"SMTP Connection error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        return False
    except socket.gaierror as e:
        print(f"Network error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

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