from sqlalchemy import Column, Integer, String, DateTime, text
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    
    full_name = Column(String(100), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    deleted_at = Column(DateTime, nullable=True)
