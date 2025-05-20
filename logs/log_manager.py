import threading
from datetime import datetime
import os

LOG_FILE =r"C:/Users/dhanu/OneDrive/Desktop/construction_project/logs.txt"
_lock = threading.Lock()

def add_log_entry(message: str):
    """Append a timestamped log entry to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    #check whether the path exists or not 
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with _lock:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line)

def get_all_logs():
    """Read all log entries from log file and return as a list of lines."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return f.readlines()







