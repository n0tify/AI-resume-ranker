import os
import uuid
import logging
import io
import csv
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from nlp_engine import ResumeAnalyzer
from dotenv import load_dotenv

# SECURITY PROTOCOL: Load the hidden environment variables from the .env vault
# This ensures that no passwords or secret keys are hardcoded into the script.
load_dotenv()

# Initialize Enterprise Flask Application
app = Flask(__name__)

# Fetch the secret key from the vault. If not found, use a fallback for local testing.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_local_development_key_only")

# Security & Directory Configuration
UPLOAD_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_MIME_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_DIRECTORY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# Administrator Configuration: Fetching credentials securely from the .env vault
ADMIN_EMAIL_TARGET = os.environ.get("ADMIN_EMAIL")
SMTP_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

# Initialize NLP Engine globally
ai_engine = ResumeAnalyzer()
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

def validate_file_extension(filename: str) -> bool:
    """Ensures uploaded files contain valid extensions to prevent malicious payloads."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_MIME_EXTENSIONS

@app.after_request
def apply_security_headers(response):
    """Injects strict HTTP security headers into every server response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.errorhandler(404)
def resource_not_found(e):
    """Handles invalid route access."""
    return render_template('index.html', rankings=None, error="404: Resource Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handles catastrophic backend failures gracefully."""
    return render_template('index.html', rankings=None, error="500: Internal Server Error"), 500

@app.errorhandler(RequestEntityTooLarge)
def handle_large_payload(e):
    """Intercepts files exceeding the 16MB limit."""
    flash("Payload Error: Uploaded files exceed the 16MB memory limit.", "danger")
    return redirect(url_for('dashboard'))

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    """
    Main application route. Handles the rendering of the Synapse UI and processes
    the multipart form data containing the Job Description and PDF files.
    """
    if request.method == 'POST':
        raw_job_description = request.form.get('job_description', '').strip()
        uploaded_dossiers = request.files.getlist('resumes')

        if not raw_job_description:
            flash("Validation Error: Target Vector (Job Description) cannot be empty.", "danger")
            return redirect(request.url)

        if not uploaded_dossiers or uploaded_dossiers[0].filename == '':
            flash("Validation Error: Please upload at least one valid PDF dossier.", "danger")
            return redirect(request.url)

        secured_file_paths = []
        original_file_names = []
        active_session_token = str(uuid.uuid4())[:12] 
        
        for uploaded_file in uploaded_dossiers:
            if uploaded_file and validate_file_extension(uploaded_file.filename):
                sanitized_name = secure_filename(uploaded_file.filename)
                unique_identifier = f"{active_session_token}_{sanitized_name}"
                absolute_storage_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_identifier)
                
                uploaded_file.save(absolute_storage_path)
                secured_file_paths.append(absolute_storage_path)
                original_file_names.append(sanitized_name)
            else:
                flash(f"Warning: File {uploaded_file.filename} was rejected. Only PDFs are supported.", "warning")

        if not secured_file_paths:
            return redirect(request.url)

        try:
            calculated_rankings = ai_engine.evaluate_candidates(raw_job_description, secured_file_paths, original_file_names)
            
            memory_proxy = io.StringIO()
            csv_writer = csv.DictWriter(memory_proxy, fieldnames=["Candidate Name", "Source File", "Match Score", "Missing Keywords"])
            csv_writer.writeheader()
            
            for rank_data in calculated_rankings:
                row_copy = rank_data.copy()
                row_copy['Missing Keywords'] = ", ".join(row_copy['Missing Keywords'])
                csv_writer.writerow(row_copy)
            
            app.config[f'volatile_csv_{active_session_token}'] = memory_proxy.getvalue()
            
            return render_template('index.html', rankings=calculated_rankings, job_description=raw_job_description, session_id=active_session_token)
            
        except Exception as system_exception:
            logging.error(f"Processing Exception: {str(system_exception)}")
            flash("System Failure: The NLP engine encountered a critical error.", "danger")
            return render_template('index.html', rankings=None)

        finally:
            for path in secured_file_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Security Wipe: Deleted {path}")
                    except Exception as deletion_error:
                        logging.error(f"Failed to wipe file {path}: {deletion_error}")

    return render_template('index.html', rankings=None)

@app.route('/download/<session_id>')
def download_csv(session_id):
    """
    Retrieves the generated telemetry report from the application's active RAM,
    transmits it to the user's browser as a downloadable file, and instantly
    destroys the memory sector to ensure Zero-Trace privacy compliance.
    """
    volatile_data = app.config.get(f'volatile_csv_{session_id}')
    
    if not volatile_data:
        flash("Security Protocol: Download link has expired or data was wiped.", "danger")
        return redirect(url_for('dashboard'))
    
    byte_stream = io.BytesIO(volatile_data.encode('utf-8'))
    app.config.pop(f'volatile_csv_{session_id}', None) 
    logging.info(f"Session {session_id} CSV data successfully purged from memory.")

    return send_file(
        byte_stream, 
        mimetype='text/csv', 
        download_name=f'Synapse_Telemetry_{session_id}.csv', 
        as_attachment=True
    )

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    Parses incoming JSON feedback data and routes it through an encrypted 
    SMTP SSL connection directly to the administrator's email inbox.
    """
    request_data = request.json
    user_stars = request_data.get('stars')
    user_feedback = request_data.get('feedback', 'No description provided.')

    if not ADMIN_EMAIL_TARGET or not SMTP_APP_PASSWORD:
        logging.error("CRITICAL: Email credentials missing from environment variables.")
        return jsonify({"status": "server_error", "message": "Server email not configured"}), 500

    try:
        email_envelope = EmailMessage()
        email_envelope['Subject'] = f"Synapse Alert: New {user_stars}-Star Rating Received"
        email_envelope['From'] = ADMIN_EMAIL_TARGET
        email_envelope['To'] = ADMIN_EMAIL_TARGET
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #ffffff; padding: 20px; border-radius: 10px;">
                <h2 style="color: #00c6ff;">Synapse Dashboard Feedback</h2>
                <p><strong>Rating:</strong> <span style="color: #fcd34d; font-size: 1.5em;">{'★' * int(user_stars)}</span> ({user_stars}/5)</p>
                <div style="background-color: #1e293b; padding: 15px; border-left: 4px solid #00c6ff; margin-top: 20px;">
                    <p style="margin: 0; color: #e2e8f0;">{user_feedback}</p>
                </div>
            </body>
        </html>
        """
        email_envelope.add_alternative(html_body, subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(ADMIN_EMAIL_TARGET, SMTP_APP_PASSWORD)
            smtp_server.send_message(email_envelope)

        logging.info("Feedback transmission successful.")
        return jsonify({"status": "success", "code": 200})
        
    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP Auth Failed. Ensure App Passwords are configured correctly.")
        return jsonify({"status": "auth_error", "message": "Email configuration invalid"}), 401
    except Exception as general_error:
        logging.error(f"Feedback transmission failure: {general_error}")
        return jsonify({"status": "server_error"}), 500

if __name__ == '__main__':
    logging.info("Booting Synapse Local Development Server on Port 5000")
    app.run(debug=True, host='127.0.0.1', port=5000)