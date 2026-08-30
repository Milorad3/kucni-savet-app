from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=schemas.CompanyOut)
def create_company(
    company_in: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Registracija firme koja upravlja vise zgrada.
    Korisnik koji je kreira automatski postaje company_admin - vidi i upravlja
    SVIM zgradama koje kasnije doda pod ovu firmu.
    """
    company = models.ManagementCompany(name=company_in.name, pib=company_in.pib)
    db.add(company)
    db.commit()
    db.refresh(company)

    current_user.role = models.UserRole.company_admin
    current_user.company_id = company.id
    db.commit()

    return company


@router.get("/{company_id}/buildings", response_model=list[schemas.BuildingWithStatsOut])
def list_company_buildings(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_company_admin),
):
    """Sve zgrade koje firma vodi - glavni 'dashboard' pregled za upravnika."""
    if current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Nemate pristup ovoj firmi")

    buildings = db.query(models.Building).filter(models.Building.management_company_id == company_id).all()

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


@router.post("/{company_id}/buildings", response_model=schemas.BuildingOut)
def add_building_to_company(
    company_id: str,
    building_in: schemas.BuildingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_company_admin),
):
    """Firma dodaje novu zgradu pod svoje upravljanje."""
    if current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Nemate pristup ovoj firmi")

    building = models.Building(
        name=building_in.name,
        address=building_in.address,
        management_company_id=company_id,
    )
    db.add(building)
    db.commit()
    db.refresh(building)
    return building
