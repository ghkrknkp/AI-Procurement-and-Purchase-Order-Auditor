from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import (
    Document, User, UserRole, ProcessingStatus, WorkflowStatus, WorkflowHistory
)
from app.schemas import DashboardStats, WorkflowHistoryResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve aggregated dashboard statistics.
    Submitters see statistics for their own submissions; Reviewers see system-wide stats.
    """
    doc_query = db.query(Document)
    if current_user.role == UserRole.SUBMITTER.value:
        doc_query = doc_query.filter(Document.owner_id == current_user.id)

    total_docs = doc_query.count()
    pending_proc = doc_query.filter(Document.processing_status == ProcessingStatus.PENDING.value).count()
    processing_cnt = doc_query.filter(Document.processing_status == ProcessingStatus.PROCESSING.value).count()
    completed_proc = doc_query.filter(Document.processing_status == ProcessingStatus.COMPLETED.value).count()
    failed_proc = doc_query.filter(Document.processing_status == ProcessingStatus.FAILED.value).count()

    draft_cnt = doc_query.filter(Document.workflow_status == WorkflowStatus.DRAFT.value).count()
    awaiting_rev = doc_query.filter(Document.workflow_status == WorkflowStatus.SUBMITTED.value).count()
    approved_cnt = doc_query.filter(Document.workflow_status == WorkflowStatus.APPROVED.value).count()
    rejected_cnt = doc_query.filter(Document.workflow_status == WorkflowStatus.REJECTED.value).count()

    # Recent activity
    hist_query = db.query(WorkflowHistory).join(Document)
    if current_user.role == UserRole.SUBMITTER.value:
        hist_query = hist_query.filter(Document.owner_id == current_user.id)

    recent_entries = (
        hist_query.order_by(desc(WorkflowHistory.created_at))
        .limit(8)
        .all()
    )

    activity_responses = []
    for entry in recent_entries:
        actor_name = entry.actor.name if entry.actor else f"User #{entry.actor_id}"
        activity_responses.append(
            WorkflowHistoryResponse(
                id=entry.id,
                document_id=entry.document_id,
                actor_id=entry.actor_id,
                actor_name=actor_name,
                previous_status=entry.previous_status,
                new_status=entry.new_status,
                reason=entry.reason,
                created_at=entry.created_at
            )
        )

    return DashboardStats(
        total_documents=total_docs,
        pending_processing=pending_proc,
        processing_count=processing_cnt,
        completed_processing=completed_proc,
        failed_processing=failed_proc,
        draft_count=draft_cnt,
        awaiting_review=awaiting_rev,
        approved_count=approved_cnt,
        rejected_count=rejected_cnt,
        recent_activity=activity_responses
    )
