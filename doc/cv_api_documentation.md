# CV Management API Documentation

## Base URL
```
https://your-domain.com/api/cv/cvs/
```

## Authentication
All endpoints require JWT authentication. Include the following header in your requests:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Get All CVs
**Endpoint:** `GET /api/cv/cvs/`  
**Description:** Retrieve a list of all CV records.  
**Permissions:** Authenticated users only.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "uuid": "string (UUID)",
      "name": "string",
      "gender": "M|F|O",
      "dob": "YYYY-MM-DD",
      "job_title": integer (JobTitle ID),
      "place": "string",
      "district": "string (Kerala district)",
      "education": "string",
      "experience": "string",
      "email": "string",
      "phone_number": "string",
      "address": "string",
      "cv_file": "string (file URL)",
      "cv_source": "string",
      "interview_status": "yes|no|pending",
      "remarks": "string",
      "created_by": "string (username)",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
}
```

### 2. Get Single CV
**Endpoint:** `GET /api/cv/cvs/{uuid}/`  
**Description:** Retrieve a specific CV record by its UUID.  
**Permissions:** Authenticated users only.  
**Parameters:**  
- `uuid`: UUID of the CV record

**Response:**
```json
{
  "success": true,
  "data": {
    "uuid": "string (UUID)",
    "name": "string",
    "gender": "M|F|O",
    "dob": "YYYY-MM-DD",
    "job_title": integer (JobTitle ID),
    "place": "string",
    "district": "string (Kerala district)",
    "education": "string",
    "experience": "string",
    "email": "string",
    "phone_number": "string",
    "address": "string",
    "cv_file": "string (file URL)",
    "cv_source": "string",
    "interview_status": "yes|no|pending",
    "remarks": "string",
    "created_by": "string (username)",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

### 3. Upload/Create CV
**Endpoint:** `POST /api/cv/cvs/`  
**Description:** Create a new CV record with file upload.  
**Permissions:** Authenticated users only.  
**Content-Type:** `multipart/form-data`

**Request Body Fields:**
- `name`: string (required)
- `gender`: string (M|F|O, default: O)
- `dob`: date (YYYY-MM-DD, optional)
- `job_title`: integer (JobTitle ID, required) - Note: Currently expects JobTitle ID, not string
- `place`: string (required)
- `district`: string (Kerala district choice, default: Wayanad)
- `education`: string (required)
- `experience`: string (required)
- `email`: string (required, unique)
- `phone_number`: string (required)
- `address`: string (optional)
- `cv_file`: file (PDF/DOC/DOCX, optional)
- `cv_source`: string (default: Direct)
- `interview_status`: string (yes|no|pending, default: pending)
- `remarks`: string (optional)

**Response:**
```json
{
  "success": true,
  "message": "CV data created successfully",
  "data": {
    "uuid": "string (UUID)",
    "name": "string",
    "gender": "M|F|O",
    "dob": "YYYY-MM-DD",
    "job_title": integer,
    "place": "string",
    "district": "string",
    "education": "string",
    "experience": "string",
    "email": "string",
    "phone_number": "string",
    "address": "string",
    "cv_file": "string (file URL)",
    "cv_source": "string",
    "interview_status": "yes|no|pending",
    "remarks": "string",
    "created_by": "string (username)",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

### 4. Edit/Update CV
**Endpoint:** `PUT /api/cv/cvs/{uuid}/`  
**Description:** Update an existing CV record.  
**Permissions:** Authenticated users only.  
**Parameters:**  
- `uuid`: UUID of the CV record  
**Content-Type:** `multipart/form-data` (for file updates) or `application/json`

**Request Body:** Same fields as create, all optional for partial updates.

**Response:**
```json
{
  "success": true,
  "message": "CV data updated successfully",
  "data": {
    "uuid": "string (UUID)",
    "...": "updated fields"
  }
}
```

### 5. Delete CV
**Endpoint:** `DELETE /api/cv/cvs/{uuid}/`  
**Description:** Delete a CV record.  
**Permissions:** Authenticated users only.  
**Parameters:**  
- `uuid`: UUID of the CV record

**Response:**
```json
{
  "success": true,
  "message": "CV data deleted successfully"
}
```

## Field Details

### Gender Choices
- `M`: Male
- `F`: Female  
- `O`: Other

### District Choices
Kerala districts: Alappuzha, Ernakulam, Idukki, Kannur, Kasaragod, Kollam, Kottayam, Kozhikode, Malappuram, Palakkad, Pathanamthitta, Thiruvananthapuram, Thrissur, Wayanad, Other

### Interview Status Choices
- `yes`: Yes
- `no`: No
- `pending`: Pending

### Job Title
Currently expects the integer ID of a JobTitle record. You may need to fetch available job titles from `/api/cv/job-titles/` endpoint first.

### File Upload
- Supported formats: PDF, DOC, DOCX
- Stored in Cloudflare R2 (if configured) or local storage
- `cv_file` field contains the file URL after upload

## Error Responses
All endpoints return standard HTTP status codes. Common errors:
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: CV record not found
- `400 Bad Request`: Validation errors (includes field-specific error details)
- `500 Internal Server Error`: Server error

## Notes
- All datetime fields are in ISO format
- File URLs are absolute URLs pointing to the stored CV files
- The `created_by` field shows the username of the user who created the record
- UUIDs are used as primary keys for security
- Email addresses must be unique across all CV records