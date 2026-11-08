import requests
import json
from django.conf import settings
from .models import Notification

def send_telegram_notification(message, user_id=None):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    
    if not token or not chat_id:
        return None
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Telegram notification error: {e}")
        return None

def create_site_notification(title, message):
    Notification.objects.create(title=title, message=message)
