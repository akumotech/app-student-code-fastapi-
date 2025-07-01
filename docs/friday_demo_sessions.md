# Friday Demo Sessions Feature

## 🎯 Overview

The Friday Demo Sessions feature allows students to voluntarily sign up to showcase their demos during weekly Friday sessions. This system provides both admin control and student interaction capabilities.

## 📊 Data Models

### DemoSession

- **Purpose**: Represents a Friday demo session
- **Key Fields**:
  - `session_date`: The Friday date
  - `is_active`: Whether students can sign up
  - `is_cancelled`: Whether the session is cancelled
  - `max_scheduled`: Optional limit on signups
  - `title`, `description`, `notes`: Session metadata

### DemoSignup

- **Purpose**: Represents a student's signup for a demo session
- **Key Fields**:
  - `session_id`: Foreign key to DemoSession
  - `student_id`: Foreign key to Student
  - `demo_id`: Optional foreign key to Demo (student's existing demo)
  - `status`: "scheduled", "presented", "no_show", "cancelled"
  - `signup_notes`: Student's notes about their demo
  - `did_present`, `presentation_notes`, `presentation_rating`: Admin tracking fields

## 🔐 Security & Permissions

### Student Permissions

- View available demo sessions
- Sign up for active, non-cancelled sessions
- Update/cancel their own signups
- Attach their own demos to signups

### Admin Permissions

- Create, update, delete demo sessions
- View all sessions and signups
- Update signup status after presentations
- Bulk create multiple sessions
- Control session active/cancelled status

## 🚀 API Endpoints

### Student Endpoints

#### Get Available Sessions

```
GET /demo-sessions
```

Returns active, non-cancelled sessions with signup counts and user signup status.

#### Sign Up for Session

```
POST /demo-sessions/{session_id}/signup
```

Body:

```json
{
  "demo_id": 123, // optional
  "signup_notes": "I'll demo my React app" // optional
}
```

#### View My Signups

```
GET /students/me/demo-signups
```

#### Update My Signup

```
PUT /demo-signups/{signup_id}
```

#### Cancel My Signup

```
DELETE /demo-signups/{signup_id}
```

### Admin Endpoints

#### List All Sessions

```
GET /admin/demo-sessions?include_inactive=false&include_cancelled=false
```

#### Create Session

```
POST /admin/demo-sessions
```

Body:

```json
{
  "session_date": "2024-01-12",
  "title": "Friday Demo Session - January 12, 2024",
  "description": "Weekly demo session",
  "is_active": true,
  "is_cancelled": false,
  "max_scheduled": null
}
```

#### Update Session

```
PUT /admin/demo-sessions/{session_id}
```

#### Delete Session

```
DELETE /admin/demo-sessions/{session_id}
```

#### View Session Signups

```
GET /admin/demo-sessions/{session_id}/signups
```

#### Update Signup (Admin)

```
PUT /admin/demo-signups/{signup_id}/admin
```

Body:

```json
{
  "did_present": true,
  "presentation_notes": "Great demo of React components",
  "presentation_rating": 5,
  "status": "presented"
}
```

#### Bulk Create Sessions

```
POST /admin/demo-sessions/bulk-create
```

## 🤖 Automation Features

### Automatic Session Creation

The system can automatically create demo sessions for upcoming Fridays:

```python
from app.integrations.scheduler import schedule_friday_demo_sessions

# Creates sessions for next 8 Fridays
schedule_friday_demo_sessions()
```

### Holiday Management

Holiday cancellation functionality is available but currently commented out. Can be enabled to automatically cancel sessions on holidays.

## 🔄 Business Logic & Validation

### Session Signup Validation

1. **Session must be active**: `is_active = True`
2. **Session must not be cancelled**: `is_cancelled = False`
3. **No duplicate signups**: One signup per student per session
4. **Signup limits**: Respects `max_scheduled` if set
5. **Demo ownership**: If attaching a demo, must belong to the student

### Session Management

1. **Date uniqueness**: Only one session per date
2. **Admin control**: Only admins can create/modify sessions
3. **Cascade deletion**: Deleting a session removes all signups

## 📝 Key Design Changes

### Batch Independence

- Demo sessions are **not directly tied to batches**
- Students from any batch can sign up for any session
- Batch relationships exist only through student signups

### Field Naming Consistency

- `max_scheduled` instead of `max_signups`
- `status: "scheduled"` instead of `"signed_up"`
- `scheduled_at` instead of `signed_up_at`

## 🛠 Database Migration

To implement this feature, create a new Alembic migration:

```bash
alembic revision --autogenerate -m "Add demo session and signup tables"
alembic upgrade head
```

## 📊 Usage Examples

### Weekly Workflow

1. **Admin**: Create Friday demo session
2. **Students**: Browse available sessions and sign up
3. **Friday**: Demo session occurs
4. **Admin**: Mark attendance and rate presentations

### Automation Setup

Add to your application startup or cron job:

```python
from app.integrations.scheduler import automated_demo_session_management

# Run weekly to create upcoming sessions
automated_demo_session_management()
```

## 🎯 Future Enhancements

1. **Email notifications** when sessions are created or cancelled
2. **Calendar integration** for session scheduling
3. **Demo recording links** for presentations
4. **Student feedback system** for sessions
5. **Advanced analytics** on demo participation
6. **Holiday calendar integration** for automatic cancellations
7. **Time slot management** within sessions
8. **Session templates** for recurring themes

## 🔧 Configuration

### Environment Variables

No additional environment variables required. Uses existing database connection.

### Optional Features

- Set `max_scheduled` per session to limit signups
- Use `notes` field for admin session instructions
- Enable holiday checking by uncommenting functions in scheduler

## 🐛 Troubleshooting

### Common Issues

1. **"Session not found"**: Check if session exists and is active
2. **"Already signed up"**: Student trying to sign up twice
3. **"Demo session is full"**: Signup limit reached
4. **"Demo not found"**: Student trying to attach non-existent demo

### Debug Queries

```sql
-- Check session signups
SELECT ds.session_date, COUNT(dsu.id) as signup_count
FROM demo_session ds
LEFT JOIN demo_signup dsu ON ds.id = dsu.session_id
GROUP BY ds.id, ds.session_date
ORDER BY ds.session_date;

-- Check student signups
SELECT s.id, u.name, ds.session_date
FROM student s
JOIN "user" u ON s.user_id = u.id
JOIN demo_signup dsu ON s.id = dsu.student_id
JOIN demo_session ds ON dsu.session_id = ds.id
ORDER BY ds.session_date DESC;
```
