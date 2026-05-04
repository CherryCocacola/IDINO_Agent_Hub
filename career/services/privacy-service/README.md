# Privacy Service

Data Subject Rights Management API for GDPR/PIPA Compliance.

## Overview

This service handles all privacy-related operations including:
- Data Subject Request Management
- Right to Access (GDPR Article 15)
- Right to Data Portability (GDPR Article 20)
- Right to Erasure (GDPR Article 17)
- Consent Management

## Port

- **Port**: 8017

## API Endpoints

### Data Subject Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/privacy/requests` | Create a new data subject request |
| GET | `/privacy/requests/student/{student_id}` | Get all requests for a student |
| GET | `/privacy/requests/{request_id}` | Get status of a specific request |

### Right to Access

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/privacy/access/{student_id}` | Process data access request |

### Right to Data Portability

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/privacy/export/{student_id}` | Export personal data (JSON/CSV) |

### Right to Erasure

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/privacy/erasure/{student_id}` | Process data erasure request |

### Consent Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/privacy/consent` | Record a consent decision |
| GET | `/privacy/consent/student/{student_id}` | Get all consents for a student |
| DELETE | `/privacy/consent/{student_id}/{consent_type}` | Revoke a specific consent |

### Information Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/privacy/rights` | Get information about data subject rights |
| GET | `/privacy/consent-types` | Get available consent types |

## Request Types

- `access` - Right to Access (Article 15)
- `rectification` - Right to Rectification (Article 16)
- `erasure` - Right to Erasure (Article 17)
- `portability` - Right to Data Portability (Article 20)
- `restriction` - Right to Restriction (Article 18)
- `objection` - Right to Object (Article 21)

## Consent Types

- `marketing` - Marketing communications
- `analytics` - Analytics and tracking
- `third_party` - Third-party data sharing
- `ai_processing` - AI-based processing
- `data_retention` - Extended data retention
- `research` - Research purposes

## Data Categories

Data is organized into the following categories:
- `personal_info` - Basic personal information
- `academic_records` - Academic history and grades
- `competency_data` - Skills and competency assessments
- `activity_history` - Platform activity logs
- `portfolio_items` - Portfolio artifacts
- `consent_records` - Consent history

## Compliance Notes

### GDPR Requirements
- 30-day processing deadline for all requests
- Clear categorization of personal data
- Transparent processing purposes disclosure
- Data portability in machine-readable format

### Data Retention
- Academic records are retained per Higher Education Act
- Retained data is anonymized during erasure
- 5-year default retention period for audit purposes

### Legal Basis
- Some data may be retained for legal/regulatory compliance
- Academic achievements are anonymized but not fully deleted
- Consent records are maintained for audit trail

## Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run service
python -m app.main
# Or
uvicorn app.main:app --host 0.0.0.0 --port 8017 --reload
```

## Environment Variables

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=idino_career
DB_USER=postgres
DB_PASSWORD=your_password
DB_SCHEMA=idino_career
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8017
```

## Example Usage

### Create Data Subject Request
```bash
curl -X POST http://localhost:8017/privacy/requests \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU001",
    "request_type": "access",
    "description": "Request for all my personal data",
    "contact_email": "student@example.com"
  }'
```

### Request Data Access
```bash
curl -X POST http://localhost:8017/privacy/access/STU001
```

### Export Data
```bash
curl -X POST "http://localhost:8017/privacy/export/STU001?format=json"
```

### Record Consent
```bash
curl -X POST http://localhost:8017/privacy/consent \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU001",
    "consent_type": "marketing",
    "granted": true,
    "purpose": "Email newsletters"
  }'
```

### Revoke Consent
```bash
curl -X DELETE http://localhost:8017/privacy/consent/STU001/marketing
```
