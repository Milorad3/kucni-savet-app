from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.post("", response_model=schemas.BuildingOut)
def create_building(
    building_in: schemas.BuildingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    building = models.Building(name=building_in.name, address=building_in.address)
    db.add(building)
    db.commit()
    db.refresh(building)

    # Onaj ko kreira zgradu automatski postaje admin (predsednik saveta) te zgrade
    current_user.building_id = building.id
    current_user.role = models.UserRole.admin
    db.commit()

    return building


@router.post("/{building_id}/apartments", response_model=schemas.ApartmentOut)
def add_apartment(
    building_id: str,
    apt_in: schemas.ApartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    building = db.query(models.Building).filter(models.Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Zgrada nije pronadjena")
    if not auth.can_manage_building(current_user, building):
        raise HTTPException(status_code=403, detail="Nemate prava upravljanja ovom zgradom")

    owner_id = None
    if apt_in.owner_email:
        owner = db.query(models.User).filter(models.User.email == apt_in.owner_email).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Vlasnik sa tim email-om nije registrovan")
        owner.building_id = building_id
        owner_id = owner.id

    apartment = models.Apartment(
        building_id=building_id,
        apartment_number=apt_in.apartment_number,
        ownership_percentage=apt_in.ownership_percentage,
        owner_id=owner_id,
    )
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


@router.get("/{building_id}/apartments", response_model=list[schemas.ApartmentOut])
def list_apartments(
    building_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.Apartment).filter(models.Apartment.building_id == building_id).all()
