from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import PyPDF2
import pyttsx3
import uuid
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Initialize database
with app.app_context():
    db.create_all()

# Directories
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    files = db.relationship("UserFile", backref="user", lazy=True)

class UserFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    pdf_filename = db.Column(db.String(100), nullable=False)
    audio_filename = db.Column(db.String(100), nullable=False)
    pdf_path = db.Column(db.String(200), nullable=False)
    audio_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# File handling
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_available_voices(max_voices=5):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        return [(voice.id, voice.name) for voice in voices[:min(max_voices, len(voices))]]
    except Exception as e:
        flash(f"Error loading voices: {str(e)}", "warning")
        return [(None, "Default Voice")]

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    voices = get_available_voices()
    default_speed = 200
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded", "error")
            return render_template("index.html", voices=voices, default_speed=default_speed)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "error")
            return render_template("index.html", voices=voices, default_speed=default_speed)
        if file and allowed_file(file.filename):
            voice_id = request.form.get("voice", None)
            try:
                speed = int(request.form.get("speed", default_speed))
                speed = max(100, min(speed, 300))  # Clamp speed
            except ValueError:
                flash("Invalid speed value. Using default.", "error")
                speed = default_speed
            filename = f"{uuid.uuid4()}_{file.filename}"  # Unique PDF name
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(pdf_path)
            try:
                with open(pdf_path, "rb") as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
                if not text.strip():
                    flash("No text could be extracted from the PDF", "error")
                    return render_template("index.html", voices=voices, default_speed=default_speed)
                unique_id = str(uuid.uuid4())
                audio_filename = f"{unique_id}.wav"
                audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
                try:
                    engine = pyttsx3.init()
                    if voice_id:
                        engine.setProperty("voice", voice_id)
                    engine.setProperty("rate", speed)
                    engine.save_to_file(text, audio_path)
                    engine.runAndWait()
                except Exception as e:
                    flash(f"Error generating audio: {str(e)}", "error")
                    return render_template("index.html", voices=voices, default_speed=default_speed)
                user_file = UserFile(
                    user_id=current_user.id,
                    pdf_filename=filename,
                    audio_filename=audio_filename,
                    pdf_path=pdf_path,
                    audio_path=audio_path
                )
                db.session.add(user_file)
                db.session.commit()
                session["audio_path"] = audio_path
                session["audio_filename"] = file.filename.rsplit(".", 1)[0] + ".wav"
                flash("Audio generated successfully! Click below to download.", "success")
                return render_template("index.html", voices=voices, default_speed=default_speed, audio_ready=True)
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return render_template("index.html", voices=voices, default_speed=default_speed)
        flash("Invalid file type. Please upload a PDF", "error")
    return render_template("index.html", voices=voices, default_speed=default_speed)

@app.route("/download")
@login_required
def download_audio():
    if "audio_path" not in session:
        flash("No audio file available for download", "error")
        return redirect(url_for("index"))
    audio_path = session["audio_path"]
    audio_filename = session["audio_filename"]
    return send_file(audio_path, as_attachment=True, download_name=audio_filename)

@app.route("/download_file/<int:file_id>/<file_type>")
@login_required
def download_file(file_id, file_type):
    user_file = UserFile.query.get_or_404(file_id)
    if user_file.user_id != current_user.id:
        flash("Unauthorized access", "error")
        return redirect(url_for("dashboard"))
    if file_type == "pdf":
        file_path = user_file.pdf_path
        download_name = user_file.pdf_filename
    elif file_type == "audio":
        file_path = user_file.audio_path
        download_name = user_file.audio_filename
    else:
        flash("Invalid file type", "error")
        return redirect(url_for("dashboard"))
    if not os.path.exists(file_path):
        flash("File not found", "error")
        return redirect(url_for("dashboard"))
    return send_file(file_path, as_attachment=True, download_name=download_name)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            flash("Email and password are required", "error")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return render_template("register.html")
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            flash("Email and password are required", "error")
            return render_template("login.html")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode("utf-8"), user.password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("audio_path", None)
    session.pop("audio_filename", None)
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    files = UserFile.query.filter_by(user_id=current_user.id).order_by(UserFile.created_at.desc()).all()
    return render_template("dashboard.html", files=files)

if __name__ == "__main__":
    app.run(debug=True)