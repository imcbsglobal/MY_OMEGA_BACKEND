# Certificate Hub API Documentation

Base URL: `/api/certificate/`

## Authentication
All endpoints require JWT authentication.
```
Authorization: Bearer <access_token>
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/employees/` | Get list of all employees |
| GET | `/salary-certificates/` | List all salary certificates |
| POST | `/salary-certificates/` | Create new salary certificate |
| GET | `/salary-certificates/{id}/` | Get specific salary certificate |
| PUT | `/salary-certificates/{id}/` | Full update salary certificate |
| PATCH | `/salary-certificates/{id}/` | Partial update salary certificate |
| DELETE | `/salary-certificates/{id}/` | Delete salary certificate |
| GET | `/experience-certificates/` | List all experience certificates |
| POST | `/experience-certificates/` | Create new experience certificate |
| GET | `/experience-certificates/{id}/` | Get specific experience certificate |
| PUT | `/experience-certificates/{id}/` | Full update experience certificate |
| PATCH | `/experience-certificates/{id}/` | Partial update experience certificate |
| DELETE | `/experience-certificates/{id}/` | Delete experience certificate |

---

## 1. Get Employee List

**Endpoint:** `GET /api/certificate/employees/`

**Description:** Get all active employees available for certificate creation.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Found 5 active employee(s)",
  "data": [
    {
      "id": 1,
      "employee_id": "EMP001",
      "name": "John Doe",
      "email": "john@example.com",
      "designation": "Software Engineer",
      "department": "IT",
      "date_of_joining": "2024-01-15",
      "location": "New York"
    },
    {
      "id": 2,
      "employee_id": "EMP002",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "designation": "HR Manager",
      "department": "Human Resources",
      "date_of_joining": "2023-05-20",
      "location": "Boston"
    }
  ]
}
```

---

## 2. List Salary Certificates

**Endpoint:** `GET /api/certificate/salary-certificates/`

**Description:** Retrieve all salary certificates with optional filtering.

**Query Parameters:**
- `employee` (optional): Filter by employee ID

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Example:**
```
GET /api/certificate/salary-certificates/?employee=3
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Salary certificate(s)",
  "data": [
    {
      "id": 1,
      "employee": 1,
      "emp_name": "John Doe",
      "emp_email": "john@example.com",
      "emp_designation": "Software Engineer",
      "emp_department": "IT",
      "emp_joining_date": "2024-01-15",
      "emp_location": "New York",
      "salary": "50000.00",
      "issued_date": "2024-11-24",
      "generated_by": 2,
      "generated_by_name": "Admin User"
    }
  ]
}
```

---

## 3. Create Salary Certificate

**Endpoint:** `POST /api/certificate/salary-certificates/`

**Description:** Create a new salary certificate for an employee.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "employee": 3,
  "salary": 50000.00
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Salary certificate created for John Doe",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_joining_date": "2024-01-15",
    "emp_location": "New York",
    "salary": "50000.00",
    "issued_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

**Validation Errors (400 Bad Request):**
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "salary": ["Salary must be greater than zero."]
  }
}
```

---

## 4. Get Salary Certificate Details

**Endpoint:** `GET /api/certificate/salary-certificates/{id}/`

**Description:** Retrieve a specific salary certificate by ID.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Salary certificate retrieved successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_joining_date": "2024-01-15",
    "emp_location": "New York",
    "salary": "50000.00",
    "issued_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

**Error (404 Not Found):**
```json
{
  "success": false,
  "message": "Salary certificate not found",
  "error": "NOT_FOUND"
}
```

---

## 5. Update Salary Certificate (Full)

**Endpoint:** `PUT /api/certificate/salary-certificates/{id}/`

**Description:** Fully update a salary certificate.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "employee": 3,
  "salary": 55000.00
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Salary certificate updated successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_joining_date": "2024-01-15",
    "emp_location": "New York",
    "salary": "55000.00",
    "issued_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

---

## 6. Update Salary Certificate (Partial)

**Endpoint:** `PATCH /api/certificate/salary-certificates/{id}/`

**Description:** Partially update a salary certificate.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "salary": 52000.00
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Salary certificate updated successfully",
  "data": {
    "id": 1,
    "employee": 3,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_address": "123 Main St, City, Country",
    "emp_joining_date": "2024-01-15",
    "emp_job_title": "Software Engineer",
    "salary": "52000.00",
    "issued_date": "2024-11-21",
    "generated_by": 1,
    "generated_by_name": "Admin User"
  }
}
```

---

## 7. Delete Salary Certificate

**Endpoint:** `DELETE /api/certificate/salary-certificates/{id}/`

**Description:** Delete a salary certificate.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Salary certificate for John Doe deleted successfully"
}
```

---

## 8. List Experience Certificates

**Endpoint:** `GET /api/certificate/experience-certificates/`

**Description:** Retrieve all experience certificates with optional filtering.

**Query Parameters:**
- `employee` (optional): Filter by employee ID

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Example:**
```
GET /api/certificate/experience-certificates/?employee=3
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Experience certificate(s) retrieved successfully",
  "data": [
    {
      "id": 1,
      "employee": 1,
      "emp_name": "John Doe",
      "emp_email": "john@example.com",
      "emp_designation": "Software Engineer",
      "emp_department": "IT",
      "emp_location": "New York",
      "offer_letter": 5,
      "offer_letter_joining": "2024-01-15",
      "joining_date": "2024-01-15",
      "issue_date": "2024-11-24",
      "generated_by": 2,
      "generated_by_name": "Admin User"
    }
  ]
}
```

---

## 9. Create Experience Certificate

**Endpoint:** `POST /api/certificate/experience-certificates/`

**Description:** Create a new experience certificate for an employee.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (with offer letter):**
```json
{
  "employee": 3,
  "offer_letter": 5
}
```

**Request Body (without offer letter - manual joining date):**
```json
{
  "employee": 3,
  "joining_date": "2024-01-15"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Experience certificate created for John Doe",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_location": "New York",
    "offer_letter": 5,
    "offer_letter_joining": "2024-01-15",
    "joining_date": "2024-01-15",
    "issue_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

**Validation Errors (400 Bad Request):**
```json
{
  "success": false,
  "message": "Invalid data provided",
  "error": "VALIDATION_ERROR",
  "details": {
    "joining_date": ["Joining date cannot be in the future."]
  }
}
```

---

## 10. Get Experience Certificate Details

**Endpoint:** `GET /api/certificate/experience-certificates/{id}/`

**Description:** Retrieve a specific experience certificate by ID.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Experience certificate retrieved successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_location": "New York",
    "offer_letter": 5,
    "offer_letter_joining": "2024-01-15",
    "joining_date": "2024-01-15",
    "issue_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

**Error (404 Not Found):**
```json
{
  "success": false,
  "message": "Experience certificate not found",
  "error": "NOT_FOUND"
}
```

---

## 11. Update Experience Certificate (Full)

**Endpoint:** `PUT /api/certificate/experience-certificates/{id}/`

**Description:** Fully update an experience certificate.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "employee": 3,
  "offer_letter": 5,
  "joining_date": "2024-01-15"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Experience certificate updated successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_location": "New York",
    "offer_letter": 5,
    "offer_letter_joining": "2024-01-15",
    "joining_date": "2024-01-15",
    "issue_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

---

## 12. Update Experience Certificate (Partial)

**Endpoint:** `PATCH /api/certificate/experience-certificates/{id}/`

**Description:** Partially update an experience certificate.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "joining_date": "2024-02-01"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Experience certificate updated successfully",
  "data": {
    "id": 1,
    "employee": 1,
    "emp_name": "John Doe",
    "emp_email": "john@example.com",
    "emp_designation": "Software Engineer",
    "emp_department": "IT",
    "emp_location": "New York",
    "offer_letter": 5,
    "offer_letter_joining": "2024-01-15",
    "joining_date": "2024-02-01",
    "issue_date": "2024-11-24",
    "generated_by": 2,
    "generated_by_name": "Admin User"
  }
}
```

---

## 13. Delete Experience Certificate

**Endpoint:** `DELETE /api/certificate/experience-certificates/{id}/`

**Description:** Delete an experience certificate.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Experience certificate for John Doe deleted successfully"
}
```

---

## Data Models

### Salary Certificate
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Integer | Auto | Primary key |
| employee | Integer | Yes | Employee ID (FK to Employee) |
| salary | Decimal | Yes | Salary amount (must be > 0) |
| issued_date | Date | Auto | Certificate issue date |
| generated_by | Integer | Auto | User who generated certificate (FK to AppUser) |
| emp_name | String | Read-only | Employee full name |
| emp_email | String | Read-only | Employee email |
| emp_designation | String | Read-only | Employee designation |
| emp_department | String | Read-only | Employee department |
| emp_joining_date | Date | Read-only | Employee joining date |
| emp_location | String | Read-only | Employee location |

### Experience Certificate
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | Integer | Auto | Primary key |
| employee | Integer | No | Employee ID (FK to Employee) |
| offer_letter | Integer | No | Offer letter ID (FK to OfferLetter) |
| joining_date | Date | No | Manual joining date (fallback) |
| issue_date | Date | Auto | Certificate issue date |
| generated_by | Integer | Auto | User who generated certificate (FK to AppUser) |
| emp_name | String | Read-only | Employee full name |
| emp_email | String | Read-only | Employee email |
| emp_designation | String | Read-only | Employee designation |
| emp_department | String | Read-only | Employee department |
| emp_location | String | Read-only | Employee location |

**Note:** If `offer_letter` is provided, `joining_date` is automatically populated from the offer letter's `joining_data` field on save.

---

## Error Response Format

All error responses follow this structure:

```json
{
  "success": false,
  "message": "Error message description",
  "error": "ERROR_CODE",
  "details": {
    "field_name": ["Error detail"]
  }
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` (400) - Invalid input data
- `NOT_FOUND` (404) - Resource not found
- `UNAUTHORIZED` (401) - Missing or invalid authentication

---

## Business Rules

### Salary Certificate
1. `salary` must be greater than zero
2. `generated_by` is automatically set to the authenticated user
3. Certificates are ordered by issued_date (newest first)

### Experience Certificate
1. If `offer_letter` is provided and `joining_date` is not, the joining date is automatically copied from the offer letter on save
2. If `joining_date` is provided manually, it cannot be in the future
3. `employee` can be null (SET_NULL on delete)
4. `generated_by` is automatically set to the authenticated user
5. Certificates are ordered by issue_date (newest first)
