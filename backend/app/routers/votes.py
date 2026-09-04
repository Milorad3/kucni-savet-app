from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(tags=["votes"])

# Kvorum pravilo - moze se konfigurisati po zgradi, ovde 50% kao standard
QUORUM_THRESHOLD_PERCENTAGE = 50.0
PASS_THRESHOLD_PERCENTAGE = 50.0  # potrebno "za" da odluka prodje


def calculate_meeting_results(db, meeting) -> list:
    """
    Racuna rezultate na osnovu PROCENTA VLASNISTVA, ne broja glasova.
    Ovo je pravno ispravan nacin racunanja u kucnim savetima -
    vlasnik veceg stana ima veci uticaj na odluku, srazmerno vlasnistvu.

    Izdvojeno iz get_results endpoint-a da bi se ista logika mogla koristiti
    i za PDF zapisnik (meetings.py), bez dupliranja koda.
    """
    total_ownership = (
        db.query(models.Apartment)
        .filter(models.Apartment.building_id == meeting.building_id)
        .with_entities(models.Apartment.ownership_percentage)
        .all()
    )
    total_ownership_sum = sum(a[0] for a in total_ownership) or 100.0

    results = []
    for item in meeting.agenda_items:
        votes = db.query(models.Vote).filter(models.Vote.agenda_item_id == item.id).all()

        for_sum = against_sum = abstain_sum = 0.0
        for v in votes:
            apt = (
                db.query(models.Apartment)
                .filter(models.Apartment.owner_id == v.user_id, models.Apartment.building_id == meeting.building_id)
                .first()
            )
            weight = apt.ownership_percentage if apt else 0.0
            if v.choice == models.VoteChoice.for_:
                for_sum += weight
            elif v.choice == models.VoteChoice.against:
                against_sum += weight
            else:
                abstain_sum += weight

        total_voted = for_sum + against_sum + abstain_sum
        quorum_reached = total_voted >= (QUORUM_THRESHOLD_PERCENTAGE / 100.0) * total_ownership_sum
        passed = quorum_reached and for_sum > against_sum

        results.append(
            schemas.VoteResult(
                agenda_item_id=item.id,
                title=item.title,
                total_ownership_voted=round(total_voted, 2),
                for_percentage=round(for_sum, 2),
                against_percentage=round(against_sum, 2),
                abstain_percentage=round(abstain_sum, 2),
                quorum_reached=quorum_reached,
                passed=passed,
            )
        )

    return results


@router.post("/agenda-items/{agenda_item_id}/vote")
def cast_vote(
    agenda_item_id: str,
    vote_in: schemas.VoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    agenda_item = db.query(models.AgendaItem).filter(models.AgendaItem.id == agenda_item_id).first()
    if not agenda_item:
        raise HTTPException(status_code=404, detail="Tacka dnevnog reda nije pronadjena")

    meeting = agenda_item.meeting
    if meeting.status != models.MeetingStatus.active:
        raise HTTPException(status_code=400, detail="Glasanje nije trenutno otvoreno za ovaj sastanak")

    # Korisnik mora da poseduje stan u ovoj zgradi da bi glasao
    apartment = (
        db.query(models.Apartment)
        .filter(models.Apartment.owner_id == current_user.id, models.Apartment.building_id == meeting.building_id)
        .first()
    )
    if not apartment:
        raise HTTPException(status_code=403, detail="Niste registrovani kao vlasnik stana u ovoj zgradi")

    # Da li je korisnik vec glasao za ovu tacku - ako jeste, azuriramo (promena glasa dozvoljena dok je aktivno)
    existing_vote = (
        db.query(models.Vote)
        .filter(models.Vote.agenda_item_id == agenda_item_id, models.Vote.user_id == current_user.id)
        .first()
    )
    if existing_vote:
        existing_vote.choice = vote_in.choice
    else:
        vote = models.Vote(agenda_item_id=agenda_item_id, user_id=current_user.id, choice=vote_in.choice)
        db.add(vote)

    db.commit()
    return {"status": "ok", "message": "Glas je zabelezen"}


@router.get("/meetings/{meeting_id}/results", response_model=list[schemas.VoteResult])
def get_results(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Sastanak nije pronadjen")
    return calculate_meeting_results(db, meeting)
