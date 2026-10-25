export interface User {
  id: number;
  name: string;
  email: string;
  role: 'submitter' | 'reviewer';
  is_active: boolean;
  created_at: string;
}

export interface ExtractedField {
  id: number;
  document_id: number;
  field_name: string;
  field_value: string | null;
  source_page: number | null;
  source_text: string | null;
  confidence: number | null;
  updated_by: number | null;
  updated_at: string;
}

export interface PurchaseOrderItem {
  id: number;
  purchase_order_id: number;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface PurchaseOrder {
  id: number;
  document_id: number;
  purchase_order_number: string;
  vendor_name: string;
  order_date?: string;
  currency: string;
  created_at: string;
  items: PurchaseOrderItem[];
}

export interface ValidationWarning {
  field: string;
  rule: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
}

export interface FieldComparison {
  field_name: string;
  po_value: string | null;
  invoice_value: string | null;
  is_match: boolean;
  severity: 'match' | 'mismatch' | 'warning' | 'missing';
  details: string | null;
}

export interface LineItemComparison {
  po_item_desc: string | null;
  invoice_item_desc: string | null;
  po_quantity: number | null;
  invoice_quantity: number | null;
  quantity_match: boolean;
  po_unit_price: number | null;
  invoice_unit_price: number | null;
  price_match: boolean;
  po_line_total: number | null;
  invoice_line_total: number | null;
  total_match: boolean;
  status: 'matched' | 'mismatch' | 'unmatched_po' | 'unmatched_invoice';
  details: string | null;
}

export interface ComparisonResponse {
  overall_match: boolean;
  has_critical_mismatches: boolean;
  summary: string;
  po_number: string | null;
  disclaimer: string;
  field_comparisons: FieldComparison[];
  line_item_comparisons: LineItemComparison[];
  warnings: string[];
}

export interface ReviewComment {
  id: number;
  document_id: number;
  reviewer_id: number;
  reviewer_name: string;
  comment: string;
  action: string | null;
  created_at: string;
}

export interface WorkflowHistory {
  id: number;
  document_id: number;
  actor_id: number;
  actor_name: string;
  previous_status: string | null;
  new_status: string;
  reason: string | null;
  created_at: string;
}

export interface DocumentItem {
  id: number;
  owner_id: number;
  owner_name: string;
  document_type: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  workflow_status: 'draft' | 'submitted' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentItem {
  extracted_fields: ExtractedField[];
  purchase_orders: PurchaseOrder[];
  review_comments: ReviewComment[];
  workflow_history: WorkflowHistory[];
  validation_warnings: ValidationWarning[];
}

export interface DashboardStats {
  total_documents: number;
  pending_processing: number;
  processing_count: number;
  completed_processing: number;
  failed_processing: number;
  draft_count: number;
  awaiting_review: number;
  approved_count: number;
  rejected_count: number;
  recent_activity: WorkflowHistory[];
}
