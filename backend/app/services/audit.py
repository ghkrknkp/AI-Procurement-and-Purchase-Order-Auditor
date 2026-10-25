from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    Document, User, UserRole, WorkflowStatus, WorkflowHistory, ReviewComment
)

class WorkflowService:
    """
    Manages workflow state transitions, permission enforcement, and audit history.
    """

    VALID_TRANSITIONS = {
        WorkflowStatus.DRAFT.value: [WorkflowStatus.SUBMITTED.value],
        WorkflowStatus.SUBMITTED.value: [
            WorkflowStatus.APPROVED.value,
            WorkflowStatus.REJECTED.value,
            WorkflowStatus.DRAFT.value # Requested corrections
        ],
        WorkflowStatus.APPROVED.value: [], # Terminal
        WorkflowStatus.REJECTED.value: [WorkflowStatus.DRAFT.value], # Allow restart if reviewer reopened
    }

    @classmethod
    def transition(
        cls,
        db: Session,
        document: Document,
        actor: User,
        target_status: str,
        reason: Optional[str] = None
    ) -> WorkflowHistory:
        current_status = document.workflow_status

        # 1. State machine validation
        allowed_next = cls.VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed_next:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow transition from '{current_status}' to '{target_status}'."
            )

        # 2. RBAC rules
        if target_status == WorkflowStatus.SUBMITTED.value:
            # Submitter submits their own draft
            if actor.role != UserRole.SUBMITTER.value and actor.role != UserRole.REVIEWER.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only document submitters can submit documents for review."
                )
            if actor.id != document.owner_id and actor.role != UserRole.REVIEWER.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own this document."
                )

        elif target_status in [WorkflowStatus.APPROVED.value, WorkflowStatus.REJECTED.value]:
            if actor.role != UserRole.REVIEWER.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only users with Reviewer role can approve or reject documents."
                )

        elif target_status == WorkflowStatus.DRAFT.value and current_status == WorkflowStatus.SUBMITTED.value:
            # Request corrections
            if actor.role != UserRole.REVIEWER.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only reviewers can return a submitted document for corrections."
                )
            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A reason must be provided when requesting corrections."
                )

        # 3. Apply state and persist in atomic transaction
        history_entry = WorkflowHistory(
            document_id=document.id,
            actor_id=actor.id,
            previous_status=current_status,
            new_status=target_status,
            reason=reason
        )
        document.workflow_status = target_status
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        db.refresh(document)

        return history_entry

    @classmethod
    def add_comment(
        cls,
        db: Session,
        document: Document,
        reviewer: User,
        comment_text: str,
        action: Optional[str] = "commented"
    ) -> ReviewComment:
        if reviewer.role != UserRole.REVIEWER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only reviewers can post review comments."
            )

        comment = ReviewComment(
            document_id=document.id,
            reviewer_id=reviewer.id,
            comment=comment_text,
            action=action
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
