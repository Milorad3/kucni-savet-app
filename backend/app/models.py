import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    company_admin = "company_admin"  # zaposleni u firmi koja upravlja vise zgrada - vidi/upravlja SVIM zgradama firme
    admin = "admin"                  # predsednik kucnog saveta - vidi/upravlja SAMO svojom zgradom
    resident = "resident"            # stanar/vlasnik - glasa u svojoj zgradi


class MeetingStatus(str, enum.Enum):
    scheduled = "scheduled"
    active = "active"
    closed = "closed"


class VoteChoice(str, enum.Enum):
    for_ = "for"
    against = "against"
    abstain = "abstain"


class BuildingAdmin(Base):
    """
    Many-to-many veza: koje zgrade jedan 'admin' (predsednik) vodi.
    Zamenjuje staro ogranicenje 'jedan predsednik = jedna zgrada' -
    sada predsednik moze da vodi vise zgrada bez potrebe da pravi formalnu firmu.
    """
    __tablename__ = "building_admins"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    building_id = Column(UUID(as_uuid=False), ForeignKey("buildings.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    building = relationship("Building", back_populates="admin_links")
    user = relationship("User", back_populates="managed_building_links")


class ManagementCompany(Base):
    """Firma koja profesionalno upravlja sa vise zgrada (npr. 'Upravnik doo')."""
    __tablename__ = "management_companies"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    pib = Column(String, nullable=True)  # poreski identifikacioni broj, opciono
    created_at = Column(DateTime, default=datetime.utcnow)

    buildings = relationship("Building", back_populates="management_company")
    employees = relationship("User", back_populates="company")


class Building(Base):
    __tablename__ = "buildings"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    # Ako je zgrada pod profesionalnim upravljanjem - veza ka firmi. Ako je NULL,
    # zgrada je samostalna (Opcija A - vodi je sam predsednik saveta).
    management_company_id = Column(UUID(as_uuid=False), ForeignKey("management_companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    management_company = relationship("ManagementCompany", back_populates="buildings")
    apartments = relationship("Apartment", back_populates="building")
    meetings = relationship("Meeting", back_populates="building")
    admin_links = relationship("BuildingAdmin", back_populates="building")


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.resident)
    # NAPOMENA: building_id ostaje samo kao "podrazumevana/prva zgrada" radi kompatibilnosti
    # sa starijim delovima koda. Stvarna lista zgrada koje admin vodi je u building_admins tabeli.
    building_id = Column(UUID(as_uuid=False), ForeignKey("buildings.id"), nullable=True)
    # Za zaposlene u firmi koja upravlja vise zgrada (company_admin):
    company_id = Column(UUID(as_uuid=False), ForeignKey("management_companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    apartments = relationship("Apartment", back_populates="owner")
    votes = relationship("Vote", back_populates="user")
    company = relationship("ManagementCompany", back_populates="employees")
    managed_building_links = relationship("BuildingAdmin", back_populates="user")


class Apartment(Base):
    """Stan - bitan za tacan obracun kvoruma po vlasnistvu (%)"""
    __tablename__ = "apartments"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    building_id = Column(UUID(as_uuid=False), ForeignKey("buildings.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    apartment_number = Column(String, nullable=False)
    ownership_percentage = Column(Float, nullable=False)  # npr. 2.5 = 2.5% zgrade

    building = relationship("Building", back_populates="apartments")
    owner = relationship("User", back_populates="apartments")


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    building_id = Column(UUID(as_uuid=False), ForeignKey("buildings.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(Enum(MeetingStatus), default=MeetingStatus.scheduled)
    created_at = Column(DateTime, default=datetime.utcnow)

    building = relationship("Building", back_populates="meetings")
    agenda_items = relationship("AgendaItem", back_populates="meeting", cascade="all, delete-orphan")


class AgendaItem(Base):
    __tablename__ = "agenda_items"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_id = Column(UUID(as_uuid=False), ForeignKey("meetings.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Float, default=0)

    meeting = relationship("Meeting", back_populates="agenda_items")
    votes = relationship("Vote", back_populates="agenda_item", cascade="all, delete-orphan")


class Vote(Base):
    __tablename__ = "votes"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    agenda_item_id = Column(UUID(as_uuid=False), ForeignKey("agenda_items.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    choice = Column(Enum(VoteChoice), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    agenda_item = relationship("AgendaItem", back_populates="votes")
    user = relationship("User", back_populates="votes")
