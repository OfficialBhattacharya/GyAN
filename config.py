import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "email": "",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "",
    "smtp_password": "",
    "send_time": "07:00",
    "sources": ["thehindu", "pib", "indianexpress"],
    "keywords": [
        "UPSC", "IAS", "IPS", "IFS", "civil services", "government", "policy", "governance",
        "economy", "economic", "GDP", "inflation", "budget", "finance", "banking",
        "environment", "climate", "pollution", "conservation", "biodiversity",
        "international relations", "diplomacy", "foreign policy", "trade",
        "science", "technology", "innovation", "research", "space",
        "security", "defence", "military", "terrorism", "cyber",
        "education", "health", "welfare", "social", "poverty",
        "constitution", "supreme court", "parliament", "election",
        "agriculture", "farmer", "rural", "infrastructure", "transport"
    ]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)