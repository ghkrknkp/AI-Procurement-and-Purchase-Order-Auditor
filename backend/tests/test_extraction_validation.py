import pytest
from app.services.validator import DocumentValidator
from app.services.extractor import DocumentExtractor

def test_validation_missing_required_fields():
    fields = {
        "invoice_number": "",
        "vendor_name": "Test Vendor",
        "invoice_date": "",
        "total_amount": "100.00"
    }
    warnings = DocumentValidator.validate_document(document_id=1, fields_dict=fields)
    rules_triggered = [w.rule for w in warnings]
    assert "required_field" in rules_triggered

def test_validation_monetary_consistency():
    # Subtotal 100 + Tax 10 != Total 150
    fields = {
        "invoice_number": "INV-001",
        "vendor_name": "Acme Corp",
        "invoice_date": "2026-10-15",
        "subtotal": "100.00",
        "tax_amount": "10.00",
        "total_amount": "150.00"
    }
    warnings = DocumentValidator.validate_document(document_id=1, fields_dict=fields)
    rules_triggered = [w.rule for w in warnings]
    assert "monetary_consistency" in rules_triggered

def test_validation_monetary_pass_within_tolerance():
    # Subtotal 100.00 + Tax 8.00 == Total 108.00
    fields = {
        "invoice_number": "INV-001",
        "vendor_name": "Acme Corp",
        "invoice_date": "2026-10-15",
        "subtotal": "100.00",
        "tax_amount": "8.00",
        "total_amount": "108.00"
    }
    warnings = DocumentValidator.validate_document(document_id=1, fields_dict=fields)
    assert not any(w.rule == "monetary_consistency" for w in warnings)

def test_validation_negative_monetary_value():
    fields = {
        "invoice_number": "INV-001",
        "vendor_name": "Acme Corp",
        "invoice_date": "2026-10-15",
        "subtotal": "-50.00",
        "tax_amount": "5.00",
        "total_amount": "55.00"
    }
    warnings = DocumentValidator.validate_document(document_id=1, fields_dict=fields)
    assert any(w.rule == "non_negative" for w in warnings)
