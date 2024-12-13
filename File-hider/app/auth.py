import re
import pyotp
import smtplib
from email.mime.text import MIMEText
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from db import User

from config import Config



# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password):
        return pwd_context.hash(password)
    
    @staticmethod
    def validate_email(email):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
    
    @staticmethod
    def send_verification_email(email, verification_code):
        try:
            msg = MIMEText(f'Your verification code is: {verification_code}')
            msg['Subject'] = 'File Hider - Email Verification'
            msg['From'] = Config.SMTP_USERNAME
            msg['To'] = email
            
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    
    @staticmethod
    def generate_verification_code():
        return pyotp.random_base32()[:6]  # 6-digit code