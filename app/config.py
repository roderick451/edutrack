import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_database_url():
    uri = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if uri:
        return uri.replace("\\", "/")
    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    return "sqlite:///" + str((instance_dir / "edutrack.db").resolve()).replace("\\", "/")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
