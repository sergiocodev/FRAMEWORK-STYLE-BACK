from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.services import user_service
from app.schemas import user_schema
from google.oauth2 import id_token
from google.auth.transport import requests
import secrets
import string

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_service.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def register(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    db_user_name = user_service.get_user_by_username(db, username=user.username)
    if db_user_name:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
        
    return user_service.create_user(db=db, user=user)

@router.post("/google")
def google_login(google_token: user_schema.GoogleToken, db: Session = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "tu-client-id-aqui.apps.googleusercontent.com":
        raise HTTPException(status_code=500, detail="Google authentication is not configured in backend.")
        
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token.token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        user_email = idinfo.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="El token de Google no contiene email")
            
        user_name = idinfo.get("name", "")
        
        user = user_service.get_user_by_email(db, email=user_email)
        
        if not user:
            random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            base_username = user_email.split('@')[0]
            username = base_username
            counter = 1
            while user_service.get_user_by_username(db, username=username):
                username = f"{base_username}{counter}"
                counter += 1
                
            new_user = user_schema.UserCreate(
                email=user_email,
                username=username,
                full_name=user_name,
                password=random_password
            )
            user = user_service.create_user(db=db, user=new_user)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")
