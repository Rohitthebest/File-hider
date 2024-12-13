import re
import pyotp
import smtplib
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from config import Config
from auth import User, AuthManager

class EmailVerificationService:
    @staticmethod
    def generate_verification_code() -> str:
        """
        Generate a secure 6-digit verification code
        
        Returns:
            str: 6-digit verification code
        """
        # Use pyotp to generate a secure, time-based code
        totp = pyotp.TOTP(pyotp.random_base32())
        return totp.now()

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email (str): Email address to validate
        
        Returns:
            bool: True if email is valid, False otherwise
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @staticmethod
    def send_verification_email(
        email: str, 
        verification_code: str, 
        username: str = None
    ) -> bool:
        """
        Send verification email with OTP
        
        Args:
            email (str): Recipient email address
            verification_code (str): Verification code to send
            username (str, optional): Username for personalization
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Compose email message
            msg = MIMEText(f'''
            Hello{f' {username}' if username else ''},

            Your verification code is: {verification_code}

            This code will expire in 10 minutes. 
            If you did not request this verification, please ignore this email.

            Best regards,
            File Hider Application
            ''')
            
            msg['Subject'] = 'Email Verification - File Hider'
            msg['From'] = Config.SMTP_USERNAME
            msg['To'] = email
            
            # Send email via SMTP
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.sendmail(Config.SMTP_USERNAME, email, msg.as_string())
            
            return True
        except Exception as e:
            print(f"Email sending error: {e}")
            return False

    @classmethod
    def initiate_verification(
        cls, 
        db: Session, 
        user: User
    ) -> dict:
        """
        Initiate email verification process
        
        Args:
            db (Session): Database session
            user (User): User to verify
        
        Returns:
            dict: Verification status and details
        """
        # Check if user is already verified
        if user.is_verified:
            return {
                "status": "error",
                "message": "User is already verified"
            }
        
        # Generate verification code
        verification_code = cls.generate_verification_code()
        
        # Update user with verification code
        user.verification_code = verification_code
        user.verification_code_created_at = datetime.utcnow()
        db.commit()
        
        # Send verification email
        email_sent = cls.send_verification_email(
            email=user.email, 
            verification_code=verification_code,
            username=user.username
        )
        
        if email_sent:
            return {
                "status": "success",
                "message": "Verification code sent to email"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to send verification email"
            }

    @classmethod
    def verify_email(
        cls, 
        db: Session, 
        email: str, 
        verification_code: str
    ) -> dict:
        """
        Verify email using provided code
        
        Args:
            db (Session): Database session
            email (str): User's email
            verification_code (str): Verification code to validate
        
        Returns:
            dict: Verification result
        """
        # Find user by email
        user = db.query(User).filter_by(email=email).first()
        
        if not user:
            return {
                "status": "error",
                "message": "User not found"
            }
        
        # Check if already verified
        if user.is_verified:
            return {
                "status": "error",
                "message": "Email already verified"
            }
        
        # Check verification code
        if user.verification_code != verification_code:
            return {
                "status": "error",
                "message": "Invalid verification code"
            }
        
        # Check code expiration (10 minutes)
        code_age = datetime.utcnow() - user.verification_code_created_at
        if code_age.total_seconds() > 600:  # 10 minutes
            return {
                "status": "error",
                "message": "Verification code expired"
            }
        
        # Mark user as verified
        user.is_verified = True
        user.verification_code = None
        user.verification_code_created_at = None
        db.commit()
        
        return {
            "status": "success", 
            "message": "Email successfully verified"
        }

    @classmethod
    def resend_verification_code(
        cls, 
        db: Session, 
        email: str
    ) -> dict:
        """
        Resend verification code to user
        
        Args:
            db (Session): Database session
            email (str): User's email
        
        Returns:
            dict: Resend status and details
        """
        # Find user by email
        user = db.query(User).filter_by(email=email).first()
        
        if not user:
            return {
                "status": "error",
                "message": "User not found"
            }
        
        # Check if already verified
        if user.is_verified:
            return {
                "status": "error",
                "message": "User is already verified"
            }
        
        # Initiate new verification
        return cls.initiate_verification(db, user)