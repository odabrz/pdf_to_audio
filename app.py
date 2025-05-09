from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import os
import PyPDF2
import pyttsx3
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Directories for uploads and audio
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_available_voices(max_voices=5):
    """Retrieve up to 5 available system voices."""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    return [(voice.id, voice.name) for voice in voices[:min(max_voices, len(voices))]]

@app.route("/", methods=["GET", "POST"])
def index():
    voices = get_available_voices()
    if request.method == "POST":
        # Check if a file was uploaded
        if "file" not in request.files:
            flash("No file uploaded", "error")
            return render_template("index.html", voices=voices, default_speed=200)
        file = request.files["file"]
        
        if file.filename == "":
            flash("No file selected", "error")
            return render_template("index.html", voices=voices, default_speed=200)
        
        if file and allowed_file(file.filename):
            # Get form inputs
            voice_id = request.form.get("voice")
            speed = request.form.get("speed", type=float, default=200.0)
            
            # Save the uploaded PDF
            filename = file.filename
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(pdf_path)
            
            # Extract text from PDF
            try:
                with open(pdf_path, "rb") as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted
                
                if not text.strip():
                    flash("No text could be extracted from the PDF", "error")
                    return render_template("index.html", voices=voices, default_speed=200)
                
                # Convert text to speech
                unique_id = str(uuid.uuid4())
                audio_filename = f"{unique_id}.wav"
                audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
                
                engine = pyttsx3.init()
                if voice_id:
                    engine.setProperty('voice', voice_id)
                engine.setProperty('rate', int(speed))
                engine.save_to_file(text, audio_path)
                engine.runAndWait()
                
                # Store audio path in session
                session['audio_path'] = audio_path
                session['audio_filename'] = filename.rsplit(".", 1)[0] + ".wav"
                flash("Audio generated successfully! Click above to download.", "success")
                return render_template("index.html", voices=voices, default_speed=200, audio_ready=True)
            
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return render_template("index.html", voices=voices, default_speed=200)
        
        else:
            flash("Invalid file type. Please upload a PDF", "error")
            return render_template("index.html", voices=voices, default_speed=200)
    
    return render_template("index.html", voices=voices, default_speed=200)

@app.route("/download")
def download_audio():
    if 'audio_path' not in session:
        flash("No audio file available for download", "error")
        return redirect(url_for("index"))
    
    audio_path = session['audio_path']
    audio_filename = session['audio_filename']
    return send_file(audio_path, as_attachment=True, download_name=audio_filename)

if __name__ == "__main__":
    app.run(debug=True)