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
    """
    Kreira novu zgradu. Moze se pozvati VISE PUTA od strane istog admina -
    jedan predsednik sada moze da vodi vise nezavisnih zgrada (bez formalne firme).
    """
    building = models.Building(name=building_in.name, address=building_in.address)
    db.add(building)
    db.flush()  # da dobijemo building.id pre commit-a

    # Poveži korisnika sa ovom zgradom preko building_admins tabele (many-to-many)
    link = models.BuildingAdmin(building_id=building.id, user_id=current_user.id)
    db.add(link)

    current_user.role = models.UserRole.admin
    # building_id se postavlja samo ako korisnik JOS NEMA podrazumevanu zgradu
    # (cuva se kao "prva/podrazumevana" radi kompatibilnosti sa starijim delovima koda)
    if not current_user.building_id:
        current_user.building_id = building.id

    db.commit()
    db.refresh(building)
    return building


@router.get("/mine", response_model=list[schemas.BuildingWithStatsOut])
def list_my_buildings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """Sve zgrade koje OVAJ predsednik vodi (moze biti vise od jedne)."""
    building_ids = auth.get_managed_building_ids(db, current_user)
    buildings = db.query(models.Building).filter(models.Building.id.in_(building_ids)).all()

    results = []
    for b in buildings:
        apartment_count = db.query(models.Apartment).filter(models.Apartment.building_id == b.id).count()
        upcoming_count = (
            db.query(models.Meeting)
            .filter(models.Meeting.building_id == b.id, models.Meeting.status != models.MeetingStatus.closed)
            .count()
        )
        results.append(
            schemas.BuildingWithStatsOut(
                id=b.id,
                name=b.name,
                address=b.address,
                management_company_id=b.management_company_id,
                apartment_count=apartment_count,
                upcoming_meeting_count=upcoming_count,
            )
        )
    return results


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
    if not auth.can_manage_building(db, current_user, building):
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
