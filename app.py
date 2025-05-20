from flask import Flask, render_template, request, redirect, url_for, session, Response, flash
import os, csv, re
from werkzeug.utils import secure_filename
from safety_detector import generate_frames
from progress_analyzer import run_progress_check
from email_sms import send_email
from log_manager import add_log_entry, get_all_logs

import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__, template_folder='dashboard/templates', static_folder='dashboard/static')
app.secret_key = 'your_secret_key'

# --- Cloudinary config ---
cloudinary.config(
    cloud_name = "ddnjv5hbk",
    api_key = "712141175449923",
    api_secret = "UE3riE1mwwzQKUOU6uqqQyKD_Ww",
    secure = True
)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

stream_active = False # Webcam stream status

# ------------------ Helper functions for Cloudinary upload ------------------
def upload_file_to_cloudinary(filepath, folder=None, resource_type="auto"):
    """Uploads a file to Cloudinary and returns the secure URL"""
    try:
        upload_options = {"resource_type": resource_type}
        if folder:
            upload_options["folder"] = folder
        response = cloudinary.uploader.upload(filepath, **upload_options)
        return response.get("secure_url")
    except Exception as e:
        add_log_entry(f"Cloudinary upload error: {str(e)}")
        return None

# ------------------------ HOME ------------------------
@app.route('/home', endpoint='home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home_admin.html') if session.get('role') == 'admin' else render_template('home_user.html')

# ------------------------ LOGIN ------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if role == 'admin' and username == 'admin' and password == 'admin':
            session['user'] = username
            session['role'] = role
            add_log_entry("Admin logged in.")
            return redirect(url_for('admin_dashboard'))

        elif role == 'user' and username == 'user' and password == 'user':
            session['user'] = username
            session['role'] = role
            add_log_entry("User logged in.")
            return redirect(url_for('user_dashboard'))

        else:
            return render_template('login.html', error="❌ Invalid credentials")
    return render_template('login.html')


# ------------------------ DASHBOARDS ------------------------
@app.route('/dashboard/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('dashboard_admin.html')

@app.route('/dashboard/user')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('login'))
    return render_template('dashboard_user.html')


# ------------------------ LOGOUT ------------------------
@app.route('/logout')
def logout():
    add_log_entry(f"{session.get('role')} logged out.")
    session.clear()
    return redirect(url_for('login'))

# ------------------------ SAFETY DETECTION ------------------------
@app.route('/safety')
def safety():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('safety.html', stream=stream_active)

@app.route('/start_webcam', methods=['POST'])
def start_webcam():
    global stream_active
    stream_active = True
    add_log_entry(f"{session.get('role')} started live detection.")
    return redirect(url_for('safety'))

@app.route('/stop_webcam', methods=['POST'])
def stop_webcam():
    global stream_active
    stream_active = False
    add_log_entry(f"{session.get('role')} stopped live detection.")
    return redirect(url_for('safety'))

@app.route('/video_feed')
def video_feed():
    global stream_active
    if stream_active:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Live feed is not active."

# ------------------------ PROGRESS TRACKING ------------------------
@app.route('/progress', methods=['GET', 'POST'])
def progress():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        expected = request.files.get('expected')
        actual = request.files.get('actual')
        video = request.files.get('video')

        if not (expected or actual or video):
            flash("⚠️ Please upload at least one image or video.", "error")
            return render_template('progress.html', result=None, error=True)

        progress_percent = None
        try:
            # Save files locally first
            expected_path, actual_path = None, None
            if expected and actual:
                expected_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(expected.filename))
                actual_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(actual.filename))
                expected.save(expected_path)
                actual.save(actual_path)

                # Run progress check
                progress_percent = run_progress_check(expected_path, actual_path)

                # Upload images to Cloudinary under folder 'progress_images'
                url_expected = upload_file_to_cloudinary(expected_path, folder="progress_images")
                url_actual = upload_file_to_cloudinary(actual_path, folder="progress_images")
                add_log_entry(f"Uploaded expected image to Cloudinary: {url_expected}")
                add_log_entry(f"Uploaded actual image to Cloudinary: {url_actual}")

            if video:
                video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
                video.save(video_path)
                # Upload video to Cloudinary with resource_type='video'
                url_video = upload_file_to_cloudinary(video_path, folder="progress_videos", resource_type="video")
                add_log_entry(f"Uploaded progress video to Cloudinary: {url_video}")

            # Send email notification
            msg = f"Hello Vikas Reddy, today's site progress is {progress_percent if progress_percent is not None else 'N/A'}%. Keep pushing!"
            send_email("reddyvikas73@gmail.com", "Daily Progress Report", msg)

            add_log_entry(f"Progress report sent to client: {progress_percent}%")
            flash("Progress analyzed and notification sent successfully.", "success")
            return render_template('progress.html', result=progress_percent, error=None)

        except Exception as e:
            add_log_entry(f"Error sending progress notification: {str(e)}")
            flash(f"Failed to send notification: {str(e)}", "error")
            return render_template('progress.html', result=progress_percent, error=True)

    return render_template('progress.html', result=None, error=None)

# ------------------------ ADMIN FEATURES ------------------------
@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    clients = []
    file_path = 'clients.csv'

    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        if not re.fullmatch(r'\d{10}', phone):
            flash("Please enter a valid 10-digit mobile number.", "error")
        elif not name:
            flash("Please enter a valid name.", "error")
        else:
            with open(file_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([name, phone])
            add_log_entry(f"Added client: {name}, {phone}")
            flash(f"Client {name} added successfully.", "success")
        return redirect(url_for('manage_users'))

    if os.path.exists(file_path):
        with open(file_path, newline='', encoding='utf-8') as file:
            clients = list(csv.reader(file))

    return render_template('admin/manage_users.html', clients=clients)

@app.route('/delete_user/<phone>', methods=['POST'])
def delete_user(phone):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    file_path = 'clients.csv'
    if os.path.exists(file_path):
        clients = []
        with open(file_path, newline='', encoding='utf-8') as file:
            clients = list(csv.reader(file))
        clients = [client for client in clients if client[1] != phone]
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(clients)
        add_log_entry(f"Deleted client with phone: {phone}")
        flash("Client deleted successfully.", "success")
    return redirect(url_for('manage_users'))

@app.route('/edit_code', methods=['GET', 'POST'])
def edit_code():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    base_dir = os.path.abspath('.')
    files = []
    for root, _, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename.endswith(('.py', '.html', '.txt')):
                rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                files.append(rel_path.replace('\\','/'))

    code = ""
    filename = request.args.get('file')
    if filename:
        filepath = os.path.join(base_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
        else:
            flash("File does not exist.", "error")

    if request.method == 'POST':
        file_to_save = request.form.get('filename')
        new_code = request.form.get('code')
        if file_to_save and new_code is not None:
            filepath = os.path.join(base_dir, file_to_save)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_code)
            add_log_entry(f"File saved: {file_to_save}")
            flash(f"File '{file_to_save}' saved successfully.", "success")
            return redirect(url_for('edit_code', file=file_to_save))

    return render_template('admin/edit_code.html', files=files, code=code, filename=filename)

@app.route('/load_code')
def load_code():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    base_dir = os.path.abspath('.')
    filename = request.args.get('filename')
    if filename:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), 200
        return "File not found", 404
    return "Filename not provided", 400


@app.route("/view_logs")
def view_logs():
    try:
        with open("logs.txt", "r") as f:
            logs = f.readlines()
    except FileNotFoundError:
        logs = ["No logs found."]
    return render_template("admin/view_logs.html", logs=logs)


    # Upload logs.txt to Cloudinary as a raw file under folder 'logs' for backup
    cloud_url = upload_file_to_cloudinary(log_file, folder="logs", resource_type="raw")
    if cloud_url:
        add_log_entry(f"Logs file uploaded to Cloudinary: {cloud_url}")

    return render_template('admin/view_logs.html',)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


