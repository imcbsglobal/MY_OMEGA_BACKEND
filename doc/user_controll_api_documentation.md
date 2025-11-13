    # User Control API Documentation

## Overview
The User Control API manages menu-based access control for the application. It provides endpoints for:
- Managing user menu permissions (Admin only)
- Retrieving hierarchical menu structures
- Fetching personalized menus for authenticated users

**Base URL**: `/api/user-controll/`

**Authentication**: JWT Token required for all endpoints
```
Authorization: Bearer <access_token>
```

---

## Table of Contents
1. [Admin Endpoints](#admin-endpoints)
   - [Get All Users](#1-get-all-users)
   - [Get Complete Menu Tree](#2-get-complete-menu-tree)
   - [Get User Menu Permissions](#3-get-user-menu-permissions)
   - [Set User Menu Permissions](#4-set-user-menu-permissions)
2. [User Endpoints](#user-endpoints)
   - [Get My Menu](#5-get-my-menu)
3. [Field Reference](#field-reference)
4. [Error Handling](#error-handling)

---

## Admin Endpoints

**Permission Required**: `IsSuperAdmin` (Superusers/staff or users with 'user_control' menu access)

### 1. Get All Users

Retrieve a list of all registered users in the system.

**Endpoint**: `GET /api/user-controll/admin/users/`

**Request**:
```http
GET /api/user-controll/admin/users/
Authorization: Bearer <admin_access_token>
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "username": "john.doe",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "is_staff": false,
    "is_superuser": false
  },
  {
    "id": 2,
    "username": "admin",
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@example.com",
    "is_staff": true,
    "is_superuser": true
  }
]
```

**Notes**:
- Users are ordered by `date_joined` (newest first)
- Returns all users including staff and superusers

---

### 2. Get Complete Menu Tree

Retrieve the complete hierarchical menu structure with all active menu items.

**Endpoint**: `GET /api/user-controll/admin/menu-tree/`

**Request**:
```http
GET /api/user-controll/admin/menu-tree/
Authorization: Bearer <admin_access_token>
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "key": "dashboard",
    "name": "Dashboard",
    "path": "/dashboard",
    "icon": "DashboardOutlined",
    "parent": null,
    "order": 1,
    "children": []
  },
  {
    "id": 2,
    "key": "user-management",
    "name": "User Management",
    "path": "/users",
    "icon": "UserOutlined",
    "parent": null,
    "order": 2,
    "children": [
      {
        "id": 3,
        "key": "user-list",
        "name": "User List",
        "path": "/users/list",
        "icon": "UnorderedListOutlined",
        "parent": 2,
        "order": 1,
        "children": []
      },
      {
        "id": 4,
        "key": "user-roles",
        "name": "User Roles",
        "path": "/users/roles",
        "icon": "SafetyOutlined",
        "parent": 2,
        "order": 2,
        "children": []
      }
    ]
  },
  {
    "id": 5,
    "key": "cv-management",
    "name": "CV Management",
    "path": "/cv",
    "icon": "FileTextOutlined",
    "parent": null,
    "order": 3,
    "children": [
      {
        "id": 6,
        "key": "cv-list",
        "name": "CV List",
        "path": "/cv/list",
        "icon": "UnorderedListOutlined",
        "parent": 5,
        "order": 1,
        "children": []
      }
    ]
  }
]
```

**Notes**:
- Only returns active menu items (`is_active=True`)
- Hierarchical structure with nested children
- Root-level items have `parent: null`
- Items ordered by `order` field, then alphabetically

---

### 3. Get User Menu Permissions

Retrieve the list of menu IDs assigned to a specific user.

**Endpoint**: `GET /api/user-controll/admin/user/{user_id}/menus/`

**Request**:
```http
GET /api/user-controll/admin/user/15/menus/
Authorization: Bearer <admin_access_token>
```

**Response** (200 OK):
```json
{
  "menu_ids": [1, 2, 3, 5, 6]
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "User not found"
}
```

**Notes**:
- Returns only directly assigned menu IDs
- Does not include auto-assigned parent menus

---

### 4. Set User Menu Permissions

Assign or update menu permissions for a specific user. Automatically includes parent menus when child menus are selected.

**Endpoint**: `POST /api/user-controll/admin/user/{user_id}/menus/`

**Request**:
```http
POST /api/user-controll/admin/user/15/menus/
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "menu_ids": [3, 4, 6]
}
```

**Response** (200 OK):
```json
{
  "ok": true,
  "menu_ids": [1, 2, 3, 4, 5, 6],
  "message": "Successfully updated menu permissions for john.doe@example.com"
}
```

**Behavior**:
- **Auto-includes parent menus**: If you assign menu ID `6` (child of `5`), the system automatically adds menu ID `5`
- **Replaces all existing permissions**: Previous menu assignments are deleted and replaced with new ones
- **Empty array allowed**: Passing `{"menu_ids": []}` removes all menu permissions

**Example - Hierarchical Auto-Assignment**:

Request:
```json
{
  "menu_ids": [6]
}
```
Response:
```json
{
  "ok": true,
  "menu_ids": [5, 6],
  "message": "Successfully updated menu permissions for john.doe@example.com"
}
```
**Explanation**: Menu `6` ("CV List") is a child of menu `5` ("CV Management"), so menu `5` is automatically included.

**Error Responses**:

**User Not Found** (404):
```json
{
  "detail": "User not found"
}
```

**Invalid Menu IDs** (400):
```json
{
  "detail": "Invalid menu IDs: {99, 100}"
}
```

**Invalid Request Data** (400):
```json
{
  "detail": "Invalid data",
  "errors": {
    "menu_ids": ["This field is required."]
  }
}
```

**Server Error** (500):
```json
{
  "detail": "Error saving menus: <error_message>"
}
```

**Notes**:
- Atomic operation: Either all changes succeed or none are applied
- Validates all menu IDs exist before applying changes
- Deletes existing permissions and recreates them (not incremental)

---

## User Endpoints

### 5. Get My Menu

Retrieve the personalized menu tree for the currently authenticated user. Menu structure is filtered based on user permissions.

**Endpoint**: `GET /api/user-controll/my-menu/`

**Request**:
```http
GET /api/user-controll/my-menu/
Authorization: Bearer <access_token>
```

**Response - Django Superuser** (200 OK):
```json
{
  "menu": [
    {
      "id": 1,
      "key": "dashboard",
      "name": "Dashboard",
      "path": "/dashboard",
      "icon": "DashboardOutlined",
      "order": 1,
      "children": []
    },
    {
      "id": 2,
      "key": "user-management",
      "name": "User Management",
      "path": "/users",
      "icon": "UserOutlined",
      "order": 2,
      "children": [
        {
          "id": 3,
          "key": "user-list",
          "name": "User List",
          "path": "/users/list",
          "icon": "UnorderedListOutlined",
          "order": 1,
          "children": []
        },
        {
          "id": 4,
          "key": "user-roles",
          "name": "User Roles",
          "path": "/users/roles",
          "icon": "SafetyOutlined",
          "order": 2,
          "children": []
        }
      ]
    },
    {
      "id": 5,
      "key": "cv-management",
      "name": "CV Management",
      "path": "/cv",
      "icon": "FileTextOutlined",
      "order": 3,
      "children": [
        {
          "id": 6,
          "key": "cv-list",
          "name": "CV List",
          "path": "/cv/list",
          "icon": "UnorderedListOutlined",
          "order": 1,
          "children": []
        }
      ]
    }
  ],
  "is_django_superuser": true,
  "is_app_admin": false,
  "user_level": "User"
}
```

**Response - Regular User with Permissions** (200 OK):
```json
{
  "menu": [
    {
      "id": 1,
      "key": "dashboard",
      "name": "Dashboard",
      "path": "/dashboard",
      "icon": "DashboardOutlined",
      "order": 1,
      "children": []
    },
    {
      "id": 5,
      "key": "cv-management",
      "name": "CV Management",
      "path": "/cv",
      "icon": "FileTextOutlined",
      "order": 3,
      "children": [
        {
          "id": 6,
          "key": "cv-list",
          "name": "CV List",
          "path": "/cv/list",
          "icon": "UnorderedListOutlined",
          "order": 1,
          "children": []
        }
      ]
    }
  ],
  "is_django_superuser": false,
  "is_app_admin": false,
  "user_level": "User"
}
```

**Response - User with No Menu Permissions** (200 OK):
```json
{
  "menu": [],
  "is_django_superuser": false,
  "is_app_admin": false,
  "user_level": "User",
  "message": "No menus assigned. Contact administrator."
}
```

**Response - App Admin (Super Admin/Admin)** (200 OK):
```json
{
  "menu": [
    {
      "id": 1,
      "key": "dashboard",
      "name": "Dashboard",
      "path": "/dashboard",
      "icon": "DashboardOutlined",
      "order": 1,
      "children": []
    }
  ],
  "is_django_superuser": false,
  "is_app_admin": true,
  "user_level": "Super Admin"
}
```

**Authorization Behavior**:
- **Django Superuser** (`is_superuser=True`): Gets full menu tree (all active menus)
- **All other users** (including Admin/Super Admin): Get only assigned menus from `UserMenuAccess` table
- **No assigned menus**: Returns empty array with a message

**Menu Filtering Logic**:
- Only active menu items are shown (`is_active=True`)
- Parent menus are shown if:
  - The parent itself is assigned to the user, OR
  - The parent has at least one allowed child/descendant
- Child menus are shown only if directly assigned or have allowed descendants

**Notes**:
- `is_django_superuser`: Whether user has Django's built-in superuser status
- `is_app_admin`: Whether user has "Admin" or "Super Admin" `user_level` in application
- `user_level`: User's application-level role (e.g., "User", "Admin", "Super Admin")

---

## Field Reference

### MenuItem Fields
| Field    | Type    | Description                                      |
|----------|---------|--------------------------------------------------|
| id       | integer | Unique identifier for the menu item              |
| key      | string  | Unique key for frontend routing/identification   |
| name     | string  | Display name of the menu item                    |
| path     | string  | URL path/route for navigation                    |
| icon     | string  | Icon identifier (e.g., Ant Design icon name)     |
| parent   | integer | ID of parent menu item (null for root items)     |
| order    | integer | Sort order within the same parent level          |
| children | array   | Nested array of child menu items                 |

### User Fields
| Field        | Type    | Description                          |
|--------------|---------|--------------------------------------|
| id           | integer | Unique user identifier               |
| username     | string  | User's login username                |
| first_name   | string  | User's first name                    |
| last_name    | string  | User's last name                     |
| email        | string  | User's email address                 |
| is_staff     | boolean | Django staff status                  |
| is_superuser | boolean | Django superuser status              |

### UserMenuAccess Fields
| Field       | Type    | Description                           |
|-------------|---------|---------------------------------------|
| user        | integer | Foreign key to User (AppUser)         |
| menu_item   | integer | Foreign key to MenuItem               |

**Unique Constraint**: `(user, menu_item)` - A user can only be assigned to a menu once.

---

## Error Handling

### Common HTTP Status Codes

| Status Code | Meaning                              |
|-------------|--------------------------------------|
| 200         | Success - Request processed          |
| 400         | Bad Request - Invalid input data     |
| 401         | Unauthorized - Missing/invalid token |
| 403         | Forbidden - Insufficient permissions |
| 404         | Not Found - Resource doesn't exist   |
| 500         | Server Error - Internal error        |

### Error Response Format

**Standard Error**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Validation Error**:
```json
{
  "detail": "Invalid data",
  "errors": {
    "menu_ids": ["This field is required."]
  }
}
```

**Multiple Invalid IDs**:
```json
{
  "detail": "Invalid menu IDs: {99, 100}"
}
```

---

## Common Use Cases

### Use Case 1: Assign Basic Dashboard Access to New User

**Step 1**: Get the menu tree to find menu IDs
```http
GET /api/user-controll/admin/menu-tree/
```

**Step 2**: Assign dashboard menu (ID: 1) to user
```http
POST /api/user-controll/admin/user/15/menus/
{
  "menu_ids": [1]
}
```

**Step 3**: User logs in and retrieves their menu
```http
GET /api/user-controll/my-menu/
```

---

### Use Case 2: Grant Full CV Management Access

**Step 1**: Get menu tree (CV Management parent: 5, CV List child: 6)

**Step 2**: Assign only child menu (parent will be auto-included)
```http
POST /api/user-controll/admin/user/20/menus/
{
  "menu_ids": [6]
}
```

**Response**:
```json
{
  "ok": true,
  "menu_ids": [5, 6],
  "message": "Successfully updated menu permissions for user@example.com"
}
```

---

### Use Case 3: Remove All Menu Access from User

```http
POST /api/user-controll/admin/user/25/menus/
{
  "menu_ids": []
}
```

**Response**:
```json
{
  "ok": true,
  "menu_ids": [],
  "message": "Successfully updated menu permissions for user@example.com"
}
```

---

## Security Notes

1. **Permission Isolation**: Admin endpoints require `IsSuperAdmin` permission - only accessible to:
   - Django superusers (`is_superuser=True`)
   - Django staff (`is_staff=True`)
   - Users with 'user_control' menu access

2. **Token Authentication**: All endpoints require valid JWT access token

3. **Menu Visibility**: Users can only see menus explicitly assigned to them (except Django superusers)

4. **Atomic Operations**: Menu permission updates are atomic - either all changes apply or none do

5. **Parent Auto-Assignment**: System automatically ensures parent menus are accessible when child menus are assigned (prevents orphaned menu access)

6. **User Level vs Django Superuser**: 
   - `user_level` (Admin/Super Admin) is an application-level role that does NOT grant full menu access
   - Only Django superusers (`is_superuser=True`) get unrestricted access to all menus

---

## Best Practices

1. **Always fetch menu tree first**: Use `/admin/menu-tree/` to understand the hierarchy before assigning menus

2. **Verify menu assignments**: Use `/admin/user/{user_id}/menus/` to check what menus a user currently has

3. **Let system handle parents**: Don't manually include parent menu IDs - the system auto-assigns them based on selected children

4. **Test with `/my-menu/`**: After assigning permissions, have the user call `/my-menu/` to verify they see the correct menus

5. **Handle empty menus gracefully**: Frontend should display a helpful message when `menu` array is empty

6. **Cache menu data**: Menu structures rarely change - consider caching `/my-menu/` response for performance

---

## Postman Collection Examples

### Environment Variables
```
base_url = http://localhost:8000/api
access_token = <your_jwt_access_token>
```

### Admin - Get All Users
```
GET {{base_url}}/user-controll/admin/users/
Headers:
  Authorization: Bearer {{access_token}}
```

### Admin - Get Menu Tree
```
GET {{base_url}}/user-controll/admin/menu-tree/
Headers:
  Authorization: Bearer {{access_token}}
```

### Admin - Get User Menus
```
GET {{base_url}}/user-controll/admin/user/15/menus/
Headers:
  Authorization: Bearer {{access_token}}
```

### Admin - Set User Menus
```
POST {{base_url}}/user-controll/admin/user/15/menus/
Headers:
  Authorization: Bearer {{access_token}}
  Content-Type: application/json
Body:
{
  "menu_ids": [1, 2, 3, 5, 6]
}
```

### User - Get My Menu
```
GET {{base_url}}/user-controll/my-menu/
Headers:
  Authorization: Bearer {{access_token}}
```

---

## Changelog

**Version 1.0** - Initial documentation
- Admin endpoints for user and menu management
- User endpoint for personalized menu retrieval
- Hierarchical menu structure with auto-parent assignment
- Django superuser vs app admin differentiation

---

**Documentation Generated**: 2025
**Backend**: Django 5.2.7 + Django REST Framework
**Database**: PostgreSQL with UUID primary keys
