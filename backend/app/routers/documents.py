import os
import uuid
import shutil
from typing import List, Optional, Dict
from pathlib import Path
from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, Query
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.database import get_db
from app.models import (
    Document, User, UserRole, ProcessingStatus, WorkflowStatus,
    ExtractedField, WorkflowHistory, PurchaseOrder, ReviewComment
)
from app.schemas import (
    DocumentResponse, DocumentDetailResponse, DocumentFieldsUpdate,
    ExtractedFieldResponse, PurchaseOrderResponse, ReviewCommentResponse,
    WorkflowHistoryResponse
)
from app.dependencies import get_current_user
from app.config import settings
from app.services.extractor import DocumentExtractor
from app.services.validator import DocumentValidator
from app.services.audit import WorkflowService

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg"
}
MAX_FILE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

def build_document_detail_response(doc: Document, db: Session) -> DocumentDetailResponse:
    owner_name = doc.owner.name if doc.owner else f"User #{doc.owner_id}"

    # Extracted fields
    ext_fields = [ExtractedFieldResponse.model_validate(f) for f in doc.extracted_fields]
    fields_dict = {f.field_name: f.field_value for f in doc.extracted_fields}
    field_confs = {f.field_name: f.confidence for f in doc.extracted_fields}

    # Run validation engine
    warnings = DocumentValidator.validate_document(
        document_id=doc.id,
        fields_dict=fields_dict,
        field_confidences=field_confs,
        db=db
    )

    # Purchase orders
    po_responses = [PurchaseOrderResponse.model_validate(po) for po in doc.purchase_orders]

    # Comments with reviewer name
    comment_responses = []
    for c in doc.review_comments:
        c_resp = ReviewCommentResponse(
            id=c.id,
            document_id=c.document_id,
            reviewer_id=c.reviewer_id,
            reviewer_name=c.reviewer.name if c.reviewer else f"Reviewer #{c.reviewer_id}",
            comment=c.comment,
            action=c.action,
            created_at=c.created_at
        )
        comment_responses.append(c_resp)

    # Workflow history with actor name
    hist_responses = []
    for h in doc.workflow_history:
        h_resp = WorkflowHistoryResponse(
            id=h.id,
            document_id=h.document_id,
            actor_id=h.actor_id,
            actor_name=h.actor.name if h.actor else f"User #{h.actor_id}",
            previous_status=h.previous_status,
            new_status=h.new_status,
            reason=h.reason,
            created_at=h.created_at
        )
        hist_responses.append(h_resp)

    return DocumentDetailResponse(
        id=doc.id,
        owner_id=doc.owner_id,
        owner_name=owner_name,
        original_filename=doc.original_filename,
        document_type=doc.document_type,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        processing_status=doc.processing_status,
        workflow_status=doc.workflow_status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        extracted_fields=ext_fields,
        purchase_orders=po_responses,
        review_comments=comment_responses,
        workflow_history=hist_responses,
        validation_warnings=warnings
    )

@router.post("", response_model=DocumentDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document (PDF, PNG, JPG), validate type and size, and perform OCR / extraction.
    """
    orig_filename = file.filename or "unknown"
    ext = Path(orig_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # Read and validate size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    # Generate safe unique filename
    unique_name = f"{uuid.uuid4().hex}_{Path(orig_filename).name}"
    save_path = Path(settings.UPLOAD_DIR) / unique_name

    with open(save_path, "wb") as f_out:
        f_out.write(content)

    mime_type = file.content_type or "application/octet-stream"

    # Create document record
    doc = Document(
        owner_id=current_user.id,
        document_type="invoice",
        original_filename=orig_filename,
        relative_file_path=str(unique_name),
        mime_type=mime_type,
        file_size=file_size,
        processing_status=ProcessingStatus.PROCESSING.value,
        workflow_status=WorkflowStatus.DRAFT.value
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Record initial creation in audit history
    init_hist = WorkflowHistory(
        document_id=doc.id,
        actor_id=current_user.id,
        previous_status=None,
        new_status=WorkflowStatus.DRAFT.value,
        reason="Document uploaded and created in Draft state."
    )
    db.add(init_hist)
    db.commit()

    # Trigger extraction
    try:
        extracted = DocumentExtractor.extract_fields(str(save_path), mime_type)
        for field in extracted:
            ef = ExtractedField(
                document_id=doc.id,
                field_name=field.name,
                field_value=field.value,
                source_page=field.source_page,
                source_text=field.source_text,
                confidence=field.confidence,
                updated_by=current_user.id
            )
            db.add(ef)
        doc.processing_status = ProcessingStatus.COMPLETED.value
        db.commit()
    except Exception as e:
        doc.processing_status = ProcessingStatus.FAILED.value
        db.commit()

    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    search: Optional[str] = Query(None, description="Search by filename or invoice number"),
    workflow_status: Optional[str] = Query(None),
    processing_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List documents with search, status filters, and pagination.
    Submitters see their own documents; Reviewers see all documents.
    """
    query = db.query(Document)

    if current_user.role == UserRole.SUBMITTER.value:
        query = query.filter(Document.owner_id == current_user.id)

    if workflow_status:
        query = query.filter(Document.workflow_status == workflow_status)

    if processing_status:
        query = query.filter(Document.processing_status == processing_status)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.outerjoin(ExtractedField).filter(
            or_(
                Document.original_filename.ilike(term),
                (ExtractedField.field_name == "invoice_number") & (ExtractedField.field_value.ilike(term)),
                (ExtractedField.field_name == "vendor_name") & (ExtractedField.field_value.ilike(term))
            )
        ).distinct()

    docs = query.order_by(desc(Document.created_at)).offset(offset).limit(limit).all()

    result = []
    for d in docs:
        owner_name = d.owner.name if d.owner else f"User #{d.owner_id}"
        resp = DocumentResponse(
            id=d.id,
            owner_id=d.owner_id,
            owner_name=owner_name,
            original_filename=d.original_filename,
            document_type=d.document_type,
            mime_type=d.mime_type,
            file_size=d.file_size,
            processing_status=d.processing_status,
            workflow_status=d.workflow_status,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        result.append(resp)
    return result

@router.get("/{id}", response_model=DocumentDetailResponse)
def get_document(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full document details, extracted fields, validation warnings, and audit trail.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this document.")

    return build_document_detail_response(doc, db)

@router.patch("/{id}/fields", response_model=DocumentDetailResponse)
def update_document_fields(
    id: int,
    fields_update: DocumentFieldsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit extracted fields. Submitters can only edit while in 'draft' state.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value:
        if doc.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this document.")
        if doc.workflow_status != WorkflowStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit fields while document is in '{doc.workflow_status}' status. Document must be in Draft."
            )

    # Update or insert fields
    for field_name, new_val in fields_update.fields.items():
        existing = (
            db.query(ExtractedField)
            .filter(ExtractedField.document_id == doc.id, ExtractedField.field_name == field_name)
            .first()
        )
        if existing:
            existing.field_value = new_val
            existing.updated_by = current_user.id
            # User manually edited/confirmed value, bump confidence to 1.0
            existing.confidence = 1.0
        else:
            new_field = ExtractedField(
                document_id=doc.id,
                field_name=field_name,
                field_value=new_val,
                source_page=1,
                source_text="User manual entry",
                confidence=1.0,
                updated_by=current_user.id
            )
            db.add(new_field)

    db.commit()
    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.post("/{id}/process", response_model=DocumentDetailResponse)
def reprocess_document(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry or re-run document extraction and validation.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    doc.processing_status = ProcessingStatus.PROCESSING.value
    db.commit()

    file_path = Path(settings.UPLOAD_DIR) / doc.relative_file_path
    if not file_path.exists():
        doc.processing_status = ProcessingStatus.FAILED.value
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file missing on disk.")

    try:
        extracted = DocumentExtractor.extract_fields(str(file_path), doc.mime_type)
        # Clear existing extracted fields
        db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).delete()
        for field in extracted:
            ef = ExtractedField(
                document_id=doc.id,
                field_name=field.name,
                field_value=field.value,
                source_page=field.source_page,
                source_text=field.source_text,
                confidence=field.confidence,
                updated_by=current_user.id
            )
            db.add(ef)
        doc.processing_status = ProcessingStatus.COMPLETED.value
        db.commit()
    except Exception as e:
        doc.processing_status = ProcessingStatus.FAILED.value
        db.commit()

    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.post("/{id}/submit", response_model=DocumentDetailResponse)
def submit_document(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit document for Reviewer evaluation (transitions Draft -> Submitted).
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    WorkflowService.transition(
        db=db,
        document=doc,
        actor=current_user,
        target_status=WorkflowStatus.SUBMITTED.value,
        reason="Document submitted by user for formal procurement review."
    )

    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.get("/{id}/file")
def get_document_file(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Serve raw uploaded file for in-browser PDF viewer and image display.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    file_path = Path(settings.UPLOAD_DIR) / doc.relative_file_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file not found.")

    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type=doc.mime_type
    )
