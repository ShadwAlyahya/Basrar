import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

router = APIRouter(prefix="/auth", tags=["Authentication"])

temp_verification_codes = {}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegisterRequest(UserCreate):
    lang: Optional[str] = "en"

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    lang: Optional[str] = "en"

class Token(BaseModel):
    access_token: str
    token_type: str

def send_real_email(to_email: str, subject: str, body_text: str):
    try:
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            return False
            
        msg = MIMEMultipart()
        msg['From'] = formataddr((str(Header('Basrar AI', 'utf-8')), SENDER_EMAIL))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body_text, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered" if user_data.lang == "en" else "البريد الإلكتروني مسجل مسبقاً"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    verification_code = str(random.randint(100000, 999999))
    temp_verification_codes[user_data.email] = verification_code
    
    if user_data.lang == "ar":
        subject = "رمز تفعيل حسابك في منصة بصرار (Basrar AI)"
        body = f"مرحباً {new_user.username}،\n\nشكراً لتسجيلك في منصة بصرار للتحليل التنفيذي.\nرمز التحقق الخاص بك هو: {verification_code}\n\nيرجى استخدامه لتفعيل حسابك."
    else:
        subject = "Your Basrar AI Account Verification Code"
        body = f"Hello {new_user.username},\n\nThank you for registering with Basrar Executive Analytics.\nYour verification code is: {verification_code}\n\nPlease use it to verify your account."
    
    send_real_email(new_user.email, subject, body)
    
    return {"message": "Verification code sent successfully", "email": new_user.email}

@router.post("/verify-code")
def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    stored_code = temp_verification_codes.get(data.email)
    if not stored_code or stored_code != data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    db.commit()
    
    del temp_verification_codes[data.email]
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "message": "Account verified successfully"}

@router.post("/login", response_model=Token)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if hasattr(user, 'is_verified') and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not verified. Please verify your email first.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="البريد الإلكتروني غير مسجل لدينا." if data.lang == "ar" else "Email not registered."
        )
    
    reset_token = str(random.randint(10000, 99999))
    
    if data.lang == "ar":
        subject = "إعادة تعيين كلمة المرور - منصة بصرار"
        body = f"مرحباً،\n\nلقد طلبت إعادة تعيين كلمة المرور لحسابك في بصرار.\nرمز إعادة التعيين الخاص بك هو: {reset_token}"
    else:
        subject = "Password Reset - Basrar AI"
        body = f"Hello,\n\nYou requested a password reset for your Basrar account.\nYour reset token is: {reset_token}"
    
    success = send_real_email(data.email, subject, body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="فشل إرسال بريد استعادة كلمة المرور." if data.lang == "ar" else "Failed to send password reset email."
        )
        
    return {"message": "تم إرسال تعليمات إعادة تعيين كلمة المرور إلى بريدك الإلكتروني بنجاح." if data.lang == "ar" else "Password reset instructions sent successfully."}