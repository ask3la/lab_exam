import os

SECRET_KEY = 'exam-secret-key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///library.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'covers')
MAX_CONTENT_LENGTH = 8 * 1024 * 1024
