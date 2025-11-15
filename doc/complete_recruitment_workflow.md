# Complete Recruitment Workflow

## End-to-End Process Overview

The complete recruitment workflow involves multiple steps across different modules:

1. **CV Submission** (CV Management)
2. **Interview Scheduling** (Interview Management)
3. **Interview Evaluation** (Interview Management)
4. **Offer Letter Creation** (Offer Letter Management)
5. **Offer Letter Tracking** (Offer Letter Management)

### Step-by-Step Process

```bash
# === STEP 1: CV SUBMISSION ===
# First, submit a candidate's CV through CV Management API
POST /api/cv-management/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone_number": "9876543210",
  "job_title": 1,
  "place": "Kochi",
  "district": "Ernakulam",
  "education": "B.Tech Computer Science",
  "experience": "3 years",
  "cv_file": "cv_file_url",
  "cv_source": "Direct"
}

# Response: CV created with interview_status = 'pending'

# === STEP 2: SCHEDULE INTERVIEW ===
# Get available CVs for interview
GET /api/interview-management/cvs-for-interview/
Authorization: Bearer <your_token>

# Schedule interview for the candidate
POST /api/interview-management/start-interview/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "candidate": "cv-uuid-from-step-1",
  "scheduled_at": "2025-11-20T10:00:00Z",
  "interviewer": 1
}

# === STEP 3: CONDUCT INTERVIEW ===
# Update interview status after evaluation
PATCH /api/interview-management/{interview-id}/update-status/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "status": "selected"
}

# This also updates the CV's interview_status to 'selected'

# === STEP 4: CREATE OFFER LETTER ===
# Get list of selected candidates available for offer letters
GET /api/offer-letter/selected-candidates/
Authorization: Bearer <your_token>

# Create offer letter for the selected candidate
POST /api/offer-letter/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "candidate": "candidate-uuid-from-selected-candidates",
  "position": "Software Engineer",
  "department": "Engineering",
  "salary": 60000.00,
  "joining_data": "2025-12-15",
  "notice_period": 30,
  "subject": "Job Offer - Software Engineer",
  "body": "Dear Candidate,\n\nWe are delighted to offer you the position of Software Engineer...",
  "terms_condition": "1. Employment contingent on background check\n2. Probation period of 6 months",
  "work_start_time": "09:00:00",
  "work_end_time": "18:00:00"
}

# === STEP 5: SEND AND TRACK OFFER LETTER ===
# Update offer letter status to 'sent'
PATCH /api/offer-letter/{offer-id}/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "candidate_status": "sent"
}

# === STEP 6: TRACK CANDIDATE RESPONSE ===
# Update based on candidate acceptance/rejection
PATCH /api/offer-letter/{offer-id}/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "candidate_status": "willing"  // or "not_willing"
}
```

### API Flow Summary

| Step | Module | API Endpoint | Action |
|------|--------|--------------|--------|
| 1 | CV Management | `POST /api/cv-management/` | Submit candidate CV |
| 2 | Interview Management | `GET /api/interview-management/cvs-for-interview/` | Get available CVs |
| 3 | Interview Management | `POST /api/interview-management/start-interview/` | Schedule interview |
| 4 | Interview Management | `PATCH /api/interview-management/{id}/update-status/` | Mark as selected |
| 5 | Offer Letter | `GET /api/offer-letter/selected-candidates/` | Get selected candidates |
| 6 | Offer Letter | `POST /api/offer-letter/` | Create offer letter |
| 7 | Offer Letter | `PATCH /api/offer-letter/{id}/` | Send offer letter |
| 8 | Offer Letter | `PATCH /api/offer-letter/{id}/` | Track acceptance/rejection |

### Status Flow

- **CV Status**: `pending` → `ongoing` → `selected`/`rejected`
- **Interview Status**: `pending` → `selected`/`rejected`
- **Offer Letter Status**: `draft` → `sent` → `willing`/`not_willing`

### Related Documentation

- [CV Management API Documentation](./cv_api_documentation.md)
- [Interview Management API Documentation](./interview_management_api_documentation.md)
- [Offer Letter API Documentation](./offer_letter_api_documentation.md)

---

**Last Updated:** November 15, 2025