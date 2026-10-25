# AI Procurement and Purchase Order Auditor

> **Edvexa Technical Assessment** — Full-stack AI-assisted document processing system for invoice validation and purchase order reconciliation.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38BDF8)](https://tailwindcss.com)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Getting Started](#getting-started)
6. [Demo Credentials](#demo-credentials)
7. [API Reference](#api-reference)
8. [Running Tests](#running-tests)
9. [Sample Documents](#sample-documents)
10. [Known Limitations](#known-limitations)
11. [AI Usage](#ai-usage)

---

## Overview

This application automates the procurement audit workflow by:

1. **Extracting** invoice data from uploaded PDF or image files using text parsing and OCR
2. **Validating** extracted fields (required fields, date formats, monetary values, duplicate detection)
3. **Comparing** invoices against purchase orders to detect quantity, price, and total discrepancies
4. **Routing** documents through a review workflow (Submitter → Reviewer) with role-based access control
5. **Tracking** a complete audit trail of every action taken on each document

---

## Features

| Feature | Description |
|---------|-------------|
| **Document Upload** | PDF and image (PNG/JPG) upload with drag-and-drop |
| **AI Extraction** | Regex + pypdf text extraction with pytesseract OCR fallback for scanned images |
| **Field Validation** | Required fields, date format, monetary sanity, line-item consistency, duplicate detection |
| **PO Matching** | Line-by-line comparison with configurable tolerance (+/- 0.05) |
| **Mismatch Detection** | Flags quantity, unit price, and total amount discrepancies |
| **Workflow Engine** | DRAFT → SUBMITTED → APPROVED / REJECTED state machine |
| **RBAC** | Submitter role (upload/submit) and Reviewer role (approve/reject/request corrections) |
| **Reviewer Comments** | Comments recorded and visible on each document |
| **Audit Trail** | Full chronological history of every state transition with actor and timestamp |
| **Dashboard** | Summary stats: total docs, pending review, approved, flagged; recent activity chart |
| **JWT Auth** | Secure login with BCrypt-hashed passwords and JWT bearer tokens |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                    │
│  Login │ Dashboard │ Upload │ Document Detail       │
│  (TypeScript + Tailwind CSS + React Router)         │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST (Axios + JWT)
                     ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (:8000)                │
│  /api/v1/auth   /api/v1/documents                  │
│  /api/v1/pos    /api/v1/reviews                    │
│  /api/v1/dashboard                                  │
├────────────┬──────────────┬───────────────────────┤
│  Extractor │  Validator   │  Matcher   │  Audit    │
│  (pypdf +  │  (rules-     │  (PO line  │  (state   │
│   OCR)     │   based)     │   compare) │  machine) │
├────────────┴──────────────┴───────────────────────┤
│          SQLAlchemy ORM + Alembic                  │
│              SQLite (procurement.db)               │
└─────────────────────────────────────────────────────┘
```

### Database Models

```
User ──────────────┐
                   │ uploaded_by / reviewed_by
Document ──────────┼─────────────────────────────┐
  │                │                             │
  ├── ExtractedField (key/value pairs)           │
  ├── PurchaseOrder ──── PurchaseOrderItem       │
  ├── ReviewComment (reviewer notes)             │
  └── WorkflowHistory (audit trail)             │
                                                  │
                   └──────────────────────────────┘
```

---

## Tech Stack

### Backend
| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115 | REST API framework |
| SQLAlchemy | 2.0 | ORM |
| Alembic | 1.14 | Database migrations |
| Pydantic | 2.x | Data validation and settings |
| PyJWT | 2.x | JWT token generation |
| bcrypt | 4.x | Password hashing |
| pypdf | 4.x | PDF text extraction (primary) |
| PyMuPDF | 1.25 | PDF extraction (attempted, DLL-blocked on this system) |
| pytesseract | 0.3 | OCR for scanned images |
| Pillow | 11.x | Image processing |
| reportlab | 4.x | Sample PDF generation |
| pytest | 8.x | Testing framework |
| httpx | 0.28 | Async HTTP client for tests |
| uvicorn | 0.34 | ASGI server |

### Frontend
| Package | Version | Purpose |
|---------|---------|---------|
| React | 18.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 8.x | Build tool |
| Tailwind CSS | 3.4 | Utility-first styling |
| React Router | 6.x | Client-side routing |
| Axios | 1.x | HTTP client |
| Recharts | 2.x | Dashboard charts |
| lucide-react | 0.x | Icons |

---

## Getting Started

### Prerequisites

- **Python 3.11+** (tested on 3.12.1)
- **Node.js 18+** (tested on 24.19.0)
- **Git**
- Tesseract OCR *(optional — for scanned image support)*
  - Windows: download from https://github.com/tesseract-ocr/tesseract/releases
  - Add to PATH

### 1. Clone the repository

```bash
git clone https://github.com/ghkrknkp/AI-Procurement-and-Purchase-Order-Auditor.git
cd AI-Procurement-and-Purchase-Order-Auditor
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/macOS

# Run database migrations
alembic upgrade head

# Seed demo data (creates 2 users + 4 sample documents)
python seed.py

# Start the backend server
uvicorn app.main:app --port 8000 --reload
```

Backend will be running at: http://127.0.0.1:8000

API docs (auto-generated): http://127.0.0.1:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/macOS

# Start development server
npm run dev
```

Frontend will be running at: http://localhost:5173

### 4. Generate Sample Documents (Optional)

```bash
cd backend
python generate_samples.py
```

This creates 4 sample files in `sample_documents/`:
- `sample_invoice_matched.pdf` — Invoice that matches its PO exactly
- `sample_invoice_mismatch_qty.pdf` — Quantity discrepancy (12 chairs vs 10 ordered)
- `sample_invoice_mismatch_price.pdf` — Price discrepancy (unit price mismatch)
- `sample_invoice_scanned.png` — Simulated scanned invoice image

---

## Demo Credentials

| Role | Email | Password |
|------|-------|---------|
| **Submitter** | submitter@edvexa.com | Submitter123! |
| **Reviewer** | reviewer@edvexa.com | Reviewer123! |

### Demo Workflow

1. Log in as **Submitter** → Upload a PDF invoice → Click "Submit for Review"
2. Log in as **Reviewer** → Find the submitted document → Review extracted fields → Approve or Reject

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login and receive JWT token |
| POST | `/auth/register` | Register a new user |
| GET | `/auth/me` | Get current user profile |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/` | List all documents (filtered by role) |
| POST | `/documents/upload` | Upload PDF or image file |
| GET | `/documents/{id}` | Get document details with extracted fields |
| GET | `/documents/{id}/file` | Serve original document file |
| GET | `/documents/{id}/comparison` | Get PO comparison results |
| POST | `/documents/{id}/po` | Attach a purchase order |
| POST | `/documents/{id}/submit` | Submit document for review |

### Reviews (Reviewer only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reviews/queue` | Get documents pending review |
| POST | `/reviews/{id}/approve` | Approve a document |
| POST | `/reviews/{id}/reject` | Reject a document |
| POST | `/reviews/{id}/request-corrections` | Send back for corrections |
| POST | `/reviews/{id}/comment` | Add a comment |

### Purchase Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pos/` | List all purchase orders |
| POST | `/pos/` | Create a new PO |
| GET | `/pos/{id}` | Get PO details with line items |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/stats` | Summary statistics |
| GET | `/dashboard/recent-activity` | Recent document activity |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## Running Tests

```bash
cd backend

# Activate virtual environment first
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # Linux/macOS

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_auth.py -v
pytest tests/test_po_comparison.py -v
```

### Test Coverage

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_auth.py` | 5 | Login, register, JWT, role enforcement, duplicate user |
| `test_extraction_validation.py` | 4 | PDF extraction, field validation, duplicate detection, OCR fallback |
| `test_po_comparison.py` | 3 | Exact match, quantity mismatch, price mismatch |
| `test_workflow_rbac.py` | 4 | Submit, approve, reject, RBAC boundaries |
| **Total** | **16** | **All core workflows** |

---

## Sample Documents

The `sample_documents/` directory contains pre-generated invoices for testing:

```
sample_documents/
├── sample_invoice_matched.pdf          # Clean invoice, matches PO exactly
├── sample_invoice_mismatch_qty.pdf     # 12 chairs ordered vs 10 in PO
├── sample_invoice_mismatch_price.pdf   # Unit price differs from PO
└── sample_invoice_scanned.png          # Simulated scanned invoice (tests OCR path)
```

Upload these via the web UI or use the seed data which auto-attaches them to demo documents.

---

## Project Structure

```
AI Procurement/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models.py            # 7 ORM models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── security.py          # bcrypt + JWT
│   │   ├── dependencies.py      # DI: get_current_user, require_reviewer
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   ├── documents.py
│   │   │   ├── purchase_orders.py
│   │   │   └── reviews.py
│   │   └── services/
│   │       ├── extractor.py     # PDF/image text extraction
│   │       ├── validator.py     # Field validation rules
│   │       ├── matcher.py       # PO comparison engine
│   │       └── audit.py         # Workflow state machine
│   ├── migrations/              # Alembic migrations
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_extraction_validation.py
│   │   ├── test_po_comparison.py
│   │   └── test_workflow_rbac.py
│   ├── uploads/                 # Uploaded files (gitignored)
│   ├── generate_samples.py      # Generates sample PDFs/images
│   ├── seed.py                  # Seeds demo data
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Axios with JWT interceptor
│   │   ├── auth/
│   │   │   ├── AuthContext.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   └── StatusBadge.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DocumentsList.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   └── DocumentDetail.tsx
│   │   ├── types/index.ts
│   │   └── App.tsx
│   ├── tailwind.config.js
│   └── .env.example
├── sample_documents/
├── screenshots/
├── AI_USAGE.md
└── README.md
```

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| **PyMuPDF DLL blocked** | On this Windows system, `_mupdf.pyd` is blocked by App Control policy. System falls back to `pypdf` (pure Python). PyMuPDF is still installed and will work on systems without App Control restrictions. |
| **Tesseract not available** | OCR for scanned images requires Tesseract installed separately. Without it, image uploads fall back to empty extraction. |
| **Regex-based extraction** | Invoice extraction uses regex patterns, not a trained ML model. Extraction accuracy depends on invoice format consistency. |
| **SQLite concurrency** | SQLite is used for simplicity; a production system would use PostgreSQL. |
| **No file size limit** | Upload endpoint does not enforce a hard file size limit (Nginx would handle this in production). |
| **Single machine only** | JWT secret and database are local; no multi-instance support. |

---

## AI Usage

See [AI_USAGE.md](AI_USAGE.md) for a complete, honest disclosure of how AI tools were used in this project.

---

## License

This project was created as a technical assessment for Edvexa. All code is original work produced during the assessment period.
