import os
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
try:
    import fitz  # PyMuPDF
except (ImportError, Exception):
    fitz = None

try:
    import pypdf
except ImportError:
    pypdf = None

from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

from app.config import settings

logger = logging.getLogger(__name__)

# Configure tesseract executable if specified in settings
if pytesseract and settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


class ExtractedFieldData:
    def __init__(
        self,
        name: str,
        value: Optional[str],
        source_page: Optional[int] = None,
        source_text: Optional[str] = None,
        confidence: Optional[float] = None
    ):
        self.name = name
        self.value = value
        self.source_page = source_page
        self.source_text = source_text
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.name,
            "field_value": self.value,
            "source_page": self.source_page,
            "source_text": self.source_text,
            "confidence": self.confidence,
        }


class DocumentExtractor:
    """
    Hybrid PDF and Image extraction service using PyMuPDF for digital text
    and pytesseract for scanned PDFs or images.
    Extracts key fields, bounding text snippets, and confidence scores.
    """

    @classmethod
    def extract_text_from_file(cls, file_path: str, mime_type: str) -> List[Tuple[int, str]]:
        """
        Extracts raw text per page. Returns list of (page_num, text).
        """
        pages_content = []
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
            # Attempt PyMuPDF first
            extracted_via_fitz = False
            if fitz:
                try:
                    doc = fitz.open(file_path)
                    for page_idx, page in enumerate(doc):
                        page_text = page.get_text("text").strip()
                        if len(page_text) < 30 and pytesseract:
                            try:
                                pix = page.get_pixmap(dpi=200)
                                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                ocr_text = pytesseract.image_to_string(img).strip()
                                if len(ocr_text) > len(page_text):
                                    page_text = ocr_text
                            except Exception as ocr_err:
                                logger.warning(f"OCR fallback failed on page {page_idx + 1}: {ocr_err}")

                        pages_content.append((page_idx + 1, page_text))
                    doc.close()
                    extracted_via_fitz = True
                except Exception as e:
                    logger.warning(f"PyMuPDF error: {e}. Falling back to pypdf.")

            # Fallback to pure Python pypdf
            if not extracted_via_fitz and pypdf:
                try:
                    reader = pypdf.PdfReader(file_path)
                    for idx, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        pages_content.append((idx + 1, text.strip()))
                except Exception as e:
                    logger.error(f"Error reading PDF with pypdf {file_path}: {e}")
                    raise e

        elif mime_type.startswith("image/") or path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            try:
                if pytesseract:
                    img = Image.open(file_path)
                    text = pytesseract.image_to_string(img).strip()
                    pages_content.append((1, text))
                else:
                    pages_content.append((1, "OCR engine not available. Please install Tesseract OCR."))
            except Exception as e:
                logger.error(f"Error performing OCR on image {file_path}: {e}")
                pages_content.append((1, ""))

        return pages_content

    @classmethod
    def extract_fields(cls, file_path: str, mime_type: str) -> List[ExtractedFieldData]:
        """
        Parses invoice text and identifies standard procurement invoice fields.
        """
        pages = cls.extract_text_from_file(file_path, mime_type)
        if not pages:
            return []

        full_text = "\n".join([text for _, text in pages])
        first_page_text = pages[0][1] if pages else ""
        first_page_num = pages[0][0] if pages else 1

        fields: Dict[str, ExtractedFieldData] = {}

        # 1. Invoice Number
        inv_match = re.search(
            r'(?:invoice\s*(?:#|no|number|num)?[:\s]*|inv[-#:\s]+)([A-Za-z0-9\-_]{3,25})',
            full_text,
            re.IGNORECASE
        )
        if inv_match:
            fields["invoice_number"] = ExtractedFieldData(
                name="invoice_number",
                value=inv_match.group(1).strip(),
                source_page=first_page_num,
                source_text=inv_match.group(0),
                confidence=0.95
            )
        else:
            # Fallback search for common patterns like INV-2024-001
            inv_code = re.search(r'\b(INV-[A-Za-z0-9\-]+)\b', full_text, re.IGNORECASE)
            if inv_code:
                fields["invoice_number"] = ExtractedFieldData(
                    name="invoice_number",
                    value=inv_code.group(1).strip(),
                    source_page=first_page_num,
                    source_text=inv_code.group(0),
                    confidence=0.85
                )
            else:
                fields["invoice_number"] = ExtractedFieldData(
                    name="invoice_number",
                    value="",
                    source_page=first_page_num,
                    source_text="",
                    confidence=0.0
                )

        # 2. Vendor Name
        vendor_match = re.search(
            r'(?:vendor|from|supplier|billed by|seller)[:\s]*([^\n\r,]{3,60})',
            full_text,
            re.IGNORECASE
        )
        if vendor_match:
            vendor_val = vendor_match.group(1).strip()
            fields["vendor_name"] = ExtractedFieldData(
                name="vendor_name",
                value=vendor_val,
                source_page=first_page_num,
                source_text=vendor_match.group(0),
                confidence=0.90
            )
        else:
            # First non-empty lines often contain the vendor header name
            lines = [l.strip() for l in first_page_text.splitlines() if l.strip()]
            candidate = ""
            for line in lines[:5]:
                if not re.search(r'(invoice|tax|date|bill to|phone|email)', line, re.IGNORECASE):
                    candidate = line
                    break
            fields["vendor_name"] = ExtractedFieldData(
                name="vendor_name",
                value=candidate if candidate else "",
                source_page=first_page_num,
                source_text=candidate,
                confidence=0.65 if candidate else 0.0
            )

        # 3. Invoice Date
        date_match = re.search(
            r'(?:invoice\s*date|date|billed\s*on)[:\s]*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}|[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}|[A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
            full_text,
            re.IGNORECASE
        )
        if date_match:
            fields["invoice_date"] = ExtractedFieldData(
                name="invoice_date",
                value=date_match.group(1).strip(),
                source_page=first_page_num,
                source_text=date_match.group(0),
                confidence=0.92
            )
        else:
            fields["invoice_date"] = ExtractedFieldData(
                name="invoice_date",
                value="",
                source_page=first_page_num,
                source_text="",
                confidence=0.0
            )

        # 4. Currency
        curr_val = "USD"
        curr_conf = 0.80
        curr_snippet = "$"
        if re.search(r'\b(EUR|€)\b', full_text):
            curr_val = "EUR"
            curr_snippet = "EUR"
            curr_conf = 0.95
        elif re.search(r'\b(GBP|£)\b', full_text):
            curr_val = "GBP"
            curr_snippet = "GBP"
            curr_conf = 0.95
        elif re.search(r'\b(CAD)\b', full_text):
            curr_val = "CAD"
            curr_snippet = "CAD"
            curr_conf = 0.95
        elif re.search(r'\b(USD|\$)\b', full_text):
            curr_val = "USD"
            curr_snippet = "$"
            curr_conf = 0.95

        fields["currency"] = ExtractedFieldData(
            name="currency",
            value=curr_val,
            source_page=first_page_num,
            source_text=curr_snippet,
            confidence=curr_conf
        )

        # Helper to clean and convert monetary string to clean decimal
        def clean_amount(val_str: str) -> str:
            cleaned = re.sub(r'[^\d.]', '', val_str.replace(',', ''))
            return cleaned

        # 5. Subtotal
        subtotal_match = re.search(
            r'(?:subtotal|sub-total|net\s*amount)[:\s]*[\$€£]?\s*([\d,]+\.?\d*)',
            full_text,
            re.IGNORECASE
        )
        if subtotal_match:
            fields["subtotal"] = ExtractedFieldData(
                name="subtotal",
                value=clean_amount(subtotal_match.group(1)),
                source_page=pages[-1][0],
                source_text=subtotal_match.group(0),
                confidence=0.90
            )
        else:
            fields["subtotal"] = ExtractedFieldData(
                name="subtotal",
                value="",
                source_page=pages[-1][0] if pages else 1,
                source_text="",
                confidence=0.0
            )

        # 6. Tax Amount
        tax_match = re.search(
            r'(?:tax|vat|gst|sales\s*tax)(?:\s*\(\d+%\))?[:\s]*[\$€£]?\s*([\d,]+\.?\d*)',
            full_text,
            re.IGNORECASE
        )
        if tax_match:
            fields["tax_amount"] = ExtractedFieldData(
                name="tax_amount",
                value=clean_amount(tax_match.group(1)),
                source_page=pages[-1][0],
                source_text=tax_match.group(0),
                confidence=0.90
            )
        else:
            fields["tax_amount"] = ExtractedFieldData(
                name="tax_amount",
                value="0.00",
                source_page=pages[-1][0] if pages else 1,
                source_text="Default 0.00",
                confidence=0.50
            )

        # 7. Total Amount
        total_match = re.search(
            r'(?:total\s*(?:amount|due)?|balance\s*due|amount\s*payable)[:\s]*[\$€£]?\s*([\d,]+\.?\d*)',
            full_text,
            re.IGNORECASE
        )
        if total_match:
            fields["total_amount"] = ExtractedFieldData(
                name="total_amount",
                value=clean_amount(total_match.group(1)),
                source_page=pages[-1][0],
                source_text=total_match.group(0),
                confidence=0.95
            )
        else:
            fields["total_amount"] = ExtractedFieldData(
                name="total_amount",
                value="",
                source_page=pages[-1][0] if pages else 1,
                source_text="",
                confidence=0.0
            )

        # 8. Line Items (structured JSON stored as string)
        # Search for lines with [description] [quantity] [unit_price] [line_total]
        line_items = []
        for line in full_text.splitlines():
            # Pattern matching: Item Description ... Qty Price Total
            # e.g.: "Dell XPS 15 Laptop   10   1200.00   12000.00"
            m = re.match(
                r'^(.*?)\s+(\d+(?:\.\d+)?)\s+[\$€£]?\s*(\d+(?:\.\d{2})?)\s+[\$€£]?\s*(\d+(?:\.\d{2})?)$',
                line.strip()
            )
            if m:
                desc = m.group(1).strip()
                if not re.search(r'(total|subtotal|tax|discount|shipping)', desc, re.IGNORECASE):
                    try:
                        line_items.append({
                            "description": desc,
                            "quantity": float(m.group(2)),
                            "unit_price": float(m.group(3)),
                            "line_total": float(m.group(4))
                        })
                    except ValueError:
                        pass

        fields["line_items"] = ExtractedFieldData(
            name="line_items",
            value=json.dumps(line_items) if line_items else "[]",
            source_page=first_page_num,
            source_text=f"Found {len(line_items)} line items",
            confidence=0.88 if line_items else 0.40
        )

        return list(fields.values())
