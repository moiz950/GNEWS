import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env from the project directory explicitly. On hosts like PythonAnywhere the
# WSGI process runs from a different working directory, so a pathless load_dotenv()
# would silently fail to find the file and the API key would be missing.
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///news.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
    GNEWS_BASE_URL = "https://gnews.io/api/v4"
