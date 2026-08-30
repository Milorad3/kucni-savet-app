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
    # company_admin upravlja vise zgrada pa MORA da kaze za koju je sastanak;
    # obican admin (predsednik) ima samo jednu zgradu, pa se ona koristi automatski.
    if current_user.role == models.UserRole.company_admin:
        if not meeting_in.building_id:
            raise HTTPException(status_code=400, detail="Morate izabrati zgradu za koju kreirate sastanak")
        target_building_id = meeting_in.building_id
    else:
        if not current_user.building_id:
            raise HTTPException(status_code=400, detail="Prvo morate kreirati/pridruziti se zgradi")
        target_building_id = current_user.building_id

    building = db.query(models.Building).filter(models.Building.id == target_building_id).first()
    if not building or not auth.can_manage_building(current_user, building):
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
    if current_user.role == models.UserRole.company_admin:
        # Upravnik moze da vidi sastanke SVIH svojih zgrada, ili filtrira po jednoj
        query = db.query(models.Meeting).join(models.Building).filter(
            models.Building.management_company_id == current_user.company_id
        )
        if building_id:
            query = query.filter(models.Meeting.building_id == building_id)
        return query.order_by(models.Meeting.scheduled_at.desc()).all()

    return (
        db.query(models.Meeting)
        .filter(models.Meeting.building_id == current_user.building_id)
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
    if not auth.can_manage_building(current_user, meeting.building):
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
    if not auth.can_manage_building(current_user, meeting.building):
        raise HTTPException(status_code=403, detail="Nemate prava upravljanja ovim sastankom")
    meeting.status = models.MeetingStatus.closed
    db.commit()
    db.refresh(meeting)
    return meeting
