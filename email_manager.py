import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from config import load_config

# Set up logging
logger = logging.getLogger(__name__)

def validate_email_config(config):
    """
    Validate email configuration
    
    Args:
        config (dict): Email configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_fields = ['email', 'smtp_server', 'smtp_port', 'smtp_username', 'smtp_password']
    
    for field in required_fields:
        if not config.get(field):
            raise ValueError(f"Email configuration missing required field: {field}")
    
    # Validate email format (basic check)
    email = config['email']
    if '@' not in email or '.' not in email.split('@')[1]:
        raise ValueError(f"Invalid email address format: {email}")
    
    # Validate port
    port = config['smtp_port']
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValueError(f"Invalid SMTP port: {port}")

def create_email_html(news_items):
    """
    Create HTML content for news email
    
    Args:
        news_items (list): List of news items
        
    Returns:
        str: HTML content for email
    """
    if not news_items:
        return """
        <html>
        <body>
            <h2>UPSC Daily News Digest</h2>
            <p>No news items found matching your keywords today.</p>
            <p><em>This email was sent automatically by UPSC News Aggregator</em></p>
        </body>
        </html>
        """
    
    # Group news by source
    sources = {}
    for item in news_items:
        source = item['source']
        if source not in sources:
            sources[source] = []
        sources[source].append(item)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h3 {{ color: #34495e; margin-top: 25px; }}
            .news-item {{ margin: 15px 0; padding: 10px; border-left: 4px solid #3498db; background-color: #f8f9fa; }}
            .news-title {{ font-weight: bold; margin-bottom: 5px; }}
            .news-link {{ color: #2980b9; text-decoration: none; }}
            .news-link:hover {{ text-decoration: underline; }}
            .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #bdc3c7; font-size: 12px; color: #7f8c8d; }}
            .summary {{ background-color: #e8f6f3; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h2>UPSC Daily News Digest</h2>
        <div class="summary">
            <strong>Summary:</strong> Found {len(news_items)} relevant news items from {len(sources)} sources.
        </div>
    """
    
    for source, items in sources.items():
        html += f"""<h3>{source} ({len(items)} items)</h3>"""
        
        for item in items:
            title = item['title']
            link = item.get('link', '')
            
            if link:
                html += f"""
                <div class="news-item">
                    <div class="news-title">
                        <a href="{link}" class="news-link" target="_blank">{title}</a>
                    </div>
                </div>
                """
            else:
                html += f"""
                <div class="news-item">
                    <div class="news-title">{title}</div>
                </div>
                """
    
    html += f"""
        <div class="footer">
            <p><em>This email was sent automatically by UPSC News Aggregator on {datetime.now().strftime('%d %B %Y at %I:%M %p')}</em></p>
            <p>If you no longer wish to receive these emails, please update your settings in the application.</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_news_email(config, news_items):
    """
    Send news digest email
    
    Args:
        config (dict): Email configuration
        news_items (list): List of news items to include
        
    Raises:
        ValueError: If configuration is invalid
        smtplib.SMTPException: If email sending fails
        Exception: For other unexpected errors
    """
    try:
        # Validate configuration
        validate_email_config(config)
        
        logger.info(f"Preparing to send news email with {len(news_items)} items")
        
        # Create email message
        msg = MIMEMultipart('alternative')
        
        # Email headers
        subject = f"Daily UPSC News Digest - {datetime.now().strftime('%d %B %Y')}"
        if not news_items:
            subject += " (No Items)"
            
        msg['Subject'] = subject
        msg['From'] = formataddr(("UPSC News Aggregator", config['smtp_username']))
        msg['To'] = config['email']
        msg['Reply-To'] = config['smtp_username']
        
        # Create HTML content
        html_content = create_email_html(news_items)
        
        # Create plain text version
        text_content = f"""
UPSC Daily News Digest - {datetime.now().strftime('%d %B %Y')}

Found {len(news_items)} relevant news items:

"""
        
        for item in news_items:
            text_content += f"• {item['source']}: {item['title']}\n"
            if item.get('link'):
                text_content += f"  Link: {item['link']}\n"
            text_content += "\n"
        
        text_content += "\nThis email was sent automatically by UPSC News Aggregator"
        
        # Attach both versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        logger.info(f"Connecting to SMTP server {config['smtp_server']}:{config['smtp_port']}")
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            # Enable security
            server.starttls()
            
            # Login
            server.login(config['smtp_username'], config['smtp_password'])
            
            # Send message
            server.send_message(msg)
            
        logger.info(f"News email sent successfully to {config['email']}")
        
    except ValueError as e:
        logger.error(f"Email configuration error: {e}")
        raise
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        raise Exception("Email authentication failed. Please check your username and password.")
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"SMTP recipients refused: {e}")
        raise Exception("Email recipient was refused. Please check the email address.")
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP server disconnected: {e}")
        raise Exception("Connection to email server was lost. Please try again.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        raise Exception(f"Failed to send email: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)
        raise Exception(f"Unexpected error while sending email: {e}")

def test_email_connection(config):
    """
    Test email configuration by connecting to SMTP server
    
    Args:
        config (dict): Email configuration
        
    Returns:
        dict: Test results
    """
    try:
        validate_email_config(config)
        
        logger.info("Testing email connection...")
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=10) as server:
            server.starttls()
            server.login(config['smtp_username'], config['smtp_password'])
            
        return {
            "success": True,
            "message": "Email configuration test successful"
        }
        
    except Exception as e:
        logger.error(f"Email connection test failed: {e}")
        return {
            "success": False,
            "message": f"Email test failed: {e}"
        }