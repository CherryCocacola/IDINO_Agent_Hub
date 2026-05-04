# Portfolio Service

Student portfolio management service for IDINO Career system.

## Overview

This service manages student portfolio items including GitHub repositories, Notion pages, blogs, websites, projects, papers, and other artifacts.

## Port

- **8016**

## Features

- CRUD operations for portfolio items
- Multiple artifact types support
- Primary portfolio marking
- Portfolio summary statistics
- Student verification via Student Service

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/portfolio/types` | Get available portfolio types |
| GET | `/portfolio/student/{student_id}` | Get all portfolio items for a student |
| GET | `/portfolio/student/{student_id}/summary` | Get portfolio summary statistics |
| GET | `/portfolio/{portfolio_id}` | Get specific portfolio item |
| POST | `/portfolio` | Create new portfolio item |
| PUT | `/portfolio/{portfolio_id}` | Update portfolio item |
| DELETE | `/portfolio/{portfolio_id}` | Delete portfolio item |
| PUT | `/portfolio/{portfolio_id}/primary` | Set as primary portfolio |

## Artifact Types

- `github` - GitHub repository or profile
- `notion` - Notion page or workspace
- `blog` - Personal or technical blog
- `website` - Personal portfolio website
- `project` - Project documentation or demo
- `paper` - Research paper or publication
- `video` - Video content or presentation
- `document` - Document or report
- `other` - Other portfolio item

## Installation

```bash
cd services/portfolio-service
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Running

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8016 --reload
```

## API Documentation

- Swagger UI: http://localhost:8016/docs
- ReDoc: http://localhost:8016/redoc

## Database

Uses `tb_portfolio` table in `idino_career` schema.

```sql
CREATE TABLE tb_portfolio (
    portfolio_id UUID PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    artifact_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_dt TIMESTAMP
);
```

## Example Requests

### Create Portfolio Item

```bash
curl -X POST http://localhost:8016/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "2021010001",
    "artifact_type": "github",
    "title": "My GitHub Profile",
    "url": "https://github.com/username",
    "description": "Personal projects and contributions",
    "is_primary": true
  }'
```

### Get Student Portfolios

```bash
curl http://localhost:8016/portfolio/student/2021010001
```

### Set Primary Portfolio

```bash
curl -X PUT http://localhost:8016/portfolio/{portfolio_id}/primary
```
