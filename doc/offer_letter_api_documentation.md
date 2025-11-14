# Offer Letter Management API Documentation

## Base URL
```
/api/offer-letters/
```

---

## Authentication
All endpoints require authentication using JWT tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. List All Offer Letters
**GET** `/api/offer-letters/`

Get a list of all offer letters with optional filtering.

#### Query Parameters
- `status` (optional): Filter by status (`draft`, `sent`, `accepted`, `rejected`)
- `candidate` (optional): Filter by candidate ID

#### Request Example
```http
GET /api/offer-letters/?status=sent
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Found 5 offer letter(s)",
  "data": [
    {
      "id": 1,
      "candidate": "uuid-here",
      "candidate_name": "John Doe",
      "candidate_email": "john@example.com",
      "candidate_phone": "9876543210",
      "position": "Software Engineer",
      "department": "IT",
      "salary": 50000.00,
      "currency": "INR",
      "joining_date": "2025-12-01",
      "probation_period": 3,
      "subject": "Job Offer - Software Engineer",
      "body": "We are pleased to offer you...",
      "terms_conditions": "Terms and conditions...",
      "pdf_file": null,
      "status": "sent",
      "sent_at": "2025-11-14T10:30:00Z",
      "accepted_at": null,
      "rejected_at": null,
      "rejection_reason": "",
      "created_by": 1,
      "created_by_name": "admin@example.com",
      "created_at": "2025-11-14T09:00:00Z",
      "updated_at": "2025-11-14T10:30:00Z"
    }
  ]
}
```

---

### 2. Create Offer Letter
**POST** `/api/offer-letters/`

Create a new offer letter for a selected candidate.

#### Request Body
```json
{
  "candidate": "uuid-of-candidate",
  "position": "Software Engineer",
  "department": "IT",
  "salary": 50000.00,
  "currency": "INR",
  "joining_date": "2025-12-01",
  "probation_period": 3,
  "subject": "Job Offer - Software Engineer",
  "body": "Dear [Candidate Name], We are pleased to offer you the position of Software Engineer...",
  "terms_conditions": "1. This offer is contingent upon...\n2. Your employment will be subject to..."
}
```

#### Field Descriptions
- `candidate` (UUID, required): ID of the candidate (must have 'selected' status)
- `position` (string, required): Job position being offered
- `department` (string, required): Department name
- `salary` (decimal, required): Salary amount
- `currency` (string, required): Currency code (e.g., INR, USD)
- `joining_date` (date, required): Expected joining date (format: YYYY-MM-DD)
- `probation_period` (integer, required): Probation period in months
- `subject` (string, required): Email/letter subject
- `body` (text, required): Offer letter body content
- `terms_conditions` (text, required): Terms and conditions

#### Response Example (201 Created)
```json
{
  "success": true,
  "message": "Offer letter created successfully for John Doe",
  "data": {
    "id": 1,
    "candidate": "uuid-here",
    "candidate_name": "John Doe",
    "position": "Software Engineer",
    "status": "draft",
    ...
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "candidate": ["Offer letters can only be created for candidates with 'selected' status."],
    "joining_date": ["Joining date must be in the future."]
  }
}
```

---

### 3. Get Offer Letter Details
**GET** `/api/offer-letters/<id>/`

Retrieve details of a specific offer letter.

#### Request Example
```http
GET /api/offer-letters/1/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter retrieved successfully",
  "data": {
    "id": 1,
    "candidate": "uuid-here",
    "candidate_name": "John Doe",
    "candidate_email": "john@example.com",
    "candidate_phone": "9876543210",
    "position": "Software Engineer",
    "department": "IT",
    "salary": 50000.00,
    "currency": "INR",
    "joining_date": "2025-12-01",
    "probation_period": 3,
    "subject": "Job Offer - Software Engineer",
    "body": "We are pleased to offer you...",
    "terms_conditions": "Terms and conditions...",
    "pdf_file": null,
    "status": "draft",
    "sent_at": null,
    "accepted_at": null,
    "rejected_at": null,
    "rejection_reason": "",
    "created_by": 1,
    "created_by_name": "admin@example.com",
    "created_at": "2025-11-14T09:00:00Z",
    "updated_at": "2025-11-14T09:00:00Z"
  }
}
```

#### Error Response (404 Not Found)
```json
{
  "success": false,
  "message": "Offer letter not found",
  "error": "NOT_FOUND"
}
```

---

### 4. Update Offer Letter
**PUT/PATCH** `/api/offer-letters/<id>/`

Update an existing offer letter (partial updates supported with PATCH).

#### Request Body (PATCH)
```json
{
  "salary": 55000.00,
  "probation_period": 6
}
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter updated successfully",
  "data": {
    "id": 1,
    "salary": 55000.00,
    "probation_period": 6,
    ...
  }
}
```

---

### 5. Delete Offer Letter
**DELETE** `/api/offer-letters/<id>/`

Delete an offer letter.

#### Request Example
```http
DELETE /api/offer-letters/1/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter for John Doe deleted successfully",
  "data": null
}
```

---

### 6. Get Selected Candidates
**GET** `/api/offer-letters/selected-candidates/`

Get all candidates with 'selected' interview status who are available for offer letters.

#### Request Example
```http
GET /api/offer-letters/selected-candidates/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Found 3 selected candidate(s) available for offer letters",
  "data": [
    {
      "id": "uuid-interview-id",
      "candidate_id": "uuid-candidate-id",
      "name": "John Doe",
      "email": "john@example.com",
      "phone_number": "9876543210",
      "job_title": 1,
      "job_title_name": "Software Engineer",
      "experience": "3 years",
      "education": "B.Tech Computer Science",
      "place": "Kalpetta",
      "district": "Wayanad",
      "interview_status": "selected",
      "scheduled_at": "2025-11-10T10:00:00Z",
      "status": "selected"
    }
  ]
}
```

---

### 7. Send Offer Letter
**POST** `/api/offer-letters/<id>/send-offer/`

Mark an offer letter as sent (status changes from 'draft' to 'sent').

#### Request Example
```http
POST /api/offer-letters/1/send-offer/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter marked as sent",
  "data": {
    "id": 1,
    "status": "sent",
    "sent_at": "2025-11-14T12:00:00Z",
    ...
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Only draft offers can be sent",
  "error": "INVALID_STATUS"
}
```

---

### 8. Accept Offer Letter
**POST** `/api/offer-letters/<id>/accept-offer/`

Accept an offer letter (status changes from 'sent' to 'accepted').

#### Request Example
```http
POST /api/offer-letters/1/accept-offer/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter accepted successfully",
  "data": {
    "id": 1,
    "status": "accepted",
    "accepted_at": "2025-11-14T15:30:00Z",
    ...
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Only sent offers can be accepted",
  "error": "INVALID_STATUS"
}
```

---

### 9. Reject Offer Letter
**POST** `/api/offer-letters/<id>/reject-offer/`

Reject an offer letter (status changes from 'sent' to 'rejected').

#### Request Body
```json
{
  "rejection_reason": "Candidate found a better opportunity"
}
```

#### Field Descriptions
- `rejection_reason` (string, optional): Reason for rejection

#### Request Example
```http
POST /api/offer-letters/1/reject-offer/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "rejection_reason": "Accepted another offer"
}
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter rejected",
  "data": {
    "id": 1,
    "status": "rejected",
    "rejected_at": "2025-11-14T16:00:00Z",
    "rejection_reason": "Accepted another offer",
    ...
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Only sent offers can be rejected",
  "error": "INVALID_STATUS"
}
```

---

## Status Flow

```
draft → sent → accepted
              ↘ rejected
```

- **draft**: Offer letter created but not yet sent
- **sent**: Offer letter sent to candidate
- **accepted**: Candidate accepted the offer
- **rejected**: Candidate rejected the offer

---

## Error Codes

| Error Code | Description |
|------------|-------------|
| VALIDATION_ERROR | Invalid data provided in request |
| NOT_FOUND | Offer letter not found |
| INVALID_STATUS | Operation not allowed for current status |

---

## Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request / Validation error |
| 401 | Unauthorized |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Notes

1. **Candidate Eligibility**: Only candidates with 'selected' interview status can have offer letters created for them.

2. **Joining Date Validation**: The joining date must be in the future.

3. **Status Transitions**: 
   - Only 'draft' offers can be sent
   - Only 'sent' offers can be accepted or rejected
   
4. **Automatic Fields**: The `created_by` field is automatically set to the authenticated user making the request.

5. **Filtering**: Use query parameters to filter offer letters by status or candidate ID.

6. **Timestamps**: All datetime fields are in ISO 8601 format with timezone (UTC).

---

## Example Workflow

### Complete Offer Letter Process

```bash
# 1. Get selected candidates
GET /api/offer-letters/selected-candidates/

# 2. Create offer letter for a candidate
POST /api/offer-letters/
{
  "candidate": "uuid-from-step-1",
  "position": "Software Engineer",
  ...
}

# 3. Review and update if needed
PATCH /api/offer-letters/1/
{
  "salary": 55000.00
}

# 4. Send the offer
POST /api/offer-letters/1/send-offer/

# 5. Candidate accepts/rejects
POST /api/offer-letters/1/accept-offer/
# OR
POST /api/offer-letters/1/reject-offer/
{
  "rejection_reason": "Reason here"
}
```
