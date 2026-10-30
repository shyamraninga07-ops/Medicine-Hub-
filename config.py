import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'medicare-hub-secret-key-super-secure-2026-prod-alpha')
    
    # Database
    DB_DIR = os.path.join(BASE_DIR, 'database')
    os.makedirs(DB_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{os.path.join(DB_DIR, "medicare.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PRESCRIPTIONS_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'prescriptions')
    AVATARS_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
    os.makedirs(PRESCRIPTIONS_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(AVATARS_UPLOAD_FOLDER, exist_ok=True)
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days
    
    # Application Defaults
    DEFAULT_REFILL_THRESHOLD_DAYS = 5
    DEFAULT_REFILL_THRESHOLD_UNITS = 5

