from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import PyPDF2
import pyttsx3
from gtts import gTTS
import uuid
import bcrypt
from datetime import datetime
from io import BytesIO
from pydub import AudioSegment  # For converting MP3 to WAV

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

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

# Text-to-speech function
def text_to_speech(text, audio_path, voice_index=0, speed=200, use_gtts=True):
    try:
        if use_gtts and os.getenv("RENDER", "false") == "true":  # Use gTTS on Render
            tts = gTTS(text=text, lang="en")
            mp3_path = audio_path.replace(".wav", ".mp3")
            tts.save(mp3_path)
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(audio_path, format="wav")
            os.remove(mp3_path)
        else:  # Use pyttsx3 locally
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.setProperty("voice", voices[voice_index].id)
            engine.setProperty("rate", speed)
            engine.save_to_file(text, audio_path)
            engine.runAndWait()
    except Exception as e:
        print(f"Text-to-speech error: {e}")
        raise

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Please log in to convert files.", "error")
            return redirect(url_for("login"))
        file = request.files.get("file")
        voice_index = int(request.form.get("voice", 0))
        speed = int(request.form.get("speed", 200))
        if file and file.filename.endswith(".pdf"):
            pdf_filename = f"{uuid.uuid4()}_{file.filename}"
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_filename)
            file.save(pdf_path)
            # Extract text
            with open(pdf_path, "rb") as f:
                pdf = PyPDF2.PdfReader(f)
                text = "".join(page.extract_text() for page in pdf.pages if page.extract_text())
            if not text:
                flash("No text found in PDF.", "error")
                return redirect(url_for("index"))
            # Convert to audio
            audio_filename = f"{uuid.uuid4()}.wav"
            audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
            text_to_speech(text, audio_path, voice_index, speed, use_gtts=True)
            # Save to database
            user_file = UserFile(
                user_id=current_user.id,
                pdf_filename=pdf_filename,
                audio_filename=audio_filename,
                pdf_path=pdf_path,
                audio_path=audio_path
            )
            db.session.add(user_file)
            db.session.commit()
            return send_file(audio_path, as_attachment=True, download_name=audio_filename)
        flash("Invalid file format. Please upload a PDF.", "error")
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode("utf-8"), user.password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    files = UserFile.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", files=files)

@app.route("/download/<int:file_id>")
@login_required
def download(file_id):
    user_file = UserFile.query.get_or_404(file_id)
    if user_file.user_id != current_user.id:
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard"))
    return send_file(user_file.audio_path, as_attachment=True, download_name=user_file.audio_filename)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)