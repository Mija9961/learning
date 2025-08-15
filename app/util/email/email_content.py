from datetime import datetime

class GetEmailContent:
    @staticmethod
    def get_welcome_email_html(username, activation_link):
        """Generate HTML email content for account activation."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f8fafc; border-radius: 5px; margin: 20px 0; }}
                .button {{ background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; 
                          border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to LearnAnyThingWithAI!</h1>
                </div>
                <div class="content">
                    <p>Dear {username},</p>
                    
                    <p>Thank you for registering with LearnAnyThingWithAI! We're excited to have you join our learning community.</p>
                    
                    <p>To activate your account and start your learning journey, please click the button below:</p>
                    
                    <center>
                        <a style="color: white" href="{activation_link}" class="button">Activate Your Account</a>
                    </center>
                    
                    <p>This activation link will expire in 24 hours for security reasons.</p>
                    
                    <p>If you can't click the button, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; font-size: 0.9em; color: #666;">
                        {activation_link}
                    </p>
                    
                    <p>If you didn't create this account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Best Regards,<br>The LearnAnyThingWithAI Team</p>
                    <small>This is an automated message, please do not reply to this email.</small>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_content(content="Test"):
        """Generate plain text email content."""
        return f"""Hi,
            {content}
            
            Best Regards,
            LearnAnythingWithAI Team
        """

    @staticmethod
    def get_html_content(content="Test"):
        """Generate basic HTML email content."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <p>Hi,</p>
            <p>{content}</p>
            <br>
            <p>Best Regards,</p>
            <p>LearnAnyThingWithAI Team</p>
        </div>
        """

    def get_thanks_email_html():

        # Get the current date and time
        current_datetime = datetime.now()

        # Extract the year from the datetime object
        current_year = current_datetime.year
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; 
                    border: 1px solid #e0e0e0; border-radius: 8px; background-color: #fafafa;">
            <h2 style="color: #333333; text-align: center;">Thank You for Contacting Us</h2>
            <p style="font-size: 16px; color: #555555; line-height: 1.5;">
                We have successfully received your message. Our team will review your request and get back to you 
                as soon as possible.
            </p>
            <p style="font-size: 16px; color: #555555; line-height: 1.5;">
                If you have any urgent concerns, feel free to reply to this email or call our support line.
            </p>
            <hr style="border: none; border-top: 1px solid #dddddd; margin: 20px 0;">
            <p style="font-size: 14px; color: #999999; text-align: center;">
                &copy; {current_year} LearnAnythingWithAI. All rights reserved.
            </p>
        </div>
        """

