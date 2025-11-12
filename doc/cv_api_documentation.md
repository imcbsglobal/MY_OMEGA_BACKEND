# CV Management API Documentation# CV Management API Documentation



## Base URL## Base URL

``````

{{baseUrl}}/api/cv-management/{{baseUrl}}/api/cv-management/

``````



## Authentication## Authentication

``````

Authorization: Bearer <your_access_token>Authorization: Bearer <your_access_token>

``````



------



## Job Title Endpoints## Job Title Endpoints



### 1. List Job Titles### 1. List Job Titles

**GET** `/job-titles/`**GET** `/job-titles/`



**Response:****Response (200 OK):**

```json```json

{{

  "success": true,  "success": true,

  "message": "Found 5 job title(s)",  "message": "Found 5 job title(s)",

  "data": [  "data": [

    {    {

      "id": 1,      "id": 1,

      "title": "Software Developer",      "title": "Software Developer",

      "created_at": "2025-11-10T08:00:00Z",      "created_at": "2025-11-10T08:00:00Z",

      "updated_at": "2025-11-10T08:00:00Z"      "updated_at": "2025-11-10T08:00:00Z"

    }    },

  ]    {

}      "id": 2,

```      "title": "HR Manager",

      "created_at": "2025-11-10T09:00:00Z",

---      "updated_at": "2025-11-10T09:00:00Z"

    }

### 2. Get Single Job Title  ]

**GET** `/job-titles/{id}/`}

```

**Response:**

```json**Error Response (500 Internal Server Error):**

{```json

  "success": true,{

  "message": "Job title retrieved successfully",  "success": false,

  "data": {  "message": "Error retrieving job titles",

    "id": 1,  "error": "INTERNAL_ERROR",

    "title": "Software Developer",  "details": "Please try again later"

    "created_at": "2025-11-10T08:00:00Z",}

    "updated_at": "2025-11-10T08:00:00Z"```

  }

}**cURL Example:**

``````bash

curl -X GET "{{baseUrl}}/api/cv-management/job-titles/" \

---  -H "Authorization: Bearer YOUR_JWT_TOKEN"

```

### 3. Create Job Title

**POST** `/job-titles/`---



**Request:**### 2. Get Single Job Title

```json

{**Endpoint:** `GET /api/cv-management/job-titles/{id}/`

  "title": "Software Developer"

}**Description:** Retrieve details of a specific job title.

```

**Success Response (200 OK):**

**Response:**```json

```json{

{  "success": true,

  "success": true,  "message": "Job title retrieved successfully",

  "message": "Job title created successfully",  "data": {

  "data": {    "id": 1,

    "id": 1,    "title": "Software Developer",

    "title": "Software Developer",    "created_at": "2025-11-10T08:00:00Z",

    "created_at": "2025-11-10T08:00:00Z",    "updated_at": "2025-11-10T08:00:00Z"

    "updated_at": "2025-11-10T08:00:00Z"  }

  }}

}```

```

**Error Response (404 Not Found):**

---```json

{

### 4. Update Job Title  "success": false,

**PUT/PATCH** `/job-titles/{id}/`  "message": "Job title not found",

  "error": "NOT_FOUND",

**Request:**  "details": "The requested job title does not exist"

```json}

{```

  "title": "Senior Software Developer"

}**cURL Example:**

``````bash

curl -X GET "{{baseUrl}}/api/cv-management/job-titles/1/" \

**Response:**  -H "Authorization: Bearer YOUR_JWT_TOKEN"

```json```

{

  "success": true,---

  "message": "Job title updated successfully",

  "data": {### 3. Create Job Title

    "id": 1,

    "title": "Senior Software Developer",**Endpoint:** `POST /api/cv-management/job-titles/`

    "created_at": "2025-11-10T08:00:00Z",

    "updated_at": "2025-11-11T10:30:00Z"**Description:** Create a new job title record.

  }

}**Request Body:**

``````json

{

---  "title": "Software Developer"

}

### 5. Delete Job Title```

**DELETE** `/job-titles/{id}/`

**Fields:**

**Response:**- `title` (string, required, unique): The job title name

```json

{**Success Response (201 Created):**

  "success": true,```json

  "message": "Job title deleted successfully"{

}  "success": true,

```  "message": "Job title created successfully",

  "data": {

---    "id": 1,

    "title": "Software Developer",

## CV Data Endpoints    "created_at": "2025-11-10T08:00:00Z",

    "updated_at": "2025-11-10T08:00:00Z"

### 1. List All CVs  }

**GET** `/cvs/`}

```

**Query Parameters:**

- `status` (optional): `pending`, `ongoing`, `selected`, `rejected`**Error Response (400 Bad Request):**

```json

**Example:** `/cvs/?status=pending`{

  "success": false,

**Response:**  "message": "Invalid data provided",

```json  "error": "VALIDATION_ERROR",

{  "details": {

  "success": true,    "title": ["This field is required."]

  "message": "Found 25 CV(s)",  }

  "data": [}

    {```

      "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",

      "name": "John Doe",**cURL Example:**

      "gender": "M",```bash

      "dob": "1990-05-15",curl -X POST "{{baseUrl}}/api/cv-management/job-titles/" \

      "job_title": 1,  -H "Authorization: Bearer YOUR_JWT_TOKEN" \

      "place": "Kochi",  -H "Content-Type: application/json" \

      "district": "Ernakulam",  -d '{"title": "Software Developer"}'

      "education": "Bachelor of Computer Science",```

      "experience": "5 years",

      "email": "john.doe@example.com",---

      "phone_number": "+91 9876543210",

      "address": "123 Main Street, Kochi, Kerala",### 4. Update Job Title

      "cv_file": "/media/cvs/john_doe_cv.pdf",

      "cv_source": "LinkedIn",**Endpoint:** `PUT /api/cv-management/job-titles/{id}/` or `PATCH /api/cv-management/job-titles/{id}/`

      "interview_status": "pending",

      "remarks": "Strong technical background",**Description:** Update an existing job title. Use PUT for full update or PATCH for partial update.

      "created_by": "admin",

      "created_at": "2025-11-10T08:00:00Z",**Request Body:**

      "updated_at": "2025-11-10T08:00:00Z"```json

    }{

  ]  "title": "Senior Software Developer"

}}

``````



---**Success Response (200 OK):**

```json

### 2. Get Single CV{

**GET** `/cvs/{id}/`  "success": true,

  "message": "Job title updated successfully",

**Response:**  "data": {

```json    "id": 1,

{    "title": "Senior Software Developer",

  "success": true,    "created_at": "2025-11-10T08:00:00Z",

  "message": "CV retrieved successfully",    "updated_at": "2025-11-11T10:30:00Z"

  "data": {  }

    "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",}

    "name": "John Doe",```

    "gender": "M",

    "dob": "1990-05-15",**Error Response (404 Not Found):**

    "job_title": 1,```json

    "place": "Kochi",{

    "district": "Ernakulam",  "success": false,

    "education": "Bachelor of Computer Science",  "message": "Job title not found",

    "experience": "5 years",  "error": "NOT_FOUND",

    "email": "john.doe@example.com",  "details": "The requested job title does not exist"

    "phone_number": "+91 9876543210",}

    "address": "123 Main Street, Kochi, Kerala",```

    "cv_file": "/media/cvs/john_doe_cv.pdf",

    "cv_source": "LinkedIn",**Error Response (400 Bad Request):**

    "interview_status": "pending",```json

    "remarks": "Strong technical background",{

    "created_by": "admin",  "success": false,

    "created_at": "2025-11-10T08:00:00Z",  "message": "Invalid data provided",

    "updated_at": "2025-11-10T08:00:00Z"  "error": "VALIDATION_ERROR",

  }  "details": {

}    "title": ["Job title with this name already exists."]

```  }

}

---```



### 3. Create CV**cURL Example:**

**POST** `/cvs/````bash

curl -X PATCH "{{baseUrl}}/api/cv-management/job-titles/1/" \

**Content-Type:** `application/json` or `multipart/form-data` (for file upload)  -H "Authorization: Bearer YOUR_JWT_TOKEN" \

  -H "Content-Type: application/json" \

**Request:**  -d '{"title": "Senior Software Developer"}'

```json```

{

  "name": "John Doe",---

  "email": "john.doe@example.com",

  "phone_number": "+91 9876543210",### 5. Delete Job Title

  "job_title": 1,

  "place": "Kochi",**Endpoint:** `DELETE /api/cv-management/job-titles/{id}/`

  "district": "Ernakulam",

  "education": "Bachelor of Computer Science",**Description:** Delete a job title record.

  "experience": "5 years",

  "gender": "M",**Success Response (200 OK):**

  "dob": "1990-05-15",```json

  "address": "123 Main Street, Kochi, Kerala",{

  "cv_source": "LinkedIn",  "success": true,

  "remarks": "Strong technical background"  "message": "Job title deleted successfully"

}}

``````



**Required Fields:****Error Response (404 Not Found):**

- `name`, `email`, `phone_number`, `job_title`, `place`, `education`, `experience````json

{

**Response:**  "success": false,

```json  "message": "Job title not found",

{  "error": "NOT_FOUND",

  "success": true,  "details": "The requested job title does not exist"

  "message": "CV data created successfully for John Doe",}

  "data": {```

    "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",

    "name": "John Doe",**cURL Example:**

    "gender": "M",```bash

    "dob": "1990-05-15",curl -X DELETE "{{baseUrl}}/api/cv-management/job-titles/1/" \

    "job_title": 1,  -H "Authorization: Bearer YOUR_JWT_TOKEN"

    "place": "Kochi",```

    "district": "Ernakulam",

    "education": "Bachelor of Computer Science",---

    "experience": "5 years",

    "email": "john.doe@example.com",## CV Data Endpoints

    "phone_number": "+91 9876543210",

    "address": "123 Main Street, Kochi, Kerala",### 1. List All CVs

    "cv_file": null,

    "cv_source": "LinkedIn",**Endpoint:** `GET /api/cv-management/cvs/`

    "interview_status": "pending",

    "remarks": "Strong technical background",**Description:** Retrieve a list of all CV records with optional status filtering.

    "created_by": "admin",

    "created_at": "2025-11-10T08:00:00Z",**Query Parameters:**

    "updated_at": "2025-11-10T08:00:00Z"- `status` (optional): Filter by interview status (`pending`, `ongoing`, `selected`, `rejected`)

  }

}**Success Response (200 OK):**

``````json

{

---  "success": true,

  "message": "Found 25 CV(s)",

### 4. Update CV  "data": [

**PUT/PATCH** `/cvs/{id}/`    {

      "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",

**Request:**      "name": "John Doe",

```json      "gender": "M",

{      "dob": "1990-05-15",

  "experience": "7 years",      "job_title": 1,

  "interview_status": "selected",      "place": "Kochi",

  "remarks": "Excellent candidate, hired"      "district": "Ernakulam",

}      "education": "Bachelor of Computer Science",

```      "experience": "5 years",

      "email": "john.doe@example.com",

**Response:**      "phone_number": "+91 9876543210",

```json      "address": "123 Main Street, Kochi, Kerala",

{      "cv_file": "/media/cvs/john_doe_cv.pdf",

  "success": true,      "cv_source": "LinkedIn",

  "message": "CV data updated successfully",      "interview_status": "pending",

  "data": {      "remarks": "Strong technical background",

    "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",      "created_by": "admin",

    "name": "John Doe",      "created_at": "2025-11-10T08:00:00Z",

    "experience": "7 years",      "updated_at": "2025-11-10T08:00:00Z"

    "interview_status": "selected",    }

    "remarks": "Excellent candidate, hired",  ]

    "updated_at": "2025-11-11T14:30:00Z"}

  }```

}

```**Error Response (500 Internal Server Error):**

```json

---{

  "success": false,

### 5. Delete CV  "message": "Error retrieving CV data",

**DELETE** `/cvs/{id}/`  "error": "INTERNAL_ERROR",

  "details": "Please try again later"

**Response:**}

```json```

{

  "success": true,**cURL Example:**

  "message": "CV data deleted successfully"```bash

}# Get all CVs

```curl -X GET "{{baseUrl}}/api/cv-management/cvs/" \

  -H "Authorization: Bearer YOUR_JWT_TOKEN"

---

# Filter by status

## Error Responsescurl -X GET "{{baseUrl}}/api/cv-management/cvs/?status=pending" \

  -H "Authorization: Bearer YOUR_JWT_TOKEN"

### Validation Error (400)```

```json

{---

  "success": false,

  "message": "Invalid data provided",### 2. Get Single CV

  "error": "VALIDATION_ERROR",

  "details": {**Endpoint:** `GET /api/cv-management/cvs/{id}/`

    "email": ["This field is required."]

  }**Description:** Retrieve detailed information of a specific CV record.

}

```**Success Response (200 OK):**

```json

### Not Found (404){

```json  "success": true,

{  "message": "CV retrieved successfully",

  "success": false,  "data": {

  "message": "CV not found",    "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",

  "error": "NOT_FOUND",    "name": "John Doe",

  "details": "The requested CV does not exist"    "gender": "M",

}    "dob": "1990-05-15",

```    "job_title": 1,

    "place": "Kochi",

### Server Error (500)    "district": "Ernakulam",

```json    "education": "Bachelor of Computer Science",

{    "experience": "5 years",

  "success": false,    "email": "john.doe@example.com",

  "message": "Error retrieving CV data",    "phone_number": "+91 9876543210",

  "error": "INTERNAL_ERROR",    "address": "123 Main Street, Kochi, Kerala",

  "details": "Please try again later"    "cv_file": "/media/cvs/john_doe_cv.pdf",

}    "cv_source": "LinkedIn",

```    "interview_status": "pending",

    "remarks": "Strong technical background",

---    "created_by": "admin",

    "created_at": "2025-11-10T08:00:00Z",

## Field Reference    "updated_at": "2025-11-10T08:00:00Z"

  }

### Gender}

- `M` - Male, `F` - Female, `O` - Other (default)```



### District (Kerala)**Error Response (404 Not Found):**

Alappuzha, Ernakulam, Idukki, Kannur, Kasaragod, Kollam, Kottayam, Kozhikode, Malappuram, Palakkad, Pathanamthitta, Thiruvananthapuram, Thrissur, Wayanad, Other```json

{

### Interview Status  "success": false,

- `pending` (default), `ongoing`, `selected`, `rejected`  "message": "CV not found",

  "error": "NOT_FOUND",

---  "details": "The requested CV does not exist"

}

## Notes```



- All CV records use UUID as primary key**cURL Example:**

- Email addresses must be unique```bash

- `created_by` is automatically set to authenticated usercurl -X GET "{{baseUrl}}/api/cv-management/cvs/ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914/" \

- Job title must exist before creating CV  -H "Authorization: Bearer YOUR_JWT_TOKEN"

- File uploads supported for `cv_file` (PDF, DOC, DOCX)```



------



**Last Updated:** November 11, 2025### 3. Create CV Record


**Endpoint:** `POST /api/cv-management/cvs/`

**Description:** Create a new CV record. Automatically sets `created_by` to the authenticated user.

**Content-Type:** `multipart/form-data` (for file upload) or `application/json`

**Request Body Fields:**

**Required Fields:**
- `name` (string): Candidate's full name
- `email` (string, unique): Email address
- `phone_number` (string): Contact number
- `job_title` (integer): Job Title ID
- `place` (string): Location/City
- `education` (string): Educational qualification
- `experience` (string): Work experience

**Optional Fields:**
- `gender` (string): M|F|O (default: O)
- `dob` (date): Date of birth (YYYY-MM-DD)
- `district` (string): Kerala district (default: Wayanad)
- `address` (string): Full address
- `cv_file` (file): CV document (PDF/DOC/DOCX)
- `cv_source` (string): Source of CV (default: Direct)
- `interview_status` (string): pending|ongoing|selected|rejected (default: pending)
- `remarks` (string): Additional notes

**Request Example (JSON):**
```json
{
  "name": "John Doe",
  "gender": "M",
  "dob": "1990-05-15",
  "job_title": 1,
  "place": "Kochi",
  "district": "Ernakulam",
  "education": "Bachelor of Computer Science",
  "experience": "5 years",
  "email": "john.doe@example.com",
  "phone_number": "+91 9876543210",
  "address": "123 Main Street, Kochi, Kerala",
  "cv_source": "LinkedIn",
  "remarks": "Strong technical background"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "CV data created successfully for John Doe",
  "data": {
    "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
    "name": "John Doe",
    "gender": "M",
    "dob": "1990-05-15",
    "job_title": 1,
    "place": "Kochi",
    "district": "Ernakulam",
    "education": "Bachelor of Computer Science",
    "experience": "5 years",
    "email": "john.doe@example.com",
    "phone_number": "+91 9876543210",
    "address": "123 Main Street, Kochi, Kerala",
    "cv_file": "/media/cvs/john_doe_cv.pdf",
    "cv_source": "LinkedIn",
    "interview_status": "pending",
    "remarks": "Strong technical background",
    "created_by": "admin",
    "created_at": "2025-11-10T08:00:00Z",
    "updated_at": "2025-11-10T08:00:00Z"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "email": ["This field is required."],
    "phone_number": ["This field is required."]
  }
}
```

**Error Response (400 Bad Request - Duplicate Email):**
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "email": ["User cv data with this Email Address already exists."]
  }
}
```

**cURL Example (JSON):**
```bash
curl -X POST "{{baseUrl}}/api/cv-management/cvs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+91 9876543210",
    "job_title": 1,
    "place": "Kochi",
    "district": "Ernakulam",
    "education": "Bachelor of Computer Science",
    "experience": "5 years"
  }'
```

**cURL Example (with File):**
```bash
curl -X POST "{{baseUrl}}/api/cv-management/cvs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=John Doe" \
  -F "email=john.doe@example.com" \
  -F "phone_number=+91 9876543210" \
  -F "job_title=1" \
  -F "place=Kochi" \
  -F "education=Bachelor of Computer Science" \
  -F "experience=5 years" \
  -F "cv_file=@/path/to/cv.pdf"
```

---

### 4. Update CV Record

**Endpoint:** `PUT /api/cv-management/cvs/{id}/` or `PATCH /api/cv-management/cvs/{id}/`

**Description:** Update an existing CV record. Use PUT for full update or PATCH for partial update.

**Content-Type:** `multipart/form-data` (for file updates) or `application/json`

**Request Body:** Same fields as create endpoint. All fields are optional for partial updates (PATCH).

**Request Example:**
```json
{
  "experience": "7 years",
  "interview_status": "selected",
  "remarks": "Excellent candidate, hired"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "CV data updated successfully",
  "data": {
    "id": "ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914",
    "name": "John Doe",
    "gender": "M",
    "dob": "1990-05-15",
    "job_title": 1,
    "place": "Kochi",
    "district": "Ernakulam",
    "education": "Bachelor of Computer Science",
    "experience": "7 years",
    "email": "john.doe@example.com",
    "phone_number": "+91 9876543210",
    "address": "123 Main Street, Kochi, Kerala",
    "cv_file": "/media/cvs/john_doe_cv.pdf",
    "cv_source": "LinkedIn",
    "interview_status": "selected",
    "remarks": "Excellent candidate, hired",
    "created_by": "admin",
    "created_at": "2025-11-10T08:00:00Z",
    "updated_at": "2025-11-11T14:30:00Z"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "message": "CV not found",
  "error": "NOT_FOUND",
  "details": "The requested CV does not exist"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "email": ["Enter a valid email address."]
  }
}
```

**cURL Example:**
```bash
curl -X PATCH "{{baseUrl}}/api/cv-management/cvs/ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "experience": "7 years",
    "interview_status": "selected",
    "remarks": "Excellent candidate, hired"
  }'
```

---

### 5. Delete CV Record

**Endpoint:** `DELETE /api/cv-management/cvs/{id}/`

**Description:** Delete a CV record permanently.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "CV data deleted successfully"
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "message": "CV not found",
  "error": "NOT_FOUND",
  "details": "The requested CV does not exist"
}
```

**cURL Example:**
```bash
curl -X DELETE "{{baseUrl}}/api/cv-management/cvs/ea3d16d9-dbd6-4fc3-9d40-b35f6dcc5914/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Response Format

### Success Response Structure
```json
{
  "success": true,
  "message": "Descriptive success message",
  "data": {
    // Response data object or array
  }
}
```

### Error Response Structure
```json
{
  "success": false,
  "message": "User-friendly error message",
  "error": "ERROR_CODE",
  "details": "Additional error details or validation errors"
}
```

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid input data | 400 |
| `NOT_FOUND` | Resource not found | 404 |
| `INTERNAL_ERROR` | Server error | 500 |

---

## Field Details

### Gender Choices
- `M`: Male
- `F`: Female  
- `O`: Other

### District Choices (Kerala)
- Alappuzha, Ernakulam, Idukki, Kannur, Kasaragod, Kollam, Kottayam, Kozhikode, Malappuram, Palakkad, Pathanamthitta, Thiruvananthapuram, Thrissur, Wayanad, Other

### Interview Status Choices
- `pending`: Pending (default)
- `ongoing`: Interview in Progress
- `selected`: Selected/Hired
- `rejected`: Rejected

### Job Title
Expects the integer ID of a JobTitle record. Fetch available job titles from `/api/cv-management/job-titles/` endpoint first.

### File Upload
- Supported formats: PDF, DOC, DOCX (for CV files)
- Storage: Cloudflare R2 (if configured) or local media storage
- `cv_file` field returns the full URL to access the uploaded file
- Maximum file size: Check server configuration

---

## Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 OK | Success (GET, PUT, PATCH, DELETE) |
| 201 Created | Success (POST - resource created) |
| 400 Bad Request | Validation errors or invalid data |
| 401 Unauthorized | Missing or invalid JWT token |
| 404 Not Found | Resource not found |
| 500 Internal Server Error | Server error |

---

## Important Notes

1. **Authentication**: All endpoints require JWT token in Authorization header
2. **UUID Primary Keys**: All CV records use UUID for secure identification
3. **Email Uniqueness**: Email addresses must be unique across all CV records
4. **Automatic Fields**: `created_by` is automatically set to the authenticated user
5. **Timestamps**: All datetime fields use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
6. **File URLs**: Returned file URLs are absolute and ready to use
7. **Transaction Safety**: Create/Update/Delete operations use database transactions
8. **Logging**: All operations are logged with user information for audit trails
9. **Filtering**: List endpoint supports `?status=<value>` query parameter
10. **Job Title Reference**: Must create job titles before creating CVs

---

## Quick Start Examples

### 1. Create a Job Title
```bash
curl -X POST "{{baseUrl}}/api/cv-management/job-titles/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Software Developer"}'
```

### 2. Get All Job Titles
```bash
curl -X GET "{{baseUrl}}/api/cv-management/job-titles/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Create a CV Record
```bash
curl -X POST "{{baseUrl}}/api/cv-management/cvs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+91 9876543210",
    "job_title": 1,
    "place": "Kochi",
    "district": "Ernakulam",
    "education": "Bachelor of Computer Science",
    "experience": "5 years"
  }'
```

### 4. Get All CVs
```bash
curl -X GET "{{baseUrl}}/api/cv-management/cvs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. Filter CVs by Status
```bash
curl -X GET "{{baseUrl}}/api/cv-management/cvs/?status=pending" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 6. Update CV Status
```bash
curl -X PATCH "{{baseUrl}}/api/cv-management/cvs/{cv_id}/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interview_status": "selected"}'
```

---

## Changelog

### Version 2.0 (November 11, 2025)
- ✅ Standardized response format across all endpoints
- ✅ Added comprehensive error handling with error codes
- ✅ Added message field to all responses
- ✅ Implemented logging for all operations
- ✅ Added transaction support for data consistency
- ✅ Added retrieve (GET single) endpoints
- ✅ Added status filtering for CV list endpoint
- ✅ Improved documentation with detailed examples
- ✅ Updated interview_status choices (pending, ongoing, selected, rejected)

### Version 1.0
- Initial release with basic CRUD operations

---

**Last Updated:** November 11, 2025  
**API Version:** 2.0

### Update a CV
```bash
curl -X PUT http://127.0.0.1:8000/api/cv-management/cvs/{uuid}/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"experience": "6 years"}'
```

### Delete a CV
```bash
curl -X DELETE http://127.0.0.1:8000/api/cv-management/cvs/{uuid}/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```