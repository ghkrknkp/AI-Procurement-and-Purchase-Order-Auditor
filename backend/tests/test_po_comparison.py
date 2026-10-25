import json
import pytest
from app.models import PurchaseOrder, PurchaseOrderItem
from app.services.matcher import PurchaseOrderMatcher

def test_po_comparison_clean_match():
    po = PurchaseOrder(
        purchase_order_number="PO-100",
        vendor_name="Tech Solutions",
        order_date="2026-10-01",
        currency="USD"
    )
    po.items = [
        PurchaseOrderItem(description="Laptop", quantity=5.0, unit_price=1000.0, line_total=5000.0)
    ]

    invoice_fields = {
        "vendor_name": "Tech Solutions",
        "currency": "USD",
        "total_amount": "5000.00",
        "line_items": json.dumps([
            {"description": "Laptop", "quantity": 5.0, "unit_price": 1000.0, "line_total": 5000.0}
        ])
    }

    result = PurchaseOrderMatcher.compare(po, invoice_fields)
    assert result.overall_match is True
    assert result.has_critical_mismatches is False
    assert len(result.line_item_comparisons) == 1
    assert result.line_item_comparisons[0].quantity_match is True

def test_po_comparison_quantity_mismatch():
    po = PurchaseOrder(
        purchase_order_number="PO-200",
        vendor_name="Office Express",
        currency="USD"
    )
    po.items = [
        PurchaseOrderItem(description="Office Chair", quantity=10.0, unit_price=200.0, line_total=2000.0)
    ]

    # Invoiced 12 chairs instead of 10
    invoice_fields = {
        "vendor_name": "Office Express",
        "currency": "USD",
        "total_amount": "2400.00",
        "line_items": json.dumps([
            {"description": "Office Chair", "quantity": 12.0, "unit_price": 200.0, "line_total": 2400.0}
        ])
    }

    result = PurchaseOrderMatcher.compare(po, invoice_fields)
    assert result.overall_match is False
    assert result.has_critical_mismatches is True
    assert result.line_item_comparisons[0].quantity_match is False
    assert "Quantity difference" in result.line_item_comparisons[0].details

def test_po_comparison_price_mismatch():
    po = PurchaseOrder(
        purchase_order_number="PO-300",
        vendor_name="Cloud Servers Ltd",
        currency="USD"
    )
    po.items = [
        PurchaseOrderItem(description="Cloud Server", quantity=1.0, unit_price=1500.0, line_total=1500.0)
    ]

    # Invoiced at $1800
    invoice_fields = {
        "vendor_name": "Cloud Servers Ltd",
        "currency": "USD",
        "total_amount": "1800.00",
        "line_items": json.dumps([
            {"description": "Cloud Server", "quantity": 1.0, "unit_price": 1800.0, "line_total": 1800.0}
        ])
    }

    result = PurchaseOrderMatcher.compare(po, invoice_fields)
    assert result.overall_match is False
    assert result.has_critical_mismatches is True
    assert result.line_item_comparisons[0].price_match is False
