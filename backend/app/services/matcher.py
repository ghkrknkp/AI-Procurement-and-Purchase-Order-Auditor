import json
import logging
from typing import Dict, List, Optional, Any
from app.models import PurchaseOrder, PurchaseOrderItem
from app.schemas import (
    ComparisonResponse,
    FieldComparison,
    LineItemComparison
)
from app.config import settings

logger = logging.getLogger(__name__)

class PurchaseOrderMatcher:
    """
    Purchase Order vs Invoice Comparison Engine.
    Performs field-level and line-item-level reconciliations with tolerance checks.
    """

    @classmethod
    def compare(
        cls,
        po: Optional[PurchaseOrder],
        invoice_fields: Dict[str, Optional[str]]
    ) -> ComparisonResponse:
        if not po:
            return ComparisonResponse(
                overall_match=False,
                has_critical_mismatches=False,
                summary="No purchase order associated with this document for comparison.",
                po_number=None,
                field_comparisons=[],
                line_item_comparisons=[],
                warnings=["Attach or enter a Purchase Order to perform 3-way matching and reconciliation."]
            )

        field_comparisons: List[FieldComparison] = []
        line_item_comparisons: List[LineItemComparison] = []
        warnings: List[str] = []
        has_critical = False

        # 1. Compare Vendor Name
        po_vendor = (po.vendor_name or "").strip()
        inv_vendor = (invoice_fields.get("vendor_name") or "").strip()

        vendor_match = False
        vendor_details = None
        if po_vendor and inv_vendor:
            # Case-insensitive substring or exact
            if po_vendor.lower() == inv_vendor.lower():
                vendor_match = True
                vendor_details = "Exact match"
            elif po_vendor.lower() in inv_vendor.lower() or inv_vendor.lower() in po_vendor.lower():
                vendor_match = True
                vendor_details = "Fuzzy substring match"
            else:
                vendor_match = False
                has_critical = True
                vendor_details = f"Vendor name mismatch: expected '{po_vendor}' vs '{inv_vendor}'"
        else:
            vendor_details = "Vendor name missing on invoice or purchase order"

        field_comparisons.append(
            FieldComparison(
                field_name="vendor_name",
                po_value=po_vendor,
                invoice_value=inv_vendor,
                is_match=vendor_match,
                severity="match" if vendor_match else "mismatch",
                details=vendor_details
            )
        )

        # 2. Compare Currency
        po_curr = (po.currency or "USD").upper().strip()
        inv_curr = (invoice_fields.get("currency") or "USD").upper().strip()
        curr_match = (po_curr == inv_curr)
        field_comparisons.append(
            FieldComparison(
                field_name="currency",
                po_value=po_curr,
                invoice_value=inv_curr,
                is_match=curr_match,
                severity="match" if curr_match else "mismatch",
                details="Currencies match" if curr_match else f"Currency mismatch ({po_curr} vs {inv_curr})"
            )
        )
        if not curr_match:
            has_critical = True

        # Parse Invoice Line Items
        raw_items = invoice_fields.get("line_items") or "[]"
        inv_items: List[Dict[str, Any]] = []
        try:
            inv_items = json.loads(raw_items)
            if not isinstance(inv_items, list):
                inv_items = []
        except Exception:
            inv_items = []

        po_items = po.items or []

        # 3. Line Items Comparison
        matched_invoice_indices = set()

        for po_item in po_items:
            best_match_idx = None
            best_match_score = 0

            # Match by description overlap
            po_desc_words = set(po_item.description.lower().split())

            for idx, inv_item in enumerate(inv_items):
                if idx in matched_invoice_indices:
                    continue
                inv_desc_words = set(inv_item.get("description", "").lower().split())
                overlap = len(po_desc_words.intersection(inv_desc_words))
                if overlap > best_match_score:
                    best_match_score = overlap
                    best_match_idx = idx

            if best_match_idx is not None and best_match_score > 0:
                matched_invoice_indices.add(best_match_idx)
                matched_inv = inv_items[best_match_idx]

                inv_qty = float(matched_inv.get("quantity", 0))
                inv_price = float(matched_inv.get("unit_price", 0))
                inv_total = float(matched_inv.get("line_total", 0))

                qty_diff = abs(po_item.quantity - inv_qty)
                price_diff = abs(po_item.unit_price - inv_price)
                total_diff = abs(po_item.line_total - inv_total)

                qty_ok = (qty_diff == 0)
                price_ok = (price_diff <= settings.ROUNDING_TOLERANCE)
                total_ok = (total_diff <= settings.ROUNDING_TOLERANCE)

                item_mismatch = not (qty_ok and price_ok and total_ok)
                if item_mismatch:
                    has_critical = True

                details_parts = []
                if not qty_ok:
                    details_parts.append(f"Quantity difference: PO ordered {po_item.quantity:.0f}, invoice requests {inv_qty:.0f}")
                if not price_ok:
                    details_parts.append(f"Unit price difference: PO expected {po_item.unit_price:.2f}, invoice is {inv_price:.2f}")
                if not total_ok:
                    details_parts.append(f"Line total discrepancy: PO total {po_item.line_total:.2f}, invoice total {inv_total:.2f}")

                line_item_comparisons.append(
                    LineItemComparison(
                        po_item_desc=po_item.description,
                        invoice_item_desc=matched_inv.get("description"),
                        po_quantity=po_item.quantity,
                        invoice_quantity=inv_qty,
                        quantity_match=qty_ok,
                        po_unit_price=po_item.unit_price,
                        invoice_unit_price=inv_price,
                        price_match=price_ok,
                        po_line_total=po_item.line_total,
                        invoice_line_total=inv_total,
                        total_match=total_ok,
                        status="matched" if not item_mismatch else "mismatch",
                        details="; ".join(details_parts) if details_parts else "Item, quantity, and price match PO."
                    )
                )
            else:
                # PO item not found on invoice
                has_critical = True
                line_item_comparisons.append(
                    LineItemComparison(
                        po_item_desc=po_item.description,
                        invoice_item_desc=None,
                        po_quantity=po_item.quantity,
                        invoice_quantity=None,
                        quantity_match=False,
                        po_unit_price=po_item.unit_price,
                        invoice_unit_price=None,
                        price_match=False,
                        po_line_total=po_item.line_total,
                        invoice_line_total=None,
                        total_match=False,
                        status="unmatched_po",
                        details=f"Item ordered in PO ('{po_item.description}') was not detected on invoice."
                    )
                )

        # Unmatched invoice items
        for idx, inv_item in enumerate(inv_items):
            if idx not in matched_invoice_indices:
                warnings.append(
                    f"Additional item detected on invoice not listed in PO: '{inv_item.get('description')}'."
                )
                line_item_comparisons.append(
                    LineItemComparison(
                        po_item_desc=None,
                        invoice_item_desc=inv_item.get("description"),
                        po_quantity=None,
                        invoice_quantity=float(inv_item.get("quantity", 0)),
                        quantity_match=False,
                        po_unit_price=None,
                        invoice_unit_price=float(inv_item.get("unit_price", 0)),
                        price_match=False,
                        po_line_total=None,
                        invoice_line_total=float(inv_item.get("line_total", 0)),
                        total_match=False,
                        status="unmatched_invoice",
                        details="Item is billed on invoice but does not appear on PO."
                    )
                )

        # 4. Compare PO Total vs Invoice Total
        po_total = sum(item.line_total for item in po_items)
        inv_total_raw = invoice_fields.get("total_amount")
        try:
            inv_total = float(str(inv_total_raw).replace(",", "").replace("$", "")) if inv_total_raw else 0.0
        except ValueError:
            inv_total = 0.0

        total_diff = abs(po_total - inv_total)
        total_matches = (total_diff <= settings.ROUNDING_TOLERANCE)

        if not total_matches and po_total > 0:
            has_critical = True
            tot_details = (
                f"Financial Total mismatch! PO total is {po_total:.2f}, while invoice total is {inv_total:.2f}. "
                f"Difference: {total_diff:.2f} (tolerance: {settings.ROUNDING_TOLERANCE})."
            )
        else:
            tot_details = f"Total amounts match within tolerance ({po_total:.2f})."

        field_comparisons.append(
            FieldComparison(
                field_name="total_amount",
                po_value=f"{po_total:.2f}",
                invoice_value=f"{inv_total:.2f}",
                is_match=total_matches,
                severity="match" if total_matches else "mismatch",
                details=tot_details
            )
        )

        overall_match = (not has_critical) and len(field_comparisons) > 0

        summary = (
            "All invoice items and amounts match purchase order specifications."
            if overall_match
            else "Discrepancies identified between invoice and purchase order. Reviewer inspection required."
        )

        return ComparisonResponse(
            overall_match=overall_match,
            has_critical_mismatches=has_critical,
            summary=summary,
            po_number=po.purchase_order_number,
            disclaimer="Automated matching results are diagnostic checks and do not replace legal or financial certification.",
            field_comparisons=field_comparisons,
            line_item_comparisons=line_item_comparisons,
            warnings=warnings
        )
