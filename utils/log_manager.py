import os
from datetime import datetime

LOG_FILE = 'logs/log.txt'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def add_log_entry(entry):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {entry}\n")

def get_all_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return f.readlines()

