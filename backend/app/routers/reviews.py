from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import (
    Document, User, UserRole, WorkflowStatus, ReviewComment, WorkflowHistory
)
from app.schemas import (
    ReviewCommentCreate, ReviewCommentResponse, WorkflowTransitionRequest,
    WorkflowHistoryResponse, DocumentDetailResponse
)
from app.dependencies import get_current_user, require_reviewer
from app.services.audit import WorkflowService
from app.routers.documents import build_document_detail_response

router = APIRouter(prefix="/documents", tags=["Reviews & Workflow"])

@router.post("/{id}/reviews", response_model=ReviewCommentResponse, status_code=status.HTTP_201_CREATED)
def add_review_comment(
    id: int,
    comment_in: ReviewCommentCreate,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer)
):
    """
    Add a review comment to a document (Reviewer only).
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    comment = WorkflowService.add_comment(
        db=db,
        document=doc,
        reviewer=reviewer,
        comment_text=comment_in.comment,
        action="commented"
    )

    return ReviewCommentResponse(
        id=comment.id,
        document_id=comment.document_id,
        reviewer_id=comment.reviewer_id,
        reviewer_name=reviewer.name,
        comment=comment.comment,
        action=comment.action,
        created_at=comment.created_at
    )

@router.post("/{id}/approve", response_model=DocumentDetailResponse)
def approve_document(
    id: int,
    req: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer)
):
    """
    Approve submitted document (Reviewer only).
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    reason = req.reason or "Document approved by procurement reviewer."
    WorkflowService.transition(
        db=db,
        document=doc,
        actor=reviewer,
        target_status=WorkflowStatus.APPROVED.value,
        reason=reason
    )
    WorkflowService.add_comment(
        db=db,
        document=doc,
        reviewer=reviewer,
        comment_text=reason,
        action="approved"
    )

    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.post("/{id}/reject", response_model=DocumentDetailResponse)
def reject_document(
    id: int,
    req: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer)
):
    """
    Reject submitted document with reason (Reviewer only).
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    reason = req.reason or "Document rejected by procurement reviewer."
    WorkflowService.transition(
        db=db,
        document=doc,
        actor=reviewer,
        target_status=WorkflowStatus.REJECTED.value,
        reason=reason
    )
    WorkflowService.add_comment(
        db=db,
        document=doc,
        reviewer=reviewer,
        comment_text=reason,
        action="rejected"
    )

    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.post("/{id}/request-corrections", response_model=DocumentDetailResponse)
def request_corrections(
    id: int,
    req: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_reviewer)
):
    """
    Return submitted document back to Draft state with explanation of needed corrections (Reviewer only).
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not req.reason or not req.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A detailed reason must be provided when requesting corrections."
        )

    WorkflowService.transition(
        db=db,
        document=doc,
        actor=reviewer,
        target_status=WorkflowStatus.DRAFT.value,
        reason=req.reason
    )
    WorkflowService.add_comment(
        db=db,
        document=doc,
        reviewer=reviewer,
        comment_text=f"Corrections requested: {req.reason}",
        action="requested_corrections"
    )

    db.refresh(doc)
    return build_document_detail_response(doc, db)

@router.get("/{id}/history", response_model=List[WorkflowHistoryResponse])
def get_document_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve chronological audit trail of all workflow state changes.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    history_records = (
        db.query(WorkflowHistory)
        .filter(WorkflowHistory.document_id == id)
        .order_by(WorkflowHistory.created_at.asc())
        .all()
    )

    result = []
    for h in history_records:
        actor_name = h.actor.name if h.actor else f"User #{h.actor_id}"
        result.append(
            WorkflowHistoryResponse(
                id=h.id,
                document_id=h.document_id,
                actor_id=h.actor_id,
                actor_name=actor_name,
                previous_status=h.previous_status,
                new_status=h.new_status,
                reason=h.reason,
                created_at=h.created_at
            )
        )
    return result
