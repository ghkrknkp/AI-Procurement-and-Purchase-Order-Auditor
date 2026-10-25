from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field

# ----------------- User Schemas -----------------
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# ----------------- Extracted Fields -----------------
class ExtractedFieldBase(BaseModel):
    field_name: str
    field_value: Optional[str] = None
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    confidence: Optional[float] = None

class ExtractedFieldUpdate(BaseModel):
    field_name: str
    field_value: Optional[str] = None

class ExtractedFieldResponse(ExtractedFieldBase):
    id: int
    document_id: int
    updated_by: Optional[int] = None
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Purchase Orders -----------------
class PurchaseOrderItemBase(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    purchase_order_id: int

    class Config:
        from_attributes = True

class PurchaseOrderBase(BaseModel):
    purchase_order_number: str
    vendor_name: str
    order_date: Optional[str] = None
    currency: str = "USD"

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate] = []

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    document_id: int
    created_at: datetime
    items: List[PurchaseOrderItemResponse] = []

    class Config:
        from_attributes = True

# ----------------- Validation & Comparison -----------------
class ValidationWarning(BaseModel):
    field: str
    rule: str
    severity: str # "error" | "warning" | "info"
    message: str

class FieldComparison(BaseModel):
    field_name: str
    po_value: Optional[str] = None
    invoice_value: Optional[str] = None
    is_match: bool
    severity: str # "match" | "mismatch" | "warning" | "missing"
    details: Optional[str] = None

class LineItemComparison(BaseModel):
    po_item_desc: Optional[str] = None
    invoice_item_desc: Optional[str] = None
    po_quantity: Optional[float] = None
    invoice_quantity: Optional[float] = None
    quantity_match: bool
    po_unit_price: Optional[float] = None
    invoice_unit_price: Optional[float] = None
    price_match: bool
    po_line_total: Optional[float] = None
    invoice_line_total: Optional[float] = None
    total_match: bool
    status: str # "matched" | "mismatch" | "unmatched_po" | "unmatched_invoice"
    details: Optional[str] = None

class ComparisonResponse(BaseModel):
    overall_match: bool
    has_critical_mismatches: bool
    summary: str
    po_number: Optional[str] = None
    disclaimer: str = "Automated matching results are diagnostic checks and do not replace legal or financial certification."
    field_comparisons: List[FieldComparison] = []
    line_item_comparisons: List[LineItemComparison] = []
    warnings: List[str] = []

# ----------------- Review & Workflow -----------------
class ReviewCommentCreate(BaseModel):
    comment: str

class ReviewCommentResponse(BaseModel):
    id: int
    document_id: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    comment: str
    action: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowTransitionRequest(BaseModel):
    reason: Optional[str] = None

class WorkflowHistoryResponse(BaseModel):
    id: int
    document_id: int
    actor_id: int
    actor_name: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: str
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Document Schemas -----------------
class DocumentBase(BaseModel):
    original_filename: str
    document_type: str = "invoice"

class DocumentResponse(DocumentBase):
    id: int
    owner_id: int
    owner_name: Optional[str] = None
    mime_type: str
    file_size: int
    processing_status: str
    workflow_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    extracted_fields: List[ExtractedFieldResponse] = []
    purchase_orders: List[PurchaseOrderResponse] = []
    review_comments: List[ReviewCommentResponse] = []
    workflow_history: List[WorkflowHistoryResponse] = []
    validation_warnings: List[ValidationWarning] = []

class DocumentFieldsUpdate(BaseModel):
    fields: Dict[str, Optional[str]]

# ----------------- Dashboard -----------------
class DashboardStats(BaseModel):
    total_documents: int
    pending_processing: int
    processing_count: int
    completed_processing: int
    failed_processing: int
    draft_count: int
    awaiting_review: int
    approved_count: int
    rejected_count: int
    recent_activity: List[WorkflowHistoryResponse] = []
