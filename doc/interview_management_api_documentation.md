# Interview Management API Documentation

## Base URL
```
{{baseUrl}}/api/interview-management/
```

## Authentication
All endpoints require JWT authentication. Include the token in the header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cvs-for-interview/` | Get all CVs available for interview (dropdown) |
| POST | `/start-interview/` | Start interview and add CV to Interview table |
| GET | `/` | List all interviews |
| GET | `/ongoing-interviews/` | List only ongoing interviews |
| GET | `/{id}/` | Get single interview details |
| PATCH | `/{id}/update-status/` | Update interview status (selected/rejected/pending) |
| POST/PUT/PATCH | `/{id}/evaluation/` | Create or update interview evaluation |
| DELETE | `/{id}/` | Delete interview |

---

## 1. Get CVs for Interview (Dropdown)

**Endpoint:** `GET /api/interview-management/cvs-for-interview/`

**Description:** Get all CVs that are available for interview selection. Returns only CVs with `status='pending'` by default.

**Query Parameters:**
- `all` (optional): Set to `true` to get all CVs regardless of status

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Found 10 CV(s) available for interview",
  "data": [
    {
      "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
      "name": "John Doe",
      "job_title": 1,
      "job_title_name": "Software Developer",
      "place": "Kochi",
      "email": "john@example.com",
      "phone_number": "+91 9876543210",
      "interview_status": "pending"
    },
    {
      "id": "f7e8d9c0-b3a2-1f0e-9d8c-7b6a5f4e3d2c",
      "name": "Jane Smith",
      "job_title": 2,
      "job_title_name": "Frontend Developer",
      "place": "Thiruvananthapuram",
      "email": "jane@example.com",
      "phone_number": "+91 9876543211",
      "interview_status": "pending"
    }
  ]
}
```

**Empty Response:**
```json
{
  "success": true,
  "message": "Found 0 CV(s) available for interview",
  "data": []
}
```

**Error Response (500):**
```json
{
  "success": false,
  "message": "Error retrieving CV data",
  "error": "INTERNAL_ERROR",
  "details": "Please try again later"
}
```

**cURL Example:**
```bash
# Get pending CVs only
curl -X GET "{{baseUrl}}/api/interview-management/cvs-for-interview/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get all CVs
curl -X GET "{{baseUrl}}/api/interview-management/cvs-for-interview/?all=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 2. Start Interview

**Endpoint:** `POST /api/interview-management/start-interview/`

**Description:** Select a CV from the dropdown and start an interview. This will:
1. Change the CV status from `pending` to `ongoing`
2. Create a new record in the Interview table with CV details
3. Create an empty evaluation record

**Request Body:**
```json
{
  "candidate_id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
  "scheduled_at": "2025-11-15T10:00:00Z",
  "interviewer_id": 1
}
```

**Fields:**
- `candidate_id` (required): UUID of the candidate from UserCvData
- `scheduled_at` (required): ISO 8601 DateTime when interview is scheduled
- `interviewer_id` (optional): ID of the interviewer (AppUser)

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Interview started successfully for John Doe",
  "data": {
    "id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
    "candidate": {
      "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
      "name": "John Doe",
      "job_title": 1,
      "job_title_name": "Software Developer",
      "place": "Kochi",
      "email": "john@example.com",
      "phone_number": "+91 9876543210",
      "interview_status": "ongoing"
    },
    "interviewer": {
      "id": 1,
      "email": "hr@company.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "job_role": "HR Manager"
    },
    "scheduled_at": "2025-11-15T10:00:00Z",
    "status": "pending",
    "evaluation": null,
    "created_at": "2025-11-10T09:30:00Z",
    "updated_at": "2025-11-10T09:30:00Z"
  }
}
```

**Error Responses:**

*Candidate Not Found (404):*
```json
{
  "success": false,
  "message": "Candidate not found",
  "error": "NOT_FOUND",
  "details": "No candidate found with the provided ID"
}
```

*Validation Error - Already Ongoing (400):*
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "candidate_id": ["Interview for John Doe is already in progress"]
  }
}
```

*Validation Error - Invalid Status (400):*
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "candidate_id": ["Candidate status is 'selected'. Cannot start new interview."]
  }
}
```

*Validation Error - Invalid Interviewer (400):*
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "interviewer_id": ["Interviewer with this ID does not exist"]
  }
}
```

**cURL Example:**
```bash
curl -X POST "{{baseUrl}}/api/interview-management/start-interview/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
    "scheduled_at": "2025-11-15T10:00:00Z",
    "interviewer_id": 1
  }'
```

---

## 3. List All Interviews

**Endpoint:** `GET /api/interview-management/`

**Description:** Get a list of all interviews with candidate and interviewer details.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Found 5 interview(s)",
  "data": [
    {
      "id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
      "candidate_name": "John Doe",
      "candidate_email": "john@example.com",
      "candidate_phone": "+91 9876543210",
      "job_title": "Software Developer",
      "place": "Kochi",
      "district": "Ernakulam",
      "interviewer_name": "Jane Smith",
      "scheduled_at": "2025-11-15T10:00:00Z",
      "status": "pending",
      "cv_status": "ongoing",
      "has_evaluation": true,
      "created_at": "2025-11-10T09:30:00Z",
      "updated_at": "2025-11-10T09:30:00Z"
    },
    {
      "id": "a1b2c3d4-e5f6-7g8h-9i0j-1k2l3m4n5o6p",
      "candidate_name": "Jane Smith",
      "candidate_email": "jane@example.com",
      "candidate_phone": "+91 9876543211",
      "job_title": "Frontend Developer",
      "place": "Thiruvananthapuram",
      "district": "Thiruvananthapuram",
      "interviewer_name": "John Manager",
      "scheduled_at": "2025-11-14T14:00:00Z",
      "status": "selected",
      "cv_status": "selected",
      "has_evaluation": true,
      "created_at": "2025-11-09T10:00:00Z",
      "updated_at": "2025-11-09T15:30:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "{{baseUrl}}/api/interview-management/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 4. Get Ongoing Interviews

**Endpoint:** `GET /api/interview-management/ongoing-interviews/`

**Description:** Get all interviews where the CV status is currently `ongoing`. Use this endpoint to display the list of interviews in progress.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Found 3 ongoing interview(s)",
  "data": [
    {
      "id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
      "candidate": {
        "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
        "name": "John Doe",
        "job_title": 1,
        "job_title_name": "Software Developer",
        "place": "Kochi",
        "email": "john@example.com",
        "phone_number": "+91 9876543210",
        "interview_status": "ongoing"
      },
      "interviewer_name": "Jane Smith",
      "scheduled_at": "2025-11-15T10:00:00Z",
      "status": "pending",
      "evaluation_completed": false,
      "created_at": "2025-11-10T09:30:00Z",
      "updated_at": "2025-11-10T09:30:00Z"
    }
  ]
}
```

**Empty Response:**
```json
{
  "success": true,
  "message": "No ongoing interviews found",
  "data": []
}
```

**cURL Example:**
```bash
curl -X GET "{{baseUrl}}/api/interview-management/ongoing-interviews/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 5. Get Interview Details

**Endpoint:** `GET /api/interview-management/{interview_id}/`

**Description:** Get complete details of a specific interview including candidate information and evaluation data.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Interview retrieved successfully",
  "data": {
    "id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
    "candidate": {
      "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
      "name": "John Doe",
      "job_title": 1,
      "job_title_name": "Software Developer",
      "place": "Kochi",
      "email": "john@example.com",
      "phone_number": "+91 9876543210",
      "interview_status": "ongoing"
    },
    "interviewer": {
      "id": 1,
      "email": "hr@company.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "job_role": "HR Manager"
    },
    "scheduled_at": "2025-11-15T10:00:00Z",
    "status": "pending",
    "evaluation": {
      "interview_id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
      "candidate_name": "John Doe",
      "appearance": 8,
      "knowledge": 9,
      "confidence": 7,
      "attitude": 8,
      "communication": 9,
      "languages": "English, Malayalam, Hindi",
      "expected_salary": "50000.00",
      "experience": "5 years in backend development with Python and Django",
      "remark": "Excellent candidate with strong technical skills",
      "voice_note": null,
      "average_rating": 8.2,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T11:30:00Z"
    },
    "created_at": "2025-11-10T09:30:00Z",
    "updated_at": "2025-11-10T11:30:00Z"
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "message": "Interview not found",
  "error": "NOT_FOUND",
  "details": "The requested interview does not exist"
}
```

**cURL Example:**
```bash
curl -X GET "{{baseUrl}}/api/interview-management/f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 6. Update Interview Status

**Endpoint:** `PATCH /api/interview-management/{interview_id}/update-status/`

**Description:** Update the interview status to selected, rejected, or pending. This will automatically sync the CV status as well.

**Request Body:**
```json
{
  "status": "selected",
  "remark": "Strong technical skills and good communication"
}
```

**Fields:**
- `status` (required): One of `selected`, `rejected`, or `pending`
- `remark` (optional): Additional comments about the status change (max 500 characters)

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Interview status updated to 'selected' successfully",
  "data": {
    "id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
    "candidate": {
      "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
      "name": "John Doe",
      "job_title": 1,
      "job_title_name": "Software Developer",
      "place": "Kochi",
      "email": "john@example.com",
      "phone_number": "+91 9876543210",
      "interview_status": "selected"
    },
    "interviewer": {
      "id": 1,
      "email": "hr@company.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "job_role": "HR Manager"
    },
    "scheduled_at": "2025-11-15T10:00:00Z",
    "status": "selected",
    "evaluation": {
      "appearance": 8,
      "knowledge": 9,
      "confidence": 7,
      "attitude": 8,
      "communication": 9,
      "average_rating": 8.2,
      ...
    },
    "created_at": "2025-11-10T09:30:00Z",
    "updated_at": "2025-11-10T12:00:00Z"
  }
}
```

**Error Responses:**

*Interview Not Found (404):*
```json
{
  "success": false,
  "message": "Interview not found",
  "error": "NOT_FOUND",
  "details": "The requested interview does not exist"
}
```

*Validation Error (400):*
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "status": ["\"invalid_status\" is not a valid choice."]
  }
}
```

**cURL Example:**
```bash
curl -X PATCH "{{baseUrl}}/api/interview-management/f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o/update-status/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "selected",
    "remark": "Strong technical skills and good communication"
  }'
```

---

## 7. Create/Update Interview Evaluation

**Endpoint:** `POST/PUT/PATCH /api/interview-management/{interview_id}/evaluation/`

**Description:** Create or update the evaluation for an interview. Include ratings, feedback, and other assessment details.

**Request Body:**
```json
{
  "appearance": 8,
  "knowledge": 9,
  "confidence": 7,
  "attitude": 8,
  "communication": 9,
  "languages": "English, Malayalam, Hindi",
  "expected_salary": "50000.00",
  "experience": "5 years in backend development with Python and Django. Has worked on multiple REST APIs and cloud deployments.",
  "remark": "Excellent candidate with strong technical skills. Shows great problem-solving abilities and good communication. Recommended for hire."
}
```

**Fields:**
- `appearance` (optional): Rating from 0 to 10
- `knowledge` (optional): Rating from 0 to 10
- `confidence` (optional): Rating from 0 to 10
- `attitude` (optional): Rating from 0 to 10
- `communication` (optional): Rating from 0 to 10
- `languages` (optional): Languages known by the candidate
- `expected_salary` (optional): Expected salary (decimal format)
- `experience` (optional): Experience details and observations
- `remark` (optional): General remarks and feedback
- `voice_note` (optional): Audio file (mp3, wav, m4a) - use multipart/form-data

**Success Response (201 Created / 200 OK):**
```json
{
  "success": true,
  "message": "Interview evaluation created successfully",
  "data": {
    "interview_id": "f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o",
    "candidate_name": "John Doe",
    "appearance": 8,
    "knowledge": 9,
    "confidence": 7,
    "attitude": 8,
    "communication": 9,
    "languages": "English, Malayalam, Hindi",
    "expected_salary": "50000.00",
    "experience": "5 years in backend development with Python and Django. Has worked on multiple REST APIs and cloud deployments.",
    "remark": "Excellent candidate with strong technical skills. Shows great problem-solving abilities and good communication. Recommended for hire.",
    "voice_note": null,
    "average_rating": 8.2,
    "created_at": "2025-11-10T10:00:00Z",
    "updated_at": "2025-11-10T11:30:00Z"
  }
}
```

**Error Responses:**

*Interview Not Found (404):*
```json
{
  "success": false,
  "message": "Interview not found",
  "error": "NOT_FOUND",
  "details": "The requested interview does not exist"
}
```

*Validation Error (400):*
```json
{
  "success": false,
  "message": "Invalid evaluation data",
  "error": "VALIDATION_ERROR",
  "details": {
    "appearance": ["Rating must be between 0 and 10"]
  }
}
```

**cURL Example:**
```bash
curl -X POST "{{baseUrl}}/api/interview-management/f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o/evaluation/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "appearance": 8,
    "knowledge": 9,
    "confidence": 7,
    "attitude": 8,
    "communication": 9,
    "languages": "English, Malayalam, Hindi",
    "expected_salary": "50000.00",
    "experience": "5 years in backend development",
    "remark": "Excellent candidate"
  }'
```

**With Voice Note (multipart/form-data):**
```bash
curl -X POST "{{baseUrl}}/api/interview-management/f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o/evaluation/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "appearance=8" \
  -F "knowledge=9" \
  -F "confidence=7" \
  -F "attitude=8" \
  -F "communication=9" \
  -F "languages=English, Malayalam" \
  -F "expected_salary=50000.00" \
  -F "experience=5 years in backend development" \
  -F "remark=Excellent candidate" \
  -F "voice_note=@/path/to/audio.mp3"
```

---

## 8. Delete Interview

**Endpoint:** `DELETE /api/interview-management/{interview_id}/`

**Description:** Delete an interview record. If the CV status is `ongoing`, it will be automatically reset to `pending`.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Interview deleted successfully"
}
```

**Error Response (404):**
```json
{
  "success": false,
  "message": "Interview not found",
  "error": "NOT_FOUND",
  "details": "The requested interview does not exist"
}
```

**cURL Example:**
```bash
curl -X DELETE "{{baseUrl}}/api/interview-management/f8a7b6c5-d4e3-2f1g-0h9i-8j7k6l5m4n3o/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Error Codes Reference

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data or validation failed |
| `NOT_FOUND` | 404 | Resource not found (interview, candidate, etc.) |
| `INTERNAL_ERROR` | 500 | Server error, try again later |

---

## Status Values

### CV Interview Status
- `pending` - Initial status for new CVs
- `ongoing` - Interview is in progress
- `selected` - Candidate selected after interview
- `rejected` - Candidate rejected after interview

### Interview Status
- `pending` - Interview scheduled but not completed
- `selected` - Candidate passed interview
- `rejected` - Candidate failed interview

---

## Complete Workflow Example

### Step 1: Get Available CVs for Dropdown
```http
GET /api/interview-management/cvs-for-interview/
```

**Response:** List of pending CVs to choose from

---

### Step 2: Start Interview
```http
POST /api/interview-management/start-interview/
Content-Type: application/json

{
  "candidate_id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
  "scheduled_at": "2025-11-15T10:00:00Z",
  "interviewer_id": 1
}
```

**Result:**
- ✅ CV status changes from `pending` → `ongoing`
- ✅ Interview record created in database
- ✅ Empty evaluation record created

---

### Step 3: View Ongoing Interviews
```http
GET /api/interview-management/ongoing-interviews/
```

**Response:** List of all interviews currently in progress

---

### Step 4: Fill Evaluation Form
```http
POST /api/interview-management/{interview_id}/evaluation/
Content-Type: application/json

{
  "appearance": 8,
  "knowledge": 9,
  "confidence": 7,
  "attitude": 8,
  "communication": 9,
  "languages": "English, Malayalam",
  "expected_salary": "50000.00",
  "experience": "5 years experience",
  "remark": "Excellent candidate"
}
```

**Result:** Evaluation saved

---

### Step 5: Update Interview Status
```http
PATCH /api/interview-management/{interview_id}/update-status/
Content-Type: application/json

{
  "status": "selected",
  "remark": "Strong technical skills"
}
```

**Result:**
- ✅ Interview status: `pending` → `selected`
- ✅ CV status: `ongoing` → `selected` (auto-synced)

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- UUIDs are used for interview and candidate IDs for security
- File uploads (voice notes) require `multipart/form-data` content type
- Interview status and CV status are automatically synchronized
- Deleting an interview resets ongoing CV status to pending
- Average rating is calculated automatically from the 5 rating fields
- All endpoints require valid JWT authentication token

---

## Testing Tips

1. **Test with Postman/Insomnia:**
   - Import the endpoints
   - Set up JWT authentication in headers
   - Test the complete workflow from start to finish

2. **Check Status Sync:**
   - Start an interview and verify CV status changes to `ongoing`
   - Update status and verify both interview and CV status sync

3. **Validation Testing:**
   - Try starting interview with already ongoing CV (should fail)
   - Try invalid status values (should fail)
   - Try ratings outside 0-10 range (should fail)

4. **Edge Cases:**
   - Delete interview and check if CV status resets
   - Update evaluation multiple times
   - Get ongoing interviews when none exist
