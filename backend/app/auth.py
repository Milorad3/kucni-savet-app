import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models
from .database import get_db

# VAZNO: u produkciji ovo mora biti tajna vrednost iz environment varijable,
# nikad hardkodovano u kodu.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dana

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nevazeci ili istekao token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Predsednik saveta SVOJE zgrade ili company_admin (koji upravlja vise zgrada)."""
    if user.role not in (models.UserRole.admin, models.UserRole.company_admin):
        raise HTTPException(status_code=403, detail="Samo predsednik saveta ili upravnik moze ovu akciju")
    return user


def require_company_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Iskljucivo za zaposlene firme koja upravlja vise zgrada."""
    if user.role != models.UserRole.company_admin:
        raise HTTPException(status_code=403, detail="Samo upravnik (firma) moze ovu akciju")
    return user


def can_manage_building(db, user: models.User, building: models.Building) -> bool:
    """
    Centralna provera: da li ovaj korisnik sme da upravlja OVOM konkretnom zgradom.
    - company_admin: da, ako je zgrada pod njegovom firmom (vidi SVE zgrade firme)
    - admin: da, ako je AKTIVNO povezan sa tom zgradom preko building_admins tabele
      (jedan admin/predsednik sada moze da vodi VISE zgrada, ne samo jednu)
    """
    if user.role == models.UserRole.company_admin:
        return building.management_company_id is not None and building.management_company_id == user.company_id
    if user.role == models.UserRole.admin:
        link = (
            db.query(models.BuildingAdmin)
            .filter(models.BuildingAdmin.user_id == user.id, models.BuildingAdmin.building_id == building.id)
            .first()
        )
        return link is not None
    return False


def get_managed_building_ids(db, user: models.User) -> list:
    """Vraca listu ID-jeva svih zgrada kojima korisnik sme da upravlja."""
    if user.role == models.UserRole.company_admin:
        rows = db.query(models.Building.id).filter(models.Building.management_company_id == user.company_id).all()
        return [r[0] for r in rows]
    if user.role == models.UserRole.admin:
        rows = db.query(models.BuildingAdmin.building_id).filter(models.BuildingAdmin.user_id == user.id).all()
        return [r[0] for r in rows]
    return []
