# Manual Meeting Links Guide

This guide explains how to use manual meeting links for demo sessions instead of Zoom OAuth integration.

## ✅ Benefits of Manual Meeting Links

- **No OAuth Setup Required** - Skip complex API configuration
- **Works with Any Platform** - Google Meet, Zoom, Teams, Jitsi, etc.
- **Full Admin Control** - Complete control over meeting creation
- **Simple & Reliable** - No API failures or token issues
- **Flexible** - Can be updated anytime

## 🔧 How It Works

### 1. Admin Creates Meeting

- Admin creates a meeting in their preferred video platform
- Copies the meeting link (e.g., `https://meet.google.com/abc-defg-hij`)

### 2. Create Demo Session

When creating a demo session, include the meeting link:

```json
{
  "session_date": "2025-08-01",
  "session_time": "15:00:00",
  "title": "Friday Demo Session",
  "description": "Weekly demo presentations",
  "max_scheduled": 8,
  "zoom_link": "https://meet.google.com/abc-defg-hij",
  "is_active": true
}
```

### 3. Students Get Link

- Students see the meeting link when they sign up
- Link is included in Slack notifications (if configured)
- Link is displayed in the frontend

## 📋 Step-by-Step Usage

### Option 1: Google Meet (Recommended)

1. Go to https://meet.google.com/
2. Click "New meeting" → "Start an instant meeting"
3. Copy the meeting link (e.g., `https://meet.google.com/abc-defg-hij`)
4. Create demo session with this link

### Option 2: Zoom Personal Room

1. Use your Zoom Personal Meeting Room
2. Get your PMI link: `https://zoom.us/j/1234567890`
3. Create demo session with this link

### Option 3: Microsoft Teams

1. Create a meeting in Teams
2. Copy the meeting link
3. Create demo session with this link

### Option 4: Jitsi Meet (Free)

1. Go to https://meet.jit.si/
2. Enter a room name (e.g., "demo-session-2025-08-01")
3. Use link: `https://meet.jit.si/demo-session-2025-08-01`

## 🎯 API Usage

### Create Demo Session with Meeting Link

```bash
curl -X POST "http://localhost:8000/api/v1/admin/demo-sessions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_date": "2025-08-01",
    "session_time": "15:00:00",
    "title": "Friday Demo Session",
    "description": "Weekly demo presentations",
    "max_scheduled": 8,
    "zoom_link": "https://meet.google.com/abc-defg-hij",
    "is_active": true
  }'
```

### Create Demo Session Without Link (Add Later)

```bash
curl -X POST "http://localhost:8000/api/v1/admin/demo-sessions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_date": "2025-08-01",
    "session_time": "15:00:00",
    "title": "Friday Demo Session",
    "description": "Weekly demo presentations",
    "max_scheduled": 8,
    "zoom_link": null,
    "is_active": true
  }'
```

### Update Meeting Link Later

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/demo-sessions/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "zoom_link": "https://meet.google.com/abc-defg-hij"
  }'
```

## 🔄 Workflow Examples

### Workflow 1: Create with Link

1. Admin creates Google Meet meeting
2. Admin copies link: `https://meet.google.com/abc-defg-hij`
3. Admin creates demo session with link
4. Students sign up and get meeting link
5. Slack notification sent with link (if configured)

### Workflow 2: Create Later, Add Link

1. Admin creates demo session without link
2. Admin creates meeting closer to session date
3. Admin updates demo session with meeting link
4. Students get updated link
5. Send reminder notification with link

## 💡 Pro Tips

### Meeting Link Best Practices

- **Use consistent naming** - e.g., `friday-demo-2025-08-01`
- **Test links** - Verify they work before sharing
- **Set up rooms early** - Don't wait until the last minute
- **Use recurring meetings** - Same link for weekly sessions

### Platform Recommendations

1. **Google Meet** - No signup required, reliable
2. **Jitsi Meet** - Completely free, open source
3. **Zoom Personal Room** - Consistent link, familiar interface
4. **Microsoft Teams** - Good for organizations using Office 365

### Backup Plan

- Always have a backup meeting link ready
- Consider using a consistent personal room for emergencies
- Keep meeting platform contact info handy

## 🔧 Configuration

### Environment Variables

No special configuration needed for manual links. The system works with:

- `SLACK_BOT_TOKEN` - For notifications (optional)
- `SLACK_CHANNEL` - For notifications (optional)

### Frontend Changes

The frontend will display the meeting link as provided:

- Show "Join Meeting" button if link is available
- Show "Meeting link will be provided" if no link
- Allow admins to edit meeting link

## 🚀 Testing

Run the test script to verify everything works:

```bash
python scripts/test_manual_demo_creation.py
```

## 📞 Support

If you encounter issues:

1. Check the server logs for errors
2. Verify the meeting link format
3. Test the link manually before using
4. Ensure proper authentication

## 🎉 You're Ready!

Manual meeting links provide a simple, reliable way to handle demo sessions without complex OAuth setup. This approach gives you full control and works with any video platform you prefer.
