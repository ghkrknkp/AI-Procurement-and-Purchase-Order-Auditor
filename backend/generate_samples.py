import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_documents"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def create_pdf_invoice(filepath: Path, inv_num: str, vendor: str, date: str, items: list, subtotal: float, tax: float, total: float, notes: str = ""):
    c = canvas.Canvas(str(filepath), pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.drawString(50, height - 60, vendor.upper())

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#4b5563"))
    c.drawString(50, height - 76, "123 Business Avenue, Suite 400, Tech Park")
    c.drawString(50, height - 90, "Phone: +1 (555) 019-2834 | Email: billing@vendor.com")

    # Invoice details top right
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.drawRightString(width - 50, height - 60, "INVOICE")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawRightString(width - 50, height - 80, f"Invoice #: {inv_num}")
    c.drawRightString(width - 50, height - 95, f"Invoice Date: {date}")
    c.drawRightString(width - 50, height - 110, "Payment Terms: Net 30")

    # Divider
    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(1)
    c.line(50, height - 125, width - 50, height - 125)

    # Billed to
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#374151"))
    c.drawString(50, height - 150, "BILLED TO:")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(50, height - 165, "Edvexa Enterprise Solutions Inc.")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#4b5563"))
    c.drawString(50, height - 180, "Department of Procurement & Supply Chain")
    c.drawString(50, height - 193, "789 Corporate Plaza, New York, NY 10001")

    # Table Header
    y = height - 230
    c.setFillColor(colors.HexColor("#f3f4f6"))
    c.rect(50, y, width - 100, 24, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1f2937"))
    c.drawString(60, y + 7, "Item Description")
    c.drawString(320, y + 7, "Qty")
    c.drawString(380, y + 7, "Unit Price")
    c.drawRightString(width - 60, y + 7, "Line Total")

    # Table Rows
    y -= 22
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#111827"))

    for item in items:
        desc = item["description"]
        qty = item["quantity"]
        unit = item["unit_price"]
        ltot = item["line_total"]

        c.drawString(60, y + 5, f"{desc}")
        c.drawString(325, y + 5, f"{qty}")
        c.drawString(380, y + 5, f"${unit:,.2f}")
        c.drawRightString(width - 60, y + 5, f"${ltot:,.2f}")

        c.setStrokeColor(colors.HexColor("#f3f4f6"))
        c.setLineWidth(0.5)
        c.line(50, y, width - 50, y)
        y -= 22

    # Totals Section
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(360, y, "Subtotal:")
    c.drawRightString(width - 60, y, f"${subtotal:,.2f}")

    y -= 18
    c.drawString(360, y, "Tax Amount (8%):")
    c.drawRightString(width - 60, y, f"${tax:,.2f}")

    y -= 24
    c.setFillColor(colors.HexColor("#ecfdf5"))
    c.rect(350, y - 6, width - 400, 24, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#065f46"))
    c.drawString(360, y, "Total Amount:")
    c.drawRightString(width - 60, y, f"${total:,.2f}")

    if notes:
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#6b7280"))
        c.drawString(50, 60, f"Notes: {notes}")

    c.showPage()
    c.save()

def create_image_invoice(filepath: Path):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.text((50, 50), "GLOBAL SUPPLIES CO.", fill=(20, 40, 80))
    draw.text((50, 75), "Vendor: Global Supplies Co.", fill=(50, 50, 50))
    draw.text((500, 50), "INVOICE", fill=(20, 40, 80))
    draw.text((500, 80), "Invoice #: INV-2026-IMAGE", fill=(50, 50, 50))
    draw.text((500, 105), "Invoice Date: 2026-10-22", fill=(50, 50, 50))

    draw.line([(50, 140), (750, 140)], fill=(200, 200, 200), width=2)
    draw.text((50, 160), "Billed To: Edvexa Procurement Corp", fill=(50, 50, 50))

    draw.rectangle([(50, 200), (750, 230)], fill=(240, 244, 250))
    draw.text((60, 208), "Item Description", fill=(30, 30, 30))
    draw.text((450, 208), "Qty", fill=(30, 30, 30))
    draw.text((550, 208), "Unit Price", fill=(30, 30, 30))
    draw.text((650, 208), "Line Total", fill=(30, 30, 30))

    # Item
    draw.text((60, 250), "Heavy Duty Network Cable Reel", fill=(50, 50, 50))
    draw.text((460, 250), "4", fill=(50, 50, 50))
    draw.text((550, 250), "$120.00", fill=(50, 50, 50))
    draw.text((650, 250), "$480.00", fill=(50, 50, 50))

    draw.line([(50, 280), (750, 280)], fill=(220, 220, 220), width=1)

    draw.text((500, 320), "Subtotal: $480.00", fill=(50, 50, 50))
    draw.text((500, 345), "Tax: $38.40", fill=(50, 50, 50))
    draw.text((500, 380), "Total Amount: $518.40", fill=(10, 80, 20))

    img.save(str(filepath))

def generate_all():
    # 1. Perfectly Matched
    create_pdf_invoice(
        filepath=SAMPLE_DIR / "sample_invoice_matched.pdf",
        inv_num="INV-2026-101",
        vendor="TechCorp Solutions Inc",
        date="2026-10-15",
        items=[
            {"description": "Enterprise Server Rack", "quantity": 2, "unit_price": 4500.00, "line_total": 9000.00},
            {"description": "High-Speed Network Switch", "quantity": 4, "unit_price": 750.00, "line_total": 3000.00}
        ],
        subtotal=12000.00,
        tax=960.00,
        total=12960.00,
        notes="Purchase Order Reference: PO-2026-889"
    )

    # 2. Quantity Mismatch
    create_pdf_invoice(
        filepath=SAMPLE_DIR / "sample_invoice_mismatch_qty.pdf",
        inv_num="INV-2026-202",
        vendor="Apex Office Supplies Ltd",
        date="2026-10-18",
        items=[
            {"description": "Ergonomic Office Chair", "quantity": 12, "unit_price": 250.00, "line_total": 3000.00}, # PO specified 10!
            {"description": "Adjustable Standing Desk", "quantity": 5, "unit_price": 600.00, "line_total": 3000.00}
        ],
        subtotal=6000.00,
        tax=300.00,
        total=6300.00,
        notes="PO Reference: PO-2026-904 (Warning: Invoiced 12 chairs instead of authorized 10)"
    )

    # 3. Unit Price Mismatch
    create_pdf_invoice(
        filepath=SAMPLE_DIR / "sample_invoice_mismatch_price.pdf",
        inv_num="INV-2026-303",
        vendor="Global Cloud Hardware LLC",
        date="2026-10-20",
        items=[
            {"description": "Developer Workstation Pro", "quantity": 5, "unit_price": 2400.00, "line_total": 12000.00} # PO was 2000.00!
        ],
        subtotal=12000.00,
        tax=1200.00,
        total=13200.00,
        notes="PO Reference: PO-2026-915 (Warning: Unit price billed at $2,400 vs PO $2,000)"
    )

    # 4. Scanned Image
    create_image_invoice(SAMPLE_DIR / "sample_invoice_scanned.png")

    print(f"Sample invoices generated successfully in: {SAMPLE_DIR}")

if __name__ == "__main__":
    generate_all()
