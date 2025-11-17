# Offer Letter Management API Documentation

## Base URL
```
/api/offer-letter/
```

---

## Authentication
All endpoints require authentication using JWT tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/offer-letter/` | List all offer letters |
| POST | `/api/offer-letter/` | Create new offer letter |
| GET | `/api/offer-letter/<id>/` | Get offer letter details |
| PUT/PATCH | `/api/offer-letter/<id>/` | Update offer letter |
| DELETE | `/api/offer-letter/<id>/` | Delete offer letter |
| GET | `/api/offer-letter/selected-candidates/` | Get selected candidates for offer letters |

---

## Data Models

### OfferLetter Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | Integer | Auto | Primary key |
| `candidate` | UUID | Yes | Reference to UserCvData (must have 'selected' status) |
| `position` | String | Yes | Job position (max 100 chars) |
| `department` | String | Yes | Department name (max 100 chars) |
| `salary` | Decimal | Yes | Salary amount (max digits: 10, decimal places: 2) |
| `joining_data` | Date | Yes | Expected joining date (YYYY-MM-DD) |
| `notice_period` | Integer | Yes | Notice period in days |
| `subject` | String | No | Email/letter subject (default: "Job Offer Letter") |
| `body` | Text | Yes | Offer letter body content |
| `terms_condition` | Text | No | Terms and conditions |
| `pdf_file` | File | No | Generated PDF file (upload to `offer_letters/`) |
| `candidate_cv` | File / URL | No | Candidate CV file (URL to uploaded CV) |

| `candidate_status` | String | No | Status: `draft`, `sent`, `willing`, `not_willing` (default: `draft`) |
| `rejection_status` | Text | No | Reason for rejection |
| `work_start_time` | Time | No | Daily work start time (HH:MM:SS) |
| `work_end_time` | Time | No | Daily work end time (HH:MM:SS) |
| `created_by` | FK | Auto | User who created the offer letter |
| `created_at` | DateTime | Auto | Creation timestamp |
| `updated_at` | DateTime | Auto | Last update timestamp |

---

## API Endpoints Details

### 1. List All Offer Letters
**GET** `/api/offer-letter/`

Get a list of all offer letters with optional filtering.

#### Query Parameters
- `status` (optional): Filter by candidate_status (`draft`, `sent`, `willing`, `not_willing`)
- `candidate` (optional): Filter by candidate UUID

#### Request Example
```http
GET /api/offer-letter/?status=sent
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
      "candidate": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "candidate_name": "John Doe",
      "candidate_email": "john@example.com",
      "candidate_phone": "9876543210",
      "position": "Software Engineer",
      "department": "IT",
      "salary": "50000.00",
      "joining_data": "2025-12-01",
      "notice_period": 30,
      "subject": "Job Offer - Software Engineer",
      "body": "We are pleased to offer you the position...",
      "terms_condition": "1. This offer is contingent upon...",
  "pdf_file": null,
  "candidate_cv": "https://pub-6135d70162b542fb895c54cf94077310.r2.dev/media/cvs/sample_MkmBDtD.pdf",
      "candidate_status": "sent",
      "rejection_status": "",
      "work_start_time": "09:00:00",
      "work_end_time": "18:00:00",
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
**POST** `/api/offer-letter/`

Create a new offer letter for a selected candidate.

#### Request Body
```json
{
  "candidate": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "position": "Software Engineer",
  "department": "IT",
  "salary": 50000.00,
  "joining_data": "2025-12-01",
  "notice_period": 30,
  "subject": "Job Offer - Software Engineer Position",
  "body": "Dear [Candidate Name],\n\nWe are pleased to offer you the position of Software Engineer at our company...",
  "terms_condition": "1. This offer is contingent upon successful completion of background checks.\n2. Your employment will be subject to our company policies.",
  "work_start_time": "09:00:00",
  "work_end_time": "18:00:00"
}
```

#### Field Descriptions
- `candidate` (UUID, required): ID of the candidate from UserCvData (must have 'selected' interview_status)
- `position` (string, required): Job position being offered
- `department` (string, required): Department name
- `salary` (decimal, required): Salary amount
- `joining_data` (date, required): Expected joining date (format: YYYY-MM-DD, must be future date)
- `notice_period` (integer, required): Notice period in days
- `subject` (string, optional): Email/letter subject (default: "Job Offer Letter")
- `body` (text, required): Offer letter body content
- `terms_condition` (text, optional): Terms and conditions
- `work_start_time` (time, optional): Daily work start time (format: HH:MM:SS)
- `work_end_time` (time, optional): Daily work end time (format: HH:MM:SS)

#### Response Example (201 Created)
```json
{
  "success": true,
  "message": "Offer letter created successfully for John Doe",
  "data": {
    "id": 1,
    "candidate": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "candidate_name": "John Doe",
    "candidate_email": "john@example.com",
    "candidate_phone": "9876543210",
    "position": "Software Engineer",
    "department": "IT",
    "salary": "50000.00",
    "joining_data": "2025-12-01",
    "notice_period": 30,
    "subject": "Job Offer - Software Engineer Position",
    "body": "Dear John Doe...",
    "terms_condition": "1. This offer is contingent...",
  "pdf_file": null,
  "candidate_cv": "https://pub-6135d70162b542fb895c54cf94077310.r2.dev/media/cvs/sample_MkmBDtD.pdf",
    "candidate_status": "draft",
    "rejection_status": "",
    "work_start_time": "09:00:00",
    "work_end_time": "18:00:00",
    "created_by": 1,
    "created_by_name": "admin@example.com",
    "created_at": "2025-11-14T09:00:00Z",
    "updated_at": "2025-11-14T09:00:00Z"
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
    "joining_data": ["Joining date must be in the future."]
  }
}
```

#### Validation Rules
1. **Candidate must have 'selected' interview status**
2. **Joining date must be in the future**
3. **Only one offer letter per candidate** (OneToOne relationship)

---

### 3. Get Offer Letter Details
**GET** `/api/offer-letter/<id>/`

Retrieve details of a specific offer letter.

#### Request Example
```http
GET /api/offer-letter/1/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter retrieved successfully",
  "data": {
    "id": 1,
    "candidate": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "candidate_name": "John Doe",
    "candidate_email": "john@example.com",
    "candidate_phone": "9876543210",
    "position": "Software Engineer",
    "department": "IT",
    "salary": "50000.00",
    "joining_data": "2025-12-01",
    "notice_period": 30,
    "subject": "Job Offer - Software Engineer",
    "body": "We are pleased to offer you...",
    "terms_condition": "Terms and conditions...",
  "pdf_file": null,
  "candidate_cv": "https://pub-6135d70162b542fb895c54cf94077310.r2.dev/media/cvs/sample_MkmBDtD.pdf",
    "candidate_status": "draft",
    "rejection_status": "",
    "work_start_time": "09:00:00",
    "work_end_time": "18:00:00",
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
**PUT/PATCH** `/api/offer-letter/<id>/`

Update an existing offer letter. Use PATCH for partial updates.

#### Request Body (PATCH)
```json
{
  "salary": 55000.00,
  "notice_period": 45,
  "work_start_time": "10:00:00"
}
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Offer letter updated successfully",
  "data": {
    "id": 1,
    "salary": "55000.00",
    "notice_period": 45,
    "work_start_time": "10:00:00",
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
    "salary": ["Ensure that there are no more than 10 digits in total."]
  }
}
```

---

### 5. Delete Offer Letter
**DELETE** `/api/offer-letter/<id>/`

Delete an offer letter permanently.

#### Request Example
```http
DELETE /api/offer-letter/1/
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

#### Error Response (404 Not Found)
```json
{
  "success": false,
  "message": "Offer letter not found",
  "error": "NOT_FOUND"
}
```

---

### 6. Get Selected Candidates
**GET** `/api/offer-letter/selected-candidates/`

Get all candidates with 'selected' interview status who are available for offer letters.

**Note:** This endpoint returns Interview records where the candidate has been selected.

#### Request Example
```http
GET /api/offer-letter/selected-candidates/
Authorization: Bearer <access_token>
```

#### Response Example (200 OK)
```json
{
  "success": true,
  "message": "Found 3 selected candidate(s) available for offer letters",
  "data": [
    {
      "id": "interview-uuid-here",
      "candidate_id": "candidate-uuid-here",
      "name": "John Doe",
      "phone_number": "9876543210",
      "job_title_name": "Software Engineer",
      "status": "selected"
    },
    {
      "id": "interview-uuid-2",
      "candidate_id": "candidate-uuid-2",
      "name": "Jane Smith",
      "phone_number": "9876543211",
      "job_title_name": "Frontend Developer",
      "status": "selected"
    }
  ]
}
```

#### Field Descriptions
- `id`: Interview UUID
- `candidate_id`: Candidate (UserCvData) UUID - **use this for creating offer letters**
- `name`: Candidate's full name
- `phone_number`: Candidate's phone number
- `job_title_name`: Job title applied for
- `status`: Interview status (always 'selected' in this list)

---

## Status Management

### Available Status Values

| Status | Description |
|--------|-------------|
| `draft` | Offer letter created but not sent |
| `sent` | Offer letter sent to candidate |
| `willing` | Candidate accepted the offer |
| `not_willing` | Candidate rejected the offer |

### Managing Status

The `candidate_status` field can be updated directly using the PUT/PATCH endpoints:

```json
{
  "candidate_status": "sent"
}
```

**Note:** Status management is flexible and can be updated as needed through the standard update endpoints

---

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid data provided in request |
| NOT_FOUND | 404 | Offer letter not found |
| INVALID_STATUS | 400 | Operation not allowed for current status |

---

## Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request / Validation error |
| 401 | Unauthorized - Invalid or missing token |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Important Notes

### 1. Candidate Eligibility
- Only candidates with `'selected'` interview status can have offer letters created
- This is enforced at the model level with `limit_choices_to={'interview_status':'selected'}`
- OneToOne relationship means each candidate can have only one offer letter

### 2. Date Validation
- `joining_data` must be in the future
- Validation is performed in the serializer

### 3. Automatic Fields
- `created_by` is automatically set to the authenticated user
- `created_at` and `updated_at` are automatically managed by Django
- `candidate_status` defaults to `'draft'`

### 4. Working Hours
- `work_start_time` and `work_end_time` are stored as Time fields
- Format: `HH:MM:SS` (e.g., "09:00:00" for 9 AM)
- These fields are optional

### 5. Filtering
- Filter by `status` parameter for candidate_status
- Filter by `candidate` parameter for candidate UUID
- Filters can be combined: `/api/offer-letter/?status=sent&candidate=uuid-here`

### 6. Timestamps
- All datetime fields use ISO 8601 format with timezone (UTC)
- Example: `"2025-11-14T09:00:00Z"`

### 7. OneToOne Relationship
- Each candidate can have only ONE offer letter
- Attempting to create a second offer letter for the same candidate will fail
- Delete the existing offer letter first if you need to create a new one

---

## Complete Workflow

For the complete end-to-end recruitment workflow from CV submission to offer letter, see: [Complete Recruitment Workflow](./complete_recruitment_workflow.md)

This document focuses specifically on the Offer Letter Management API endpoints.

---

## Testing with cURL

### Create Offer Letter
```bash
curl -X POST http://localhost:8000/api/offer-letter/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "position": "Backend Developer",
    "department": "Engineering",
    "salary": 55000.00,
    "joining_data": "2025-12-01",
    "notice_period": 30,
    "subject": "Job Offer - Backend Developer",
    "body": "Dear Candidate, We are pleased to offer you...",
    "terms_condition": "Standard terms apply",
    "work_start_time": "09:00:00",
    "work_end_time": "18:00:00"
  }'
```

### List All Offer Letters
```bash
curl -X GET http://localhost:8000/api/offer-letter/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Offer Letter Status
```bash
curl -X PATCH http://localhost:8000/api/offer-letter/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_status": "sent"
  }'
```

---

## Response Format

All API responses follow this standard format:

### Success Response
```json
{
  "success": true,
  "message": "Descriptive success message",
  "data": {
    // Response data object or array
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Descriptive error message",
  "error": "ERROR_CODE",
  "details": {
    // Detailed error information (for validation errors)
  }
}
```

---

## Best Practices

1. **Always check candidate eligibility** before creating offer letters
2. **Use PATCH for partial updates** instead of PUT to avoid overwriting fields
3. **Validate joining dates** are in the future before submission
4. **Store rejection reasons** when candidates reject offers for future reference
5. **Set appropriate working hours** when creating offer letters
6. **Check current status** before attempting status transitions
7. **Handle errors gracefully** and provide user feedback
8. **Use transactions** when creating/updating multiple related records
9. **Log all status changes** for audit purposes
10. **Notify candidates** when offer letters are sent via email/SMS (implement separately)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-14 | Initial API documentation |

---

**Last Updated:** November 15, 2025
