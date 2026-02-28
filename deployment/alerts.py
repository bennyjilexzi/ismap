import requests
import smtplib
from email.mime.text import MIMEText

def send_slack_alert(message, webhook_url):
    if not webhook_url:
        return
    try:
        payload = {'text': message}
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Slack alert failed: {e}")

def send_telegram_alert(message, bot_token, chat_id):
    if not bot_token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {'chat_id': chat_id, 'text': message}
        requests.post(url, json=data)
    except Exception as e:
        print(f"Telegram alert failed: {e}")

def send_email_alert(subject, body, smtp_server, smtp_port, sender, password, recipient):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
    except Exception as e:
        print(f"Email alert failed: {e}")

def send_alert(change_type, subdomain, domain, alert_config):
    import datetime
    message = f"ISMAP Alert: {change_type}\n\nDomain: {domain}\nSubdomain: {subdomain}\nTime: {datetime.datetime.now()}"
    
    if alert_config.get('slack_webhook'):
        send_slack_alert(message, alert_config['slack_webhook'])
    if alert_config.get('telegram_bot_token') and alert_config.get('telegram_chat_id'):
        send_telegram_alert(message, alert_config['telegram_bot_token'], alert_config['telegram_chat_id'])
    if alert_config.get('email'):
        send_email_alert(f"ISMAP Alert: {change_type}", message, 
                         alert_config.get('smtp_server', 'smtp.gmail.com'),
                         alert_config.get('smtp_port', 587),
                         alert_config.get('email'),
                         alert_config.get('email_password'),
                         alert_config['email'])
