from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=schemas.MeetingOut)
def create_meeting(
    meeting_in: schemas.MeetingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    # I admin i company_admin sada mogu da vode vise zgrada, pa oboje MORAJU
    # da kazu za koju zgradu je sastanak - OSIM ako vode tacno jednu (tada se
    # ona bira automatski, radi jednostavnosti kad nema dileme).
    managed_ids = auth.get_managed_building_ids(db, current_user)

    if meeting_in.building_id:
        target_building_id = meeting_in.building_id
    elif len(managed_ids) == 1:
        target_building_id = managed_ids[0]
    elif len(managed_ids) == 0:
        raise HTTPException(status_code=400, detail="Prvo morate kreirati/pridruziti se zgradi")
    else:
        raise HTTPException(status_code=400, detail="Vodite vise zgrada - morate izabrati za koju je sastanak")

    building = db.query(models.Building).filter(models.Building.id == target_building_id).first()
    if not building or not auth.can_manage_building(db, current_user, building):
        raise HTTPException(status_code=403, detail="Nemate prava upravljanja ovom zgradom")

    meeting = models.Meeting(
        building_id=target_building_id,
        title=meeting_in.title,
        description=meeting_in.description,
        scheduled_at=meeting_in.scheduled_at,
        status=models.MeetingStatus.scheduled,
    )
    db.add(meeting)
    db.flush()  # da dobijemo meeting.id pre commit-a

    for idx, item in enumerate(meeting_in.agenda_items):
        agenda_item = models.AgendaItem(
            meeting_id=meeting.id,
            title=item.title,
            description=item.description,
            order_index=idx,
        )
        db.add(agenda_item)

    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=list[schemas.MeetingOut])
def list_meetings(
    building_id: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role in (models.UserRole.company_admin, models.UserRole.admin):
        # Upravnik/predsednik moze da vidi sastanke SVIH svojih zgrada, ili filtrira po jednoj
        managed_ids = auth.get_managed_building_ids(db, current_user)
        query = db.query(models.Meeting).filter(models.Meeting.building_id.in_(managed_ids))
        if building_id:
            query = query.filter(models.Meeting.building_id == building_id)
        return query.order_by(models.Meeting.scheduled_at.desc()).all()

    # Stanar - sastanci u zgradama gde ima bar jedan stan
    apartment_building_ids = (
        db.query(models.Apartment.building_id).filter(models.Apartment.owner_id == current_user.id).all()
    )
    building_ids = [b[0] for b in apartment_building_ids]
    return (
        db.query(models.Meeting)
        .filter(models.Meeting.building_id.in_(building_ids))
        .order_by(models.Meeting.scheduled_at.desc())
        .all()
    )


@router.get("/{meeting_id}", response_model=schemas.MeetingOut)
def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Sastanak nije pronadjen")
    return meeting


@router.post("/{meeting_id}/activate", response_model=schemas.MeetingOut)
def activate_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """Otvara sastanak za glasanje - stanari mogu da glasaju samo dok je 'active'."""
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Sastanak nije pronadjen")
    if not auth.can_manage_building(db, current_user, meeting.building):
        raise HTTPException(status_code=403, detail="Nemate prava upravljanja ovim sastankom")
    meeting.status = models.MeetingStatus.active
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/close", response_model=schemas.MeetingOut)
def close_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    """Zatvara glasanje - posle ovoga vise niko ne moze da glasa, rezultati su konacni."""
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Sastanak nije pronadjen")
    if not auth.can_manage_building(db, current_user, meeting.building):
        raise HTTPException(status_code=403, detail="Nemate prava upravljanja ovim sastankom")
    meeting.status = models.MeetingStatus.closed
    db.commit()
    db.refresh(meeting)
    return meeting
