from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from .models import UserRole, MeetingStatus, VoteChoice


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    building_id: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Management Company (firma koja upravlja vise zgrada) ----
class CompanyCreate(BaseModel):
    name: str
    pib: Optional[str] = None


class CompanyOut(BaseModel):
    id: str
    name: str
    pib: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Building / Apartment ----
class BuildingCreate(BaseModel):
    name: str
    address: str


class BuildingOut(BaseModel):
    id: str
    name: str
    address: str
    management_company_id: Optional[str] = None

    class Config:
        from_attributes = True


class BuildingWithStatsOut(BuildingOut):
    apartment_count: int = 0
    upcoming_meeting_count: int = 0


class ApartmentCreate(BaseModel):
    apartment_number: str
    ownership_percentage: float
    owner_email: Optional[EmailStr] = None


class ApartmentOut(BaseModel):
    id: str
    apartment_number: str
    ownership_percentage: float
    owner_id: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Meeting / Agenda ----
class AgendaItemCreate(BaseModel):
    title: str
    description: Optional[str] = None


class AgendaItemOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    agenda_items: List[AgendaItemCreate] = []
    # Obavezno samo za company_admin koji upravlja vise zgrada - bira za koju zgradu je sastanak.
    # Predsednik (admin) ovo ne salje, automatski se koristi njegova zgrada.
    building_id: Optional[str] = None


class MeetingOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    status: MeetingStatus
    agenda_items: List[AgendaItemOut] = []

    class Config:
        from_attributes = True


# ---- Vote ----
class VoteCreate(BaseModel):
    choice: VoteChoice


class VoteResult(BaseModel):
    agenda_item_id: str
    title: str
    total_ownership_voted: float
    for_percentage: float
    against_percentage: float
    abstain_percentage: float
    quorum_reached: bool
    passed: bool
