import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from .. import models, schemas, auth, storage_utils
from ..database import get_db

router = APIRouter(tags=["documents"])

MAX_FILE_SIZE_MB = 15
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "xls", "xlsx"}


@router.post("/buildings/{building_id}/documents", response_model=schemas.DocumentOut)
async def upload_document(
    building_id: str,
    file: UploadFile = File(...),
    category: str = Form("ostalo"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    building = db.query(models.Building).filter(models.Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Zgrada nije pronadjena")

    # Ko sme da otpremi dokument: predsednik/upravnik te zgrade ILI vlasnik stana u njoj
    is_manager = current_user.role in (models.UserRole.admin, models.UserRole.company_admin) and \
        auth.can_manage_building(db, current_user, building)
    is_owner = (
        db.query(models.Apartment)
        .filter(models.Apartment.building_id == building_id, models.Apartment.owner_id == current_user.id)
        .first()
        is not None
    )
    if not (is_manager or is_owner):
        raise HTTPException(status_code=403, detail="Nemate pristup ovoj zgradi")

    if not storage_utils.STORAGE_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Skladiste dokumenata nije podeseno na serveru (nedostaju S3 environment varijable)",
        )

    extension = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Nepodrzan tip fajla: .{extension}")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Fajl je prevelik (max {MAX_FILE_SIZE_MB}MB)")

    storage_key = f"buildings/{building_id}/documents/{uuid.uuid4()}-{file.filename}"
    ok = storage_utils.upload_file(file_bytes, storage_key, file.content_type or "application/octet-stream")
    if not ok:
        raise HTTPException(status_code=500, detail="Upload nije uspeo, pokusajte ponovo")

    document = models.Document(
        building_id=building_id,
        uploaded_by_id=current_user.id,
        filename=file.filename,
        storage_key=storage_key,
        category=category,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/buildings/{building_id}/documents", response_model=list[schemas.DocumentOut])
def list_documents(
    building_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Document)
        .filter(models.Document.building_id == building_id)
        .order_by(models.Document.uploaded_at.desc())
        .all()
    )


@router.get("/documents/{document_id}/download-url")
def get_document_download_url(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Vraca privremeni link (vazi 1h) za preuzimanje dokumenta direktno sa S3."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronadjen")

    url = storage_utils.get_download_url(document.storage_key)
    if not url:
        raise HTTPException(status_code=503, detail="Skladiste dokumenata nije podeseno na serveru")
    return {"url": url, "filename": document.filename}
