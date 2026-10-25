import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

from app.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole, Document, ProcessingStatus, WorkflowStatus,
    ExtractedField, PurchaseOrder, PurchaseOrderItem, ReviewComment, WorkflowHistory
)
from app.security import get_password_hash
from app.config import settings

def seed():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("--- Starting Database Seeding ---")

    # Clear existing data for fresh reproducability
    db.query(WorkflowHistory).delete()
    db.query(ReviewComment).delete()
    db.query(PurchaseOrderItem).delete()
    db.query(PurchaseOrder).delete()
    db.query(ExtractedField).delete()
    db.query(Document).delete()
    db.query(User).delete()
    db.commit()

    # 1. Create Users
    submitter = User(
        name="Alex Submitter",
        email="submitter@edvexa.com",
        password_hash=get_password_hash("Submitter123!"),
        role=UserRole.SUBMITTER.value,
        is_active=True
    )
    reviewer = User(
        name="Morgan Reviewer",
        email="reviewer@edvexa.com",
        password_hash=get_password_hash("Reviewer123!"),
        role=UserRole.REVIEWER.value,
        is_active=True
    )
    db.add(submitter)
    db.add(reviewer)
    db.commit()
    db.refresh(submitter)
    db.refresh(reviewer)
    print(f"Created demo accounts: {submitter.email} (Submitter), {reviewer.email} (Reviewer)")

    # Ensure uploads directory
    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    sample_dir = Path(__file__).resolve().parent.parent / "sample_documents"

    # Helper to copy sample file
    def copy_sample(filename: str) -> str:
        src = sample_dir / filename
        dest_filename = f"seed_{filename}"
        dest = uploads_dir / dest_filename
        if src.exists():
            shutil.copyfile(src, dest)
        else:
            with open(dest, "wb") as f:
                f.write(b"%PDF-1.4 dummy synthetic document content")
        return dest_filename

    # -------------------------------------------------------------
    # Document 1: Clean Matching Invoice (Status: Submitted)
    # -------------------------------------------------------------
    file1 = copy_sample("sample_invoice_matched.pdf")
    doc1 = Document(
        owner_id=submitter.id,
        document_type="invoice",
        original_filename="sample_invoice_matched.pdf",
        relative_file_path=file1,
        mime_type="application/pdf",
        file_size=(uploads_dir / file1).stat().st_size if (uploads_dir / file1).exists() else 15400,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.SUBMITTED.value,
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    db.add(doc1)
    db.commit()
    db.refresh(doc1)

    items1 = [
        {"description": "Enterprise Server Rack", "quantity": 2.0, "unit_price": 4500.00, "line_total": 9000.00},
        {"description": "High-Speed Network Switch", "quantity": 4.0, "unit_price": 750.00, "line_total": 3000.00}
    ]

    fields1 = [
        ExtractedField(document_id=doc1.id, field_name="invoice_number", field_value="INV-2026-101", source_page=1, source_text="Invoice #: INV-2026-101", confidence=0.98, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="vendor_name", field_value="TechCorp Solutions Inc", source_page=1, source_text="TECHCORP SOLUTIONS INC", confidence=0.94, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="invoice_date", field_value="2026-10-15", source_page=1, source_text="Invoice Date: 2026-10-15", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="subtotal", field_value="12000.00", source_page=1, source_text="Subtotal: $12,000.00", confidence=0.92, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="tax_amount", field_value="960.00", source_page=1, source_text="Tax Amount (8%): $960.00", confidence=0.91, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="total_amount", field_value="12960.00", source_page=1, source_text="Total Amount: $12,960.00", confidence=0.97, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="currency", field_value="USD", source_page=1, source_text="$", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc1.id, field_name="line_items", field_value=json.dumps(items1), source_page=1, source_text="Found 2 line items", confidence=0.90, updated_by=submitter.id),
    ]
    db.add_all(fields1)

    # Matching PO
    po1 = PurchaseOrder(
        document_id=doc1.id,
        purchase_order_number="PO-2026-889",
        vendor_name="TechCorp Solutions Inc",
        order_date="2026-10-10",
        currency="USD"
    )
    db.add(po1)
    db.commit()
    db.refresh(po1)

    po_items1 = [
        PurchaseOrderItem(purchase_order_id=po1.id, description="Enterprise Server Rack", quantity=2.0, unit_price=4500.00, line_total=9000.00),
        PurchaseOrderItem(purchase_order_id=po1.id, description="High-Speed Network Switch", quantity=4.0, unit_price=750.00, line_total=3000.00)
    ]
    db.add_all(po_items1)

    # Workflow history
    h1_1 = WorkflowHistory(document_id=doc1.id, actor_id=submitter.id, previous_status=None, new_status=WorkflowStatus.DRAFT.value, reason="Document uploaded and created.", created_at=datetime.utcnow() - timedelta(days=2))
    h1_2 = WorkflowHistory(document_id=doc1.id, actor_id=submitter.id, previous_status=WorkflowStatus.DRAFT.value, new_status=WorkflowStatus.SUBMITTED.value, reason="Verified against PO-2026-889 and submitted for approval.", created_at=datetime.utcnow() - timedelta(days=1, hours=20))
    db.add_all([h1_1, h1_2])

    # -------------------------------------------------------------
    # Document 2: Quantity Mismatch (Status: Submitted)
    # -------------------------------------------------------------
    file2 = copy_sample("sample_invoice_mismatch_qty.pdf")
    doc2 = Document(
        owner_id=submitter.id,
        document_type="invoice",
        original_filename="sample_invoice_mismatch_qty.pdf",
        relative_file_path=file2,
        mime_type="application/pdf",
        file_size=(uploads_dir / file2).stat().st_size if (uploads_dir / file2).exists() else 14200,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.SUBMITTED.value,
        created_at=datetime.utcnow() - timedelta(days=1, hours=10)
    )
    db.add(doc2)
    db.commit()
    db.refresh(doc2)

    items2 = [
        {"description": "Ergonomic Office Chair", "quantity": 12.0, "unit_price": 250.00, "line_total": 3000.00},
        {"description": "Adjustable Standing Desk", "quantity": 5.0, "unit_price": 600.00, "line_total": 3000.00}
    ]

    fields2 = [
        ExtractedField(document_id=doc2.id, field_name="invoice_number", field_value="INV-2026-202", source_page=1, source_text="Invoice #: INV-2026-202", confidence=0.97, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="vendor_name", field_value="Apex Office Supplies Ltd", source_page=1, source_text="APEX OFFICE SUPPLIES LTD", confidence=0.93, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="invoice_date", field_value="2026-10-18", source_page=1, source_text="Invoice Date: 2026-10-18", confidence=0.94, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="subtotal", field_value="6000.00", source_page=1, source_text="Subtotal: $6,000.00", confidence=0.90, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="tax_amount", field_value="300.00", source_page=1, source_text="Tax Amount: $300.00", confidence=0.88, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="total_amount", field_value="6300.00", source_page=1, source_text="Total Amount: $6,300.00", confidence=0.96, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="currency", field_value="USD", source_page=1, source_text="$", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc2.id, field_name="line_items", field_value=json.dumps(items2), source_page=1, source_text="Found 2 line items", confidence=0.90, updated_by=submitter.id),
    ]
    db.add_all(fields2)

    # PO with only 10 chairs authorized
    po2 = PurchaseOrder(
        document_id=doc2.id,
        purchase_order_number="PO-2026-904",
        vendor_name="Apex Office Supplies Ltd",
        order_date="2026-10-12",
        currency="USD"
    )
    db.add(po2)
    db.commit()
    db.refresh(po2)

    po_items2 = [
        PurchaseOrderItem(purchase_order_id=po2.id, description="Ergonomic Office Chair", quantity=10.0, unit_price=250.00, line_total=2500.00), # 10 chairs!
        PurchaseOrderItem(purchase_order_id=po2.id, description="Adjustable Standing Desk", quantity=5.0, unit_price=600.00, line_total=3000.00)
    ]
    db.add_all(po_items2)

    h2_1 = WorkflowHistory(document_id=doc2.id, actor_id=submitter.id, previous_status=None, new_status=WorkflowStatus.DRAFT.value, reason="Invoice received and uploaded.", created_at=datetime.utcnow() - timedelta(days=1, hours=10))
    h2_2 = WorkflowHistory(document_id=doc2.id, actor_id=submitter.id, previous_status=WorkflowStatus.DRAFT.value, new_status=WorkflowStatus.SUBMITTED.value, reason="Submitted for review.", created_at=datetime.utcnow() - timedelta(days=1, hours=8))
    db.add_all([h2_1, h2_2])

    # -------------------------------------------------------------
    # Document 3: Corrections Requested (Status: Draft)
    # -------------------------------------------------------------
    file3 = copy_sample("sample_invoice_mismatch_price.pdf")
    doc3 = Document(
        owner_id=submitter.id,
        document_type="invoice",
        original_filename="sample_invoice_mismatch_price.pdf",
        relative_file_path=file3,
        mime_type="application/pdf",
        file_size=(uploads_dir / file3).stat().st_size if (uploads_dir / file3).exists() else 13800,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.DRAFT.value,
        created_at=datetime.utcnow() - timedelta(days=3)
    )
    db.add(doc3)
    db.commit()
    db.refresh(doc3)

    items3 = [
        {"description": "Developer Workstation Pro", "quantity": 5.0, "unit_price": 2400.00, "line_total": 12000.00}
    ]

    fields3 = [
        ExtractedField(document_id=doc3.id, field_name="invoice_number", field_value="INV-2026-303", source_page=1, source_text="Invoice #: INV-2026-303", confidence=0.96, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="vendor_name", field_value="Global Cloud Hardware LLC", source_page=1, source_text="GLOBAL CLOUD HARDWARE LLC", confidence=0.91, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="invoice_date", field_value="2026-10-20", source_page=1, source_text="Invoice Date: 2026-10-20", confidence=0.93, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="subtotal", field_value="12000.00", source_page=1, source_text="Subtotal: $12,000.00", confidence=0.90, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="tax_amount", field_value="1200.00", source_page=1, source_text="Tax Amount: $1,200.00", confidence=0.89, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="total_amount", field_value="13200.00", source_page=1, source_text="Total Amount: $13,200.00", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="currency", field_value="USD", source_page=1, source_text="$", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc3.id, field_name="line_items", field_value=json.dumps(items3), source_page=1, source_text="Found 1 line item", confidence=0.88, updated_by=submitter.id),
    ]
    db.add_all(fields3)

    po3 = PurchaseOrder(
        document_id=doc3.id,
        purchase_order_number="PO-2026-915",
        vendor_name="Global Cloud Hardware LLC",
        order_date="2026-10-14",
        currency="USD"
    )
    db.add(po3)
    db.commit()
    db.refresh(po3)

    po_items3 = [
        PurchaseOrderItem(purchase_order_id=po3.id, description="Developer Workstation Pro", quantity=5.0, unit_price=2000.00, line_total=10000.00)
    ]
    db.add_all(po_items3)

    comment3 = ReviewComment(
        document_id=doc3.id,
        reviewer_id=reviewer.id,
        comment="Unit price billed at $2,400.00 exceeds agreed PO rate of $2,000.00. Please request a corrected invoice from Global Cloud Hardware.",
        action="requested_corrections",
        created_at=datetime.utcnow() - timedelta(days=2, hours=1)
    )
    db.add(comment3)

    h3_1 = WorkflowHistory(document_id=doc3.id, actor_id=submitter.id, previous_status=None, new_status=WorkflowStatus.DRAFT.value, reason="Initial invoice creation.", created_at=datetime.utcnow() - timedelta(days=3))
    h3_2 = WorkflowHistory(document_id=doc3.id, actor_id=submitter.id, previous_status=WorkflowStatus.DRAFT.value, new_status=WorkflowStatus.SUBMITTED.value, reason="Submitted for PO review.", created_at=datetime.utcnow() - timedelta(days=2, hours=5))
    h3_3 = WorkflowHistory(document_id=doc3.id, actor_id=reviewer.id, previous_status=WorkflowStatus.SUBMITTED.value, new_status=WorkflowStatus.DRAFT.value, reason="Unit price billed at $2,400 exceeds agreed PO rate of $2,000. Corrections requested.", created_at=datetime.utcnow() - timedelta(days=2, hours=1))
    db.add_all([h3_1, h3_2, h3_3])

    # -------------------------------------------------------------
    # Document 4: Approved Historical Invoice (Status: Approved)
    # -------------------------------------------------------------
    doc4 = Document(
        owner_id=submitter.id,
        document_type="invoice",
        original_filename="sample_invoice_matched.pdf",
        relative_file_path=file1,
        mime_type="application/pdf",
        file_size=15400,
        processing_status=ProcessingStatus.COMPLETED.value,
        workflow_status=WorkflowStatus.APPROVED.value,
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    db.add(doc4)
    db.commit()
    db.refresh(doc4)

    fields4 = [
        ExtractedField(document_id=doc4.id, field_name="invoice_number", field_value="INV-2026-088", source_page=1, source_text="INV-2026-088", confidence=0.99, updated_by=submitter.id),
        ExtractedField(document_id=doc4.id, field_name="vendor_name", field_value="TechCorp Solutions Inc", source_page=1, source_text="TechCorp Solutions Inc", confidence=0.98, updated_by=submitter.id),
        ExtractedField(document_id=doc4.id, field_name="invoice_date", field_value="2026-10-01", source_page=1, source_text="2026-10-01", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc4.id, field_name="subtotal", field_value="5000.00", source_page=1, source_text="$5,000.00", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc4.id, field_name="tax_amount", field_value="400.00", source_page=1, source_text="$400.00", confidence=0.95, updated_by=submitter.id),
        ExtractedField(document_id=doc4.id, field_name="total_amount", field_value="5400.00", source_page=1, source_text="$5,400.00", confidence=0.99, updated_by=submitter.id),
        ExtractedField(document_id=doc4.id, field_name="currency", field_value="USD", source_page=1, source_text="$", confidence=0.95, updated_by=submitter.id),
    ]
    db.add_all(fields4)

    comment4 = ReviewComment(
        document_id=doc4.id,
        reviewer_id=reviewer.id,
        comment="All deliverables verified against contract terms and PO. Approved for disbursement.",
        action="approved",
        created_at=datetime.utcnow() - timedelta(days=4)
    )
    db.add(comment4)

    h4_1 = WorkflowHistory(document_id=doc4.id, actor_id=submitter.id, previous_status=None, new_status=WorkflowStatus.DRAFT.value, reason="Invoice uploaded.", created_at=datetime.utcnow() - timedelta(days=5))
    h4_2 = WorkflowHistory(document_id=doc4.id, actor_id=submitter.id, previous_status=WorkflowStatus.DRAFT.value, new_status=WorkflowStatus.SUBMITTED.value, reason="Submitted for approval.", created_at=datetime.utcnow() - timedelta(days=4, hours=12))
    h4_3 = WorkflowHistory(document_id=doc4.id, actor_id=reviewer.id, previous_status=WorkflowStatus.SUBMITTED.value, new_status=WorkflowStatus.APPROVED.value, reason="Approved for disbursement.", created_at=datetime.utcnow() - timedelta(days=4))
    db.add_all([h4_1, h4_2, h4_3])

    db.commit()
    print("--- Database Seeding Complete ---")
    print(f"Sample documents created: 4 (1 Matched Submitted, 1 Qty Mismatch Submitted, 1 Corrections Requested Draft, 1 Approved)")
    print(f"Submitter demo login: submitter@edvexa.com / Submitter123!")
    print(f"Reviewer demo login: reviewer@edvexa.com / Reviewer123!")

if __name__ == "__main__":
    seed()
