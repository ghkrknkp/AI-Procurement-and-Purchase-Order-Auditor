from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Document, ExtractedField
from app.schemas import ValidationWarning
from app.config import settings

class DocumentValidator:
    """
    Configurable business validation engine:
    - Required invoice fields
    - Valid invoice date and number
    - Numeric and non-negative monetary values
    - Subtotal, tax, and total consistency check
    - Duplicate invoice numbers across vendor
    - Missing or low-confidence extracted values
    """

    @classmethod
    def validate_document(
        cls,
        document_id: int,
        fields_dict: Dict[str, Optional[str]],
        field_confidences: Optional[Dict[str, Optional[float]]] = None,
        db: Optional[Session] = None
    ) -> List[ValidationWarning]:
        warnings: List[ValidationWarning] = []
        field_confidences = field_confidences or {}

        # 1. Required invoice fields
        required_fields = ["invoice_number", "vendor_name", "invoice_date", "total_amount"]
        for req in required_fields:
            val = fields_dict.get(req)
            if not val or not str(val).strip():
                warnings.append(
                    ValidationWarning(
                        field=req,
                        rule="required_field",
                        severity="error",
                        message=f"Missing required field: '{req.replace('_', ' ').title()}'."
                    )
                )

        # 2. Date validation
        inv_date = fields_dict.get("invoice_date")
        if inv_date and str(inv_date).strip():
            date_parsed = False
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y"):
                try:
                    dt = datetime.strptime(str(inv_date).strip(), fmt)
                    date_parsed = True
                    if dt.year > datetime.utcnow().year + 1:
                        warnings.append(
                            ValidationWarning(
                                field="invoice_date",
                                rule="future_date",
                                severity="warning",
                                message=f"Invoice date {inv_date} appears to be too far in the future."
                            )
                        )
                    break
                except ValueError:
                    continue
            if not date_parsed:
                warnings.append(
                    ValidationWarning(
                        field="invoice_date",
                        rule="invalid_date_format",
                        severity="warning",
                        message=f"Date '{inv_date}' could not be validated against standard date formats."
                    )
                )

        # 3. Numeric and non-negative monetary values
        monetary_fields = ["subtotal", "tax_amount", "total_amount"]
        parsed_monetary: Dict[str, float] = {}

        for mf in monetary_fields:
            raw_val = fields_dict.get(mf)
            if raw_val is not None and str(raw_val).strip() != "":
                try:
                    num = float(str(raw_val).replace(",", "").replace("$", ""))
                    if num < 0:
                        warnings.append(
                            ValidationWarning(
                                field=mf,
                                rule="non_negative",
                                severity="error",
                                message=f"{mf.replace('_', ' ').title()} cannot be negative ({num})."
                            )
                        )
                    else:
                        parsed_monetary[mf] = num
                except ValueError:
                    warnings.append(
                        ValidationWarning(
                            field=mf,
                            rule="numeric_value",
                            severity="error",
                            message=f"{mf.replace('_', ' ').title()} must be a valid numeric amount."
                        )
                    )

        # 4. Subtotal, tax, and total consistency check
        if "total_amount" in parsed_monetary and "subtotal" in parsed_monetary:
            subtotal = parsed_monetary["subtotal"]
            tax = parsed_monetary.get("tax_amount", 0.0)
            total = parsed_monetary["total_amount"]
            expected_total = round(subtotal + tax, 2)
            actual_total = round(total, 2)
            diff = abs(expected_total - actual_total)

            if diff > settings.ROUNDING_TOLERANCE:
                warnings.append(
                    ValidationWarning(
                        field="total_amount",
                        rule="monetary_consistency",
                        severity="error",
                        message=(
                            f"Mathematical discrepancy: Subtotal ({subtotal:.2f}) + Tax ({tax:.2f}) = "
                            f"{expected_total:.2f}, but Total is {actual_total:.2f} (Difference: {diff:.2f})."
                        )
                    )
                )

        # 5. Duplicate invoice check
        if db and fields_dict.get("invoice_number") and fields_dict.get("vendor_name"):
            inv_num = fields_dict["invoice_number"].strip()
            vendor = fields_dict["vendor_name"].strip()
            
            # Check other documents
            dupes = (
                db.query(ExtractedField.document_id)
                .filter(
                    ExtractedField.document_id != document_id,
                    ExtractedField.field_name == "invoice_number",
                    ExtractedField.field_value == inv_num
                )
                .all()
            )
            for d in dupes:
                other_doc_id = d[0]
                vendor_field = (
                    db.query(ExtractedField)
                    .filter(
                        ExtractedField.document_id == other_doc_id,
                        ExtractedField.field_name == "vendor_name",
                        ExtractedField.field_value == vendor
                    )
                    .first()
                )
                if vendor_field:
                    warnings.append(
                        ValidationWarning(
                            field="invoice_number",
                            rule="duplicate_invoice",
                            severity="warning",
                            message=f"Possible duplicate invoice! Invoice #{inv_num} for vendor '{vendor}' was previously uploaded in Document #{other_doc_id}."
                        )
                    )
                    break

        # 6. Low confidence warnings
        for field, conf in field_confidences.items():
            if conf is not None and conf < 0.70:
                warnings.append(
                    ValidationWarning(
                        field=field,
                        rule="low_confidence",
                        severity="info",
                        message=f"Extracted field '{field.replace('_', ' ').title()}' has low confidence ({int(conf * 100)}%). Please review carefully."
                    )
                )

        return warnings
