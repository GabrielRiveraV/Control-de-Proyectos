import os

from dotenv import load_dotenv


# CARGAR VARIABLES .env
load_dotenv()


class Config:

    # =========================
    # FLASK
    # =========================

    SECRET_KEY = os.getenv('SECRET_KEY')


    # =========================
    # MYSQL
    # =========================

    DB_HOST = os.getenv('DB_HOST')

    DB_USER = os.getenv('DB_USER')

    DB_PASSWORD = os.getenv('DB_PASSWORD')

    DB_NAME = os.getenv('DB_NAME')


    # =========================
    # UPLOADS
    # =========================

    UPLOAD_FOLDER = 'static/uploads/actas'

    UPLOAD_FOLDER_ACTAS = 'static/uploads/actas'

    UPLOAD_FOLDER_CONTRATOS = 'static/uploads/contratos'

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024


    # =========================
    # EXTENSIONES PERMITIDAS
    # =========================

    ALLOWED_EXTENSIONS = {
        'pdf',
        'xlsx',
        'xls'
    }
