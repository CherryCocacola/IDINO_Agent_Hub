# WorkNet Diagnosis Service

Integration service for Korea WorkNet (워크넷) vocational diagnosis tests.

## Overview

This service provides seamless integration with the Korean government's WorkNet platform for comprehensive vocational assessments and career guidance.

## Port

- **Port**: 8018

## Available Diagnosis Types

| Type | Korean Name | Duration | Description |
|------|-------------|----------|-------------|
| `aptitude` | 직업적성검사 | 50 min | 9 aptitude factors assessment |
| `interest` | 직업흥미검사 | 30 min | Holland RIASEC model analysis |
| `values` | 직업가치관검사 | 25 min | Work values assessment |
| `personality` | 성인용 직업성격검사 | 40 min | MBTI-based career matching |
| `entrepreneurship` | 창업적성검사 | 35 min | Startup readiness evaluation |
| `career_maturity` | 진로성숙도검사 | 30 min | Career decision readiness |

## API Endpoints

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/worknet/sessions` | Create a new diagnosis session |
| GET | `/worknet/sessions/{session_id}` | Get session status |
| GET | `/worknet/sessions/student/{student_id}` | Get all sessions for a student |
| PATCH | `/worknet/sessions/{session_id}/status` | Update session status |

### Callback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/worknet/callback` | Handle WorkNet callback with results |

### Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/worknet/results/{result_id}` | Get specific result |
| GET | `/worknet/results/student/{student_id}` | Get all results for a student |
| GET | `/worknet/results/student/{student_id}/latest` | Get latest result per type |

### Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/worknet/summary/{student_id}` | Get comprehensive diagnosis summary |

### Information

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/worknet/diagnosis-types` | Get available diagnosis types |
| GET | `/worknet/info` | Get WorkNet integration info |

## Integration Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Application   │     │  WorkNet Svc    │     │    WorkNet      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Create Session     │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │ 2. Return WorkNet URL │                       │
         │<──────────────────────│                       │
         │                       │                       │
         │ 3. Redirect User      │                       │
         │───────────────────────────────────────────────>
         │                       │                       │
         │                       │  4. Complete Test     │
         │                       │<──────────────────────│
         │                       │                       │
         │                       │  5. Callback with     │
         │                       │     Results           │
         │                       │<──────────────────────│
         │                       │                       │
         │ 6. Fetch Results      │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │ 7. Return Results     │                       │
         │<──────────────────────│                       │
```

## Result Structure

### DiagnosisResult

```json
{
  "result_id": "RES-XXXXXXXXXXXX",
  "session_id": "WKN-XXXXXXXXXXXX",
  "student_id": "STU001",
  "diagnosis_type": "aptitude",
  "overall_score": 75.5,
  "overall_percentile": 68.0,
  "overall_interpretation": "평균 이상의 적성을 보이고 있습니다.",
  "category_scores": [...],
  "occupation_matches": [...],
  "recommendations": [...],
  "completed_at": "2024-01-15T10:30:00Z",
  "valid_until": "2026-01-15T10:30:00Z"
}
```

### OccupationMatch

```json
{
  "occupation_code": "2321",
  "occupation_name": "소프트웨어 개발자",
  "occupation_name_en": "Software Developer",
  "match_score": 92.5,
  "match_rank": 1,
  "description": "컴퓨터 프로그램 설계 및 개발",
  "required_education": "대학교(4년)",
  "salary_range": "4,000만원 ~ 8,000만원",
  "employment_outlook": "매우 좋음"
}
```

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
uvicorn app.main:app --host 0.0.0.0 --port 8018 --reload
```

## Environment Variables

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=idino_career
DB_USER=postgres
DB_PASSWORD=your_password
DB_SCHEMA=idino_career

# Service
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8018

# WorkNet API
WORKNET_API_BASE_URL=https://www.work.go.kr/consltJobCarpa
WORKNET_API_KEY=your_api_key
WORKNET_CALLBACK_URL=https://your-domain.com/worknet/callback
```

## Database Tables

### tb_worknet_sessions
- `session_id` - Unique session identifier
- `student_id` - Reference to student
- `diagnosis_type` - Type of diagnosis test
- `status` - Session status (initiated, in_progress, completed, etc.)
- `worknet_url` - URL to WorkNet test page
- `expires_at` - Session expiration time
- `created_at`, `updated_at` - Timestamps

### tb_worknet_results
- `result_id` - Unique result identifier
- `session_id` - Reference to session
- `student_id` - Reference to student
- `diagnosis_type` - Type of diagnosis
- `overall_score`, `overall_percentile` - Summary scores
- `category_scores` - Detailed category scores (JSONB)
- `occupation_matches` - Matched occupations (JSONB)
- `recommendations` - Career recommendations (JSONB)
- `completed_at`, `valid_until` - Validity period

## Example Usage

### Create Diagnosis Session
```bash
curl -X POST http://localhost:8018/worknet/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU001",
    "diagnosis_type": "aptitude",
    "callback_url": "https://myapp.com/callback"
  }'
```

### Get Student's Latest Results
```bash
curl http://localhost:8018/worknet/results/student/STU001/latest
```

### Get Diagnosis Summary
```bash
curl http://localhost:8018/worknet/summary/STU001
```

### List Available Diagnosis Types
```bash
curl http://localhost:8018/worknet/diagnosis-types
```

## About WorkNet

WorkNet (워크넷) is operated by the Korea Employment Information Service under the Ministry of Employment and Labor. It provides:

- Scientifically validated vocational assessments
- Government-backed career guidance
- Comprehensive occupation database
- Employment information and job matching

Website: https://www.work.go.kr
