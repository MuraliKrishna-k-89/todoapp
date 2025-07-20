# Todo App - Windows Compatible

A comprehensive, modern todo application built with FastAPI, SQLModel, and Bootstrap 5. Fully optimized for Windows development and deployment.

## 🚀 Features

### ✨ Core Functionality

- **Task Management**: Create, edit, delete, and complete tasks
- **Priority Levels**: High, Medium, Low priority with visual indicators
- **Task Types**: BAU, SRE, Automation, Monitoring, Observability, Other
- **Time Tracking**: Allocated vs actual time spent
- **Status Management**: Pending and completed task tracking
- **Real-time Timezone Display**: EST, PST, and IST time zones on all pages

### 🗑️ Backup & Recovery

- **Deleted Tasks Backup**: 15-day retention for accidentally deleted tasks
- **One-Click Restore**: Easily restore deleted tasks
- **Automatic Cleanup**: Old backups removed automatically

### 📊 Reports & Analytics

- **Weekly Reports**: Comprehensive productivity tracking
- **Office Target Tracking**: 6-hour weekday productivity targets
- **Time Analytics**: Task completion trends and patterns
- **Visual Progress**: Daily and weekly progress indicators

### 🎨 Modern UI/UX

- **Responsive Design**: Mobile-first Bootstrap 5 interface
- **Modern Styling**: Inter font, gradients, glassmorphism effects
- **Interactive Elements**: Hover effects, smooth transitions
- **Accessibility**: Proper contrast ratios and semantic HTML
- **Dark Mode Ready**: Prepared for future dark theme implementation

## �️ Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: SQLModel with SQLite (production-ready for PostgreSQL)
- **Frontend**: Bootstrap 5 + Jinja2 templates
- **Styling**: Custom CSS with modern design patterns
- **Icons**: Bootstrap Icons for consistent iconography

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project**

   ```bash
   cd todoapp
   ```

2. **Create and activate a virtual environment**

   ```powershell
   # Create virtual environment
   python -m venv venv

   # Activate on Windows PowerShell
   .\venv\Scripts\Activate.ps1

   # If you get execution policy error, run:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```powershell
   uvicorn main:app --reload
   ```

5. **Open your browser**
   Navigate to `http://127.0.0.1:8000`

## Project Structure

```
todoapp/
├── main.py              # FastAPI application and all routes
├── requirements.txt     # Python dependencies
├── todo.db             # SQLite database (created automatically)
├── static/             # CSS files (created automatically)
│   └── style.css       # Custom styles
└── templates/          # HTML templates (created automatically)
    ├── index.html      # Home page
    ├── create_task.html # Create new task
    ├── pending_tasks.html # View pending tasks
    ├── edit_task.html  # Edit existing task
    ├── completed_tasks.html # View completed tasks
    └── reports.html    # Weekly reports
```

## Usage Guide

### Creating Tasks

1. Click "Create Task" in the navigation or home page
2. Fill in task details:
   - **Task Name**: Descriptive name for your task
   - **Priority**: Low, Medium, or High
   - **Start Date**: When you plan to start
   - **Deadline**: When the task should be completed
   - **Time Allocated**: Estimated time in minutes
3. Click "Create Task" to save

### Managing Pending Tasks

- **View All**: See all pending tasks with priority and deadline sorting
- **Status Indicators**:
  - Red row: Overdue tasks
  - Yellow row: Due today
  - Normal: Future tasks
- **Quick Actions**:
  - ✅ **Complete**: Mark task as done with actual time tracking
  - ✏️ **Edit**: Modify task details
  - 🗑️ **Delete**: Remove task (with confirmation)

### Completing Tasks

1. Click the green checkmark button on any pending task
2. Enter the actual time spent on the task
3. Click "Mark Complete" to finish

### Weekly Reports

- View productivity reports by week
- See daily breakdowns of completed tasks
- Track total time spent per week
- Navigate between different weeks using the dropdown

## Database Schema

### Task Model

- `id`: Unique identifier (auto-generated)
- `name`: Task name (required, max 100 characters)
- `priority`: Low/Medium/High (default: Low)
- `start_date`: Planned start date
- `deadline_date`: Task deadline
- `time_allocated`: Estimated time in minutes
- `time_taken`: Actual time spent in minutes
- `status`: pending/completed (default: pending)
- `completed_at`: Timestamp when completed (auto-set)

## API Endpoints

### Web Routes

- `GET /` - Home page
- `GET /create-task` - Create task form
- `POST /tasks` - Create new task
- `GET /pending-tasks` - View pending tasks
- `GET /edit-task/{task_id}` - Edit task form
- `POST /tasks/{task_id}/update` - Update task
- `POST /tasks/{task_id}/complete` - Mark task complete
- `POST /tasks/{task_id}/delete` - Delete task
- `GET /completed-tasks` - View completed tasks
- `POST /tasks/{task_id}/move-to-pending` - Move back to pending
- `GET /reports` - Weekly reports with optional week_offset parameter

## Customization

### Styling

- Edit `static/style.css` for custom styles
- Uses Bootstrap 5 classes throughout
- Modern gradient backgrounds and animations included

### Database

- SQLite database file: `todo.db`
- Automatically created on first run
- Backup by copying the database file

### Templates

- All HTML templates use Jinja2 syntax
- Bootstrap 5 components throughout
- Responsive design with mobile support

## Troubleshooting

### Common Issues

1. **Port already in use**

   ```powershell
   uvicorn main:app --reload --port 8001
   ```

2. **Module not found errors**

   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

3. **Database issues**

   - Delete `todo.db` to reset database
   - Restart application to recreate tables

4. **Template not found errors**
   - Ensure application runs once to create template files
   - Check that `templates/` and `static/` directories exist

## Development

### Adding New Features

1. Update database models in `main.py`
2. Add new routes/endpoints
3. Create or modify HTML templates
4. Update CSS for styling
5. Test with `uvicorn main:app --reload`

### Code Organization

- All code is in `main.py` for simplicity
- Database models at the top
- FastAPI routes in the middle
- HTML/CSS generation at the bottom

## License

This project is open source and available under the MIT License.
