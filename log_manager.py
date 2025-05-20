import datetime
import os
#from firebase_uploader import upload_log_to_firebase

LOG_FILE = 'logs.txt'

def add_log_entry(entry):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {entry}\n"

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    # Also upload log to Firebase
    try:
        upload_log_to_firebase(log_entry)
    except Exception as e:
        print("Firebase upload for log failed:", e)

def get_all_logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        return ["No logs found."]






