import pytest
from app.models import Document, WorkflowStatus, ProcessingStatus, WorkflowHistory

def test_workflow_submitter_cannot_approve(client, test_submitter, submitter_token, db_session):
    doc = Document(
        owner_id=test_submitter.id,
        document_type="invoice",
        original_filename="invoice_test.pdf",
        relative_file_path="invoice_test.pdf",
        mime_type="application/pdf",
        file_size=1024,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.SUBMITTED.value
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # Submitter tries to approve
    response = client.post(
        f"/api/v1/documents/{doc.id}/approve",
        json={"reason": "Self-approving"},
        headers={"Authorization": f"Bearer {submitter_token}"}
    )
    assert response.status_code == 403

def test_workflow_reviewer_can_approve(client, test_submitter, reviewer_token, db_session):
    doc = Document(
        owner_id=test_submitter.id,
        document_type="invoice",
        original_filename="invoice_test2.pdf",
        relative_file_path="invoice_test2.pdf",
        mime_type="application/pdf",
        file_size=1024,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.SUBMITTED.value
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    response = client.post(
        f"/api/v1/documents/{doc.id}/approve",
        json={"reason": "Approved by reviewer"},
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert response.status_code == 200
    assert response.json()["workflow_status"] == WorkflowStatus.APPROVED.value

    # Check audit history persisted
    history = db_session.query(WorkflowHistory).filter(WorkflowHistory.document_id == doc.id).all()
    assert any(h.new_status == WorkflowStatus.APPROVED.value for h in history)

def test_workflow_request_corrections(client, test_submitter, reviewer_token, db_session):
    doc = Document(
        owner_id=test_submitter.id,
        document_type="invoice",
        original_filename="invoice_test3.pdf",
        relative_file_path="invoice_test3.pdf",
        mime_type="application/pdf",
        file_size=1024,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.SUBMITTED.value
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    response = client.post(
        f"/api/v1/documents/{doc.id}/request-corrections",
        json={"reason": "Please fix invoice date"},
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert response.status_code == 200
    assert response.json()["workflow_status"] == WorkflowStatus.DRAFT.value

def test_cannot_edit_fields_when_not_draft(client, test_submitter, submitter_token, db_session):
    doc = Document(
        owner_id=test_submitter.id,
        document_type="invoice",
        original_filename="invoice_test4.pdf",
        relative_file_path="invoice_test4.pdf",
        mime_type="application/pdf",
        file_size=1024,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.SUBMITTED.value # In submitted, not draft
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    response = client.patch(
        f"/api/v1/documents/{doc.id}/fields",
        json={"fields": {"total_amount": "999.00"}},
        headers={"Authorization": f"Bearer {submitter_token}"}
    )
    assert response.status_code == 400
