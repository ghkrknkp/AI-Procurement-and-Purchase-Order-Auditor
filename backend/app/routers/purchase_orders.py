from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, PurchaseOrder, PurchaseOrderItem, User, UserRole, ExtractedField
from app.schemas import (
    PurchaseOrderCreate, PurchaseOrderResponse, ComparisonResponse
)
from app.dependencies import get_current_user
from app.services.matcher import PurchaseOrderMatcher

router = APIRouter(prefix="/documents", tags=["Purchase Orders & Comparison"])

@router.post("/{id}/purchase-order", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def attach_purchase_order(
    id: int,
    po_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Attach or update a purchase order with line items for a document.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Remove existing PO for this document if any to replace
    existing_po = db.query(PurchaseOrder).filter(PurchaseOrder.document_id == doc.id).first()
    if existing_po:
        db.delete(existing_po)
        db.commit()

    # Create new PO
    po = PurchaseOrder(
        document_id=doc.id,
        purchase_order_number=po_in.purchase_order_number,
        vendor_name=po_in.vendor_name,
        order_date=po_in.order_date,
        currency=po_in.currency
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    # Add PO items
    for item_data in po_in.items:
        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            line_total=item_data.line_total
        )
        db.add(item)

    db.commit()
    db.refresh(po)
    return PurchaseOrderResponse.model_validate(po)

@router.get("/{id}/comparison", response_model=ComparisonResponse)
def get_po_comparison(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare document extracted invoice fields against the attached purchase order.
    Returns matched fields, mismatches with expected vs actual, tolerance checks, and warnings.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user.role == UserRole.SUBMITTER.value and doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    po = db.query(PurchaseOrder).filter(PurchaseOrder.document_id == doc.id).first()
    invoice_fields = {f.field_name: f.field_value for f in doc.extracted_fields}

    comparison = PurchaseOrderMatcher.compare(po=po, invoice_fields=invoice_fields)
    return comparison
