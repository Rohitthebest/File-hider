from config import Config
from sqlalchemy import create_engine, Column, Integer, String, Boolean,ForeignKey,DATETIME
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI,pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String)


class HiddenFile(Base):
    __tablename__ = "hidden_files"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    original_filename = Column(String)
    hidden_filename = Column(String)
    file_path = Column(String)
    hidden_at = Column(DATETIME, default=datetime.datetime.utcnow())