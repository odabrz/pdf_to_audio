# PDF to Audio Web App 
 
A Flask-based web application that converts PDF files to audio (WAV) using `pyttsx3`. Features include user registration, login, a dashboard to manage uploaded files, and file downloads. The UI uses a gradient theme (#e0eafc to #cfdef3) with purple-blue buttons (#4e54c8). 
 
## Features 
- **User Authentication**: Register and log in securely using Flask-Login and bcrypt. 
- **PDF to Audio Conversion**: Upload PDFs, select voice and speed, and download WAV files. 
- **Dashboard**: View and download converted files. 
- **Responsive UI**: Gradient background and modern design. 
 
## Tech Stack 
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login 
- **Frontend**: HTML, CSS (gradient UI) 
- **Libraries**: PyPDF2, pyttsx3, gTTS, bcrypt 
- **Database**: SQLite (`site.db`) 
 
## Prerequisites 
- Python 3.8+ 
- Virtual environment (recommended) 
- Git 
 
## Setup Instructions 
1. **Clone the Repository**: 
   ```bash 
   git clone https://github.com/odabrz/pdf_to_audio.git 
   cd pdf_to_audio 
   ``` 
2. **Create a Virtual Environment**: 
   ```bash 
   python -m venv venv 
   source venv/bin/activate  # On Windows: venv\Scripts\activate 
   ``` 
3. **Install Dependencies**: 
   ```bash 
   pip install -r requirements.txt 
   ``` 
4. **Set Environment Variable**: 
   ```bash 
   export FLASK_SECRET_KEY="your-secret-key"  # On Windows: set FLASK_SECRET_KEY=your-secret-key 
   ``` 
5. **Initialize the Database**: 
   ```bash 
   python 
   ...     db.create_all() 
   ... 
   ``` 
6. **Run the App**: 
   ```bash 
   python app.py 
   ``` 
   Access at `http://127.0.0.1:5000`. 
 
## Usage 
- **Register**: Create an account at `/register`. 
- **Login**: Log in at `/login`. 
- **Convert PDF**: Upload a PDF, select voice and speed, and download the WAV file. 
- **Dashboard**: View and download your files at `/dashboard`. 
- **Logout**: Log out at `/logout`. 
 
## Deployment 
- **PythonAnywhere**: 
  - Clone the repo, set up a virtual environment, and configure WSGI. 
  - Set `FLASK_SECRET_KEY` in the environment. 
- **Azure**: 
  - Include `pywin32` in `requirements.txt`. 
  - Deploy using Azure App Service or similar. 
 
## Project Structure 
``` 
pdf_to_audio_app/ 
��� app.py              # Main Flask application 
��� requirements.txt    # Dependencies 
��� static/css/styles.css  # CSS for gradient UI 
��� templates/          # HTML templates 
�   ��� index.html      # Home page 
�   ��� register.html   # Registration page 
�   ��� login.html      # Login page 
�   ��� dashboard.html  # User dashboard 
��� uploads/            # Uploaded PDFs (ignored) 
��� audio/              # Generated audio files (ignored) 
��� site.db             # SQLite database (ignored) 
``` 
 
## Contributing 
Fork the repository, make changes, and submit a pull request. 
 
## License 
MIT License 
