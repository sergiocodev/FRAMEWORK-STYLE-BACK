from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models import user_model
from app.schemas import user_schema
from app.core.security import get_password_hash, pwd_context

def get_user(db: Session, user_id: int):
    return db.query(user_model.User).filter(user_model.User.id == user_id, user_model.User.deleted_at.is_(None)).first()

def get_user_by_email(db: Session, email: str):
    return db.query(user_model.User).filter(user_model.User.email == email, user_model.User.deleted_at.is_(None)).first()

def get_user_by_username(db: Session, username: str):
    return db.query(user_model.User).filter(user_model.User.username == username, user_model.User.deleted_at.is_(None)).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(user_model.User).filter(user_model.User.deleted_at.is_(None)).offset(skip).limit(limit).all()

def create_user(db: Session, user: user_schema.UserCreate):
    hashed_pwd = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})
    db_user = user_model.User(
        **user_data,
        hashed_password=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: user_schema.UserUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        for key, value in update_data.items():
            setattr(db_user, key, value)
            
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.deleted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)
    return db_user
