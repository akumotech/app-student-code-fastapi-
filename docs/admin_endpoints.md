# 🔐 Admin Endpoints Documentation

**Updated:** January 2025  
**Version:** 1.0  
**Base URL:** `/api/v1/admin`

## 📋 Overview

This document describes the admin endpoints for the student progress tracking platform. These endpoints provide comprehensive user management, student oversight, and dashboard functionality for administrators.

## 🔒 Authentication & Authorization

**Requirements:**

- User must be authenticated via JWT token (HTTP-only cookie)
- User role must be `"admin"`
- All endpoints require admin privileges

**Error Responses:**

- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient privileges (non-admin user)

---

## 📊 Dashboard Endpoints

### GET `/dashboard`

**Summary:** Get comprehensive admin dashboard overview

**Response Schema:**

```json
{
  "success": true,
  "message": "Dashboard data retrieved successfully",
  "data": {
    "stats": {
      "total_users": 150,
      "total_students": 120,
      "total_instructors": 8,
      "total_admins": 2,
      "active_batches": 3,
      "total_certificates": 45,
      "total_demos": 89,
      "users_with_wakatime": 95
    },
    "recent_students": [...],
    "active_batches": [...]
  }
}
```

### GET `/stats`

**Summary:** Get dashboard statistics only

**Response Schema:**

```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_users": 150,
    "total_students": 120,
    "total_instructors": 8,
    "total_admins": 2,
    "active_batches": 3,
    "total_certificates": 45,
    "total_demos": 89,
    "users_with_wakatime": 95
  }
}
```

---

## 👥 User Management Endpoints

### GET `/users`

**Summary:** Get paginated list of all users with filtering

**Query Parameters:**

- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20, max: 100) - Items per page
- `role` (string, optional) - Filter by role: "student", "instructor", "admin", "user"
- `search` (string, optional) - Search by name or email

**Example Requests:**

```bash
# Get first page of all users
GET /api/v1/admin/users?page=1&page_size=20

# Filter by students only
GET /api/v1/admin/users?role=student

# Search users
GET /api/v1/admin/users?search=john@example.com
```

**Response Schema:**

```json
{
  "success": true,
  "message": "Retrieved 20 users",
  "data": {
    "users": [
      {
        "id": 1,
        "email": "student@example.com",
        "name": "John Student",
        "role": "student",
        "disabled": false,
        "wakatime_connected": true,
        "last_login": null,
        "student_detail": {
          "id": 1,
          "user": {...},
          "batch": {
            "id": 1,
            "name": "April 2025 Batch",
            "description": "Spring cohort",
            "start_date": "2025-04-01",
            "end_date": "2025-06-30",
            "slack_channel": "#april-2025",
            "curriculum": "Full Stack Development"
          },
          "project": {
            "id": 1,
            "name": "Final Project",
            "start_date": "2025-06-01",
            "end_date": "2025-06-30",
            "happy_hour": "Friday 5 PM"
          },
          "certificates": [
            {
              "id": 1,
              "name": "JavaScript Fundamentals",
              "issuer": "FreeCodeCamp",
              "date_issued": "2025-01-15",
              "date_expired": null,
              "description": "Completed JavaScript course"
            }
          ],
          "demos": [
            {
              "id": 1,
              "title": "Todo App Demo",
              "description": "React-based todo application",
              "link": "https://github.com/user/todo-app",
              "demo_date": "2025-01-20",
              "status": "confirmed"
            }
          ],
          "wakatime_stats": {
            "total_seconds": 25200,
            "hours": 7,
            "minutes": 0,
            "digital": "07:00",
            "text": "7 hrs 0 mins",
            "last_updated": "2025-01-25T10:30:00"
          }
        }
      }
    ],
    "total_count": 150,
    "page": 1,
    "page_size": 20
  }
}
```

### GET `/users/{user_id}`

**Summary:** Get detailed information about a specific user

**Path Parameters:**

- `user_id` (int) - User ID

**Response:** Same user object structure as in the users list

---

## ✏️ User Modification Endpoints

### PUT `/users/{user_id}/role`

**Summary:** Update a user's role

**Path Parameters:**

- `user_id` (int) - User ID

**Request Body:**

```json
{
  "role": "student"
}
```

**Valid Roles:** `"student"`, `"instructor"`, `"admin"`, `"user"`

**Response:**

```json
{
  "success": true,
  "message": "User 1's role updated to student.",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "student",
    "disabled": false
  }
}
```

### PUT `/students/{student_id}`

**Summary:** Update student information

**Path Parameters:**

- `student_id` (int) - Student ID

**Request Body:**

```json
{
  "batch_id": 2,
  "project_id": 3
}
```

**Note:** Both fields are optional. Only provided fields will be updated.

**Response:** Complete user overview with updated student details

---

## 🎓 Batch & Project Management

### GET `/batches`

**Summary:** Get all batches

**Response:**

```json
{
  "success": true,
  "message": "Retrieved 5 batches",
  "data": [
    {
      "id": 1,
      "name": "April 2025 Batch",
      "description": "Spring cohort",
      "start_date": "2025-04-01",
      "end_date": "2025-06-30",
      "slack_channel": "#april-2025",
      "curriculum": "Full Stack Development"
    }
  ]
}
```

### GET `/projects`

**Summary:** Get all projects

**Response:**

```json
{
  "success": true,
  "message": "Retrieved 8 projects",
  "data": [
    {
      "id": 1,
      "name": "Final Project",
      "start_date": "2025-06-01",
      "end_date": "2025-06-30",
      "happy_hour": "Friday 5 PM"
    }
  ]
}
```

---

## 💡 Frontend Integration Guide

### Dashboard Implementation

**Recommended Data Flow:**

1. Load dashboard statistics first (`/stats`)
2. Load recent students and active batches (`/dashboard`)
3. Implement real-time updates with periodic polling

**Sample Frontend Code (React/TypeScript):**

```typescript
interface DashboardData {
  stats: {
    total_users: number;
    total_students: number;
    total_instructors: number;
    total_admins: number;
    active_batches: number;
    total_certificates: number;
    total_demos: number;
    users_with_wakatime: number;
  };
  recent_students: UserOverview[];
  active_batches: BatchInfo[];
}

const AdminDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch("/api/v1/admin/dashboard", {
        credentials: "include", // Include cookies
      });
      const result = await response.json();
      if (result.success) {
        setDashboardData(result.data);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    }
  };

  // Render dashboard components
};
```

### User Management Table

**Recommended Features:**

- Pagination with configurable page size
- Role-based filtering
- Search functionality
- WakaTime connection status indicator
- Quick actions (role update, view details)

**Sample User Table Component:**

```typescript
interface UserTableProps {
  onRoleUpdate: (userId: number, newRole: string) => void;
  onUserDetails: (userId: number) => void;
}

const UserTable: React.FC<UserTableProps> = ({
  onRoleUpdate,
  onUserDetails,
}) => {
  const [users, setUsers] = useState<UserOverview[]>([]);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    totalCount: 0,
  });
  const [filters, setFilters] = useState({
    role: "",
    search: "",
  });

  const fetchUsers = async () => {
    const params = new URLSearchParams({
      page: pagination.page.toString(),
      page_size: pagination.pageSize.toString(),
      ...(filters.role && { role: filters.role }),
      ...(filters.search && { search: filters.search }),
    });

    const response = await fetch(`/api/v1/admin/users?${params}`, {
      credentials: "include",
    });
    const result = await response.json();

    if (result.success) {
      setUsers(result.data.users);
      setPagination((prev) => ({
        ...prev,
        totalCount: result.data.total_count,
      }));
    }
  };

  // Render table with users
};
```

---

## 🔍 WakaTime Integration

The admin endpoints automatically include WakaTime statistics for users who have connected their accounts. The `wakatime_stats` object provides:

- **Total coding time** for the last 7 days
- **Formatted time display** (digital and text formats)
- **Last update timestamp**

**Usage in Frontend:**

```typescript
const formatWakaTimeStats = (stats: WakaTimeStats | null) => {
  if (!stats) return "No data";
  return `${stats.text} (Last updated: ${new Date(
    stats.last_updated
  ).toLocaleDateString()})`;
};
```

---

## ⚠️ Error Handling

**Common Error Responses:**

```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "User with id 999 not found",
    "timestamp": "2025-01-25T10:30:00.000Z"
  }
}
```

**Frontend Error Handling:**

```typescript
const handleApiCall = async (apiCall: () => Promise<Response>) => {
  try {
    const response = await apiCall();
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error?.message || "API call failed");
    }

    return result;
  } catch (error) {
    console.error("API Error:", error);
    // Show user-friendly error message
    throw error;
  }
};
```

---

## 🚀 Performance Considerations

1. **Pagination:** Always use pagination for user lists
2. **Caching:** Consider caching dashboard statistics for 5-10 minutes
3. **Lazy Loading:** Load detailed student information only when needed
4. **Real-time Updates:** Implement polling for critical statistics (every 30-60 seconds)

---

## 🔒 Security Notes

1. **Admin Only:** All endpoints require admin role verification
2. **Audit Trail:** Consider implementing admin activity logging
3. **Rate Limiting:** Implement rate limiting for admin endpoints
4. **Input Validation:** All user inputs are validated server-side

---

**Support:** For questions about admin endpoint integration, reference this documentation and the API's OpenAPI specification at `/docs`.
