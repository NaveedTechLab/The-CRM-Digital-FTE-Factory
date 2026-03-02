# ProjectFlow - Product Documentation

## Getting Started

### Account Setup
1. Visit app.techcorp.io and click "Start Free Trial"
2. Enter your work email and create a password
3. Choose your plan (14-day free trial on all plans)
4. Invite team members via email

### Creating Your First Project
1. Click "+ New Project" on the dashboard
2. Choose a template or start from scratch
3. Set project name, description, and team members
4. Configure your preferred view (Kanban, List, or Gantt)

## Feature Documentation

### Task Management
- **Create Task:** Click "+" in any column or use keyboard shortcut `Ctrl+N`
- **Assign Task:** Drag to a team member or use the assignee dropdown
- **Due Dates:** Click the calendar icon to set deadlines; overdue tasks turn red
- **Labels:** Color-coded labels for categorization (up to 20 per project)
- **Subtasks:** Break down tasks into smaller items with checkbox tracking
- **Dependencies:** Link tasks with "blocks" or "blocked by" relationships

### Team Collaboration
- **Comments:** @mention team members in task comments for notifications
- **File Attachments:** Drag-and-drop files (max 25MB per file, 100MB on Starter)
- **Real-time Chat:** Project-level and direct messaging
- **Activity Feed:** Track all changes with timestamps and user attribution

### Time Tracking
- **Start/Stop Timer:** Click the clock icon on any task
- **Manual Entry:** Add time entries after the fact with date and notes
- **Reports:** Weekly and monthly time reports by project, user, or client
- **Export:** Download time data as CSV for invoicing

### Integrations
- **Slack:** Get task notifications in Slack channels
- **GitHub:** Link commits and PRs to tasks automatically
- **Google Workspace:** Sync calendar events and attach Drive files
- **Jira:** Two-way sync for teams transitioning from Jira
- **Zapier:** Connect to 5,000+ apps via Zapier (Professional+)

### API Documentation
- **Base URL:** `https://api.techcorp.io/v1/`
- **Authentication:** Bearer token (generate in Settings > API Keys)
- **Rate Limits:** 100 requests/minute (Professional), 500/minute (Enterprise)
- **Endpoints:** `/projects`, `/tasks`, `/users`, `/time-entries`, `/comments`
- **Webhooks:** Configure in Settings > Integrations > Webhooks

## Troubleshooting

### Common Issues
| Issue | Solution |
|-------|----------|
| Can't log in | Reset password via "Forgot Password" link |
| Slow loading | Clear browser cache; check internet connection |
| Missing notifications | Check Settings > Notifications; verify email isn't in spam |
| File upload fails | Check file size (max 25MB); supported formats: PDF, PNG, JPG, DOC, XLS |
| API returns 401 | Regenerate API key in Settings; ensure correct plan |
| Gantt chart not showing | Requires at least 2 tasks with dates and dependencies |
| Mobile app sync issues | Force close and reopen; ensure app is updated |

### Password Reset
1. Go to app.techcorp.io/reset-password
2. Enter your email address
3. Check email for reset link (valid for 24 hours)
4. Create new password (min 8 chars, 1 uppercase, 1 number)

### Two-Factor Authentication
1. Go to Settings > Security > Two-Factor Authentication
2. Scan QR code with authenticator app (Google Authenticator, Authy)
3. Enter verification code to confirm setup
4. Save backup codes in a secure location

### Data Export
1. Go to Settings > Account > Data Export
2. Select data type: Projects, Tasks, Time Entries, or All
3. Choose format: CSV or JSON
4. Click "Export" - download link sent via email within 1 hour

## System Requirements
- **Browser:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile:** iOS 15+ or Android 11+ (dedicated app available)
- **Internet:** Minimum 5 Mbps recommended
