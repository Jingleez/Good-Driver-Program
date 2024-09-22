import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    DB_HOST = os.getenv('DB_HOST', 'team13-rds.cobd8enwsupz.us-east-1.rds.amazonaws.com')
    DB_USER = os.getenv('DB_USER', 'admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Cpsc4910_Team13!Rds')
    DB_NAME = os.getenv('DB_NAME', 'Team13_database')
