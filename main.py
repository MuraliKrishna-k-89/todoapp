import os
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Database Models ---

class TaskBase(SQLModel):
    """Base model for a To-Do task."""
    name: str = Field(index=True)
    priority: str = Field(default="Medium", max_length=10)  # "Low", "Medium", "High"
    task_type: str = Field(default="Other", max_length=20)  # "BAU", "SRE", "Automation", "Monitoring", "Observability", "Meetings", "PTO", "Holiday", "Other"
    start_date: date
    deadline_date: date
    time_allocated: int = Field(default=30)  # in minutes, default 30 minutes
    time_taken: int = 0  # in minutes, updated upon completion or edit
    is_recurring: bool = Field(default=False)  # Whether this task repeats daily
    recurring_template_id: Optional[int] = Field(default=None)  # Reference to original template

class Task(TaskBase, table=True):
    """Database model for a To-Do task."""
    __tablename__ = "task"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="pending", max_length=10)  # "pending", "completed"
    completed_at: Optional[datetime] = None  # Timestamp when task was completed

class DeletedTask(TaskBase, table=True):
    """Database model for storing deleted tasks as backup."""
    __tablename__ = "deletedtask"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    original_task_id: int = Field(index=True)  # Original task ID before deletion
    status: str = Field(max_length=10)  # Status when deleted
    completed_at: Optional[datetime] = None  # If it was completed when deleted
    deleted_at: datetime = Field(default_factory=datetime.now)  # When it was deleted

class DailyTaskTemplate(SQLModel, table=True):
    """Database model for daily recurring task templates."""
    __tablename__ = "daily_task_template"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    priority: str = Field(default="Medium", max_length=10)  # "Low", "Medium", "High"
    task_type: str = Field(default="Other", max_length=20)
    time_allocated: int = Field(default=30)  # in minutes
    is_active: bool = Field(default=True)  # Whether to generate daily tasks
    created_at: datetime = Field(default_factory=datetime.now)

class TaskCreate(TaskBase):
    """Model for creating a new task."""
    pass

class TaskUpdate(SQLModel):
    """Model for updating an existing task."""
    name: Optional[str] = None
    priority: Optional[str] = None
    task_type: Optional[str] = None
    start_date: Optional[date] = None
    deadline_date: Optional[date] = None
    time_allocated: Optional[int] = None
    time_taken: Optional[int] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None

# --- Database Setup ---

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///todo.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def create_db_and_tables():
    """Creates the database tables based on the SQLModel definitions."""
    try:
        # Clear metadata and recreate
        SQLModel.metadata.clear()
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # If there's an error, try to drop and recreate the tables
        print("Attempting to recreate database tables...")
        try:
            SQLModel.metadata.drop_all(engine)
            SQLModel.metadata.clear()
            SQLModel.metadata.create_all(engine)
            print("Database tables recreated successfully")
        except Exception as e2:
            print(f"Failed to recreate database tables: {e2}")
            # Create tables individually if bulk creation fails
            print("Attempting to create tables individually...")
            create_individual_tables()

def create_individual_tables():
    """Creates database tables individually."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Create Task table if it doesn't exist
        if 'task' not in existing_tables:
            try:
                Task.__table__.create(engine, checkfirst=True)
                print("Created Task table")
            except Exception as e:
                if "already exists" not in str(e):
                    raise
                print("Task table already exists")
        
        # Create DeletedTask table if it doesn't exist  
        if 'deletedtask' not in existing_tables:
            try:
                DeletedTask.__table__.create(engine, checkfirst=True)
                print("Created DeletedTask table")
            except Exception as e:
                if "already exists" not in str(e):
                    raise
                print("DeletedTask table already exists")
            
        # Create DailyTaskTemplate table if it doesn't exist
        if 'daily_task_template' not in existing_tables:
            try:
                DailyTaskTemplate.__table__.create(engine, checkfirst=True)
                print("Created DailyTaskTemplate table")
            except Exception as e:
                if "already exists" not in str(e):
                    raise
                print("DailyTaskTemplate table already exists")
            
    except Exception as e:
        print(f"Individual table creation error: {e}")
        # If we have table creation issues, try to work with existing database structure
        print("Continuing with existing database structure...")

def migrate_database():
    """Handles database migrations for schema changes."""
    needs_migration = False
    
    try:
        with Session(engine) as session:
            # Check if task table exists and has new fields
            try:
                result = session.exec(select(Task).limit(1)).first()
                if result and not hasattr(result, 'is_recurring'):
                    print("Missing recurring fields in Task table...")
                    needs_migration = True
            except Exception:
                print("Task table needs migration...")
                needs_migration = True
            
            # Check if DailyTaskTemplate table exists
            try:
                session.exec(select(DailyTaskTemplate).limit(1)).first()
            except Exception:
                print("DailyTaskTemplate table missing...")
                needs_migration = True
                
    except Exception as e:
        print(f"Database migration needed: {e}")
        needs_migration = True
    
    if needs_migration:
        print("Recreating database with updated schema...")
        try:
            SQLModel.metadata.drop_all(engine)
            SQLModel.metadata.clear()
            SQLModel.metadata.create_all(engine)
            print("Database migration completed")
        except Exception as e:
            print(f"Migration error: {e}")
            # Create tables individually if bulk creation fails
            create_individual_tables()

# --- FastAPI Application Setup ---

app = FastAPI(
    title="Todo App",
    description="A comprehensive todo application with backup and analytics",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories and write frontend files before mounting
def ensure_directories_exist():
    """Ensure static and templates directories exist before mounting."""
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

# Ensure directories exist before mounting
ensure_directories_exist()

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2Templates for rendering HTML
templates = Jinja2Templates(directory="templates")

# --- Helper Functions ---

def get_session():
    """Dependency to get a database session."""
    with Session(engine) as session:
        yield session

def get_week_range(week_offset: int = 0):
    """
    Calculates the start and end dates for a specific week.
    week_offset = 0 for current week, -1 for last week, etc.
    """
    today = date.today()
    # Find the Monday of the current week
    start_of_current_week = today - timedelta(days=today.weekday())
    # Adjust for the offset
    start_date = start_of_current_week + timedelta(weeks=week_offset)
    end_date = start_date + timedelta(days=6) # Sunday of that week
    return start_date, end_date

# --- API Endpoints ---

@app.on_event("startup")
async def on_startup():
    """Event handler for application startup."""
    create_db_and_tables()
    migrate_database()
    # Ensure CSS file exists
    ensure_css_file_exists()


@app.get("/", response_class=RedirectResponse)
async def read_root():
    """Redirects to the pending tasks page."""
    return RedirectResponse(url="/pending-tasks", status_code=303)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        with Session(engine) as session:
            session.exec(select(Task).limit(1))
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
        )

@app.get("/create-task", response_class=HTMLResponse)
async def create_task_page(request: Request):
    """Renders the create task page."""
    # Get error parameters from URL if any
    error = request.query_params.get('error')
    task_name = request.query_params.get('task_name')
    error_date = request.query_params.get('date')
    
    try:
        # Ensure tables exist
        create_individual_tables()
        
        # Get active daily templates for quick templates
        with Session(engine) as session:
            daily_templates = session.exec(
                select(DailyTaskTemplate)
                .where(DailyTaskTemplate.is_active == True)
                .order_by(DailyTaskTemplate.name)
            ).all()
            print(f"DEBUG: Found {len(daily_templates)} active daily templates for create task page")
            for template in daily_templates:
                print(f"  - {template.name} ({template.task_type}, {template.priority})")
    except Exception as e:
        print(f"Error fetching daily templates: {e}")
        daily_templates = []
    
    return templates.TemplateResponse("create_task.html", {
        "request": request, 
        "error": error, 
        "task_name": task_name, 
        "error_date": error_date,
        "daily_templates": daily_templates
    })

@app.post("/tasks", response_class=RedirectResponse)
async def create_task(
    name: str = Form(...),
    priority: str = Form("Medium"),
    task_type: str = Form("Other"),
    start_date: date = Form(...),
    deadline_date: date = Form(...),
    time_allocated: int = Form(30),
):
    """Creates a new task in the database."""
    # Validation
    if not name.strip():
        raise HTTPException(status_code=400, detail="Task name cannot be empty")
    
    if deadline_date < start_date:
        raise HTTPException(status_code=400, detail="Deadline must be on or after start date")
    
    if time_allocated <= 0:
        raise HTTPException(status_code=400, detail="Time allocated must be greater than 0")
    
    if priority not in ["Low", "Medium", "High"]:
        raise HTTPException(status_code=400, detail="Invalid priority level")
    
    if task_type not in ["BAU", "SRE", "Automation", "Monitoring", "Observability", "Meetings", "PTO", "Holiday", "Other"]:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    try:
        with Session(engine) as session:
            # Check for duplicate task name on the same start date
            existing_task = session.exec(
                select(Task)
                .where(Task.name == name.strip())
                .where(Task.start_date == start_date)
                .where(Task.status.in_(["pending", "completed"]))  # Check both pending and completed
            ).first()
            
            if existing_task:
                # Redirect with error message for duplicate task
                return RedirectResponse(
                    url=f"/create-task?error=duplicate&task_name={name.strip()}&date={start_date}", 
                    status_code=303
                )
            
            new_task = Task(
                name=name.strip(),
                priority=priority,
                task_type=task_type,
                start_date=start_date,
                deadline_date=deadline_date,
                time_allocated=time_allocated,
                time_taken=0,
                status="pending"
            )
            session.add(new_task)
            session.commit()
            session.refresh(new_task)
        return RedirectResponse(url="/pending-tasks", status_code=303)
    except Exception as e:
        print(f"Database error creating task: {e}")
        print(f"Task data: name={name}, priority={priority}, task_type={task_type}")
        print(f"Start date: {start_date}, Deadline: {deadline_date}, Time allocated: {time_allocated}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.get("/pending-tasks", response_class=HTMLResponse)
async def pending_tasks_page(request: Request):
    """Renders the pending tasks page and fetches pending tasks."""
    try:
        print("Accessing pending tasks page...")
        # Ensure tables exist before querying
        create_individual_tables()
        
        with Session(engine) as session:
            print("Querying pending tasks...")
            pending_tasks = session.exec(
                select(Task)
                .where(Task.status == "pending")
                .order_by(Task.deadline_date, Task.priority.desc())
            ).all()
            print(f"Found {len(pending_tasks)} pending tasks")
        
        print("Rendering template...")
        return templates.TemplateResponse(
            "pending_tasks.html", 
            {"request": request, "tasks": pending_tasks, "date": date}
        )
    except Exception as e:
        print(f"Error in pending_tasks_page: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending tasks: {str(e)}")

@app.post("/tasks/{task_id}/complete", response_class=RedirectResponse)
async def complete_task(task_id: int, time_taken: int = Form(0)):
    """Marks a task as complete and updates time taken."""
    print(f"Complete task endpoint called - task_id: {task_id}, time_taken: {time_taken}")
    try:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                print(f"Task not found: {task_id}")
                raise HTTPException(status_code=404, detail="Task not found")
            
            print(f"Found task: {task.name}, current status: {task.status}")
            task.status = "completed"
            task.time_taken = time_taken # Update time taken
            task.completed_at = datetime.now()
            session.add(task)
            session.commit()
            session.refresh(task)
            print(f"Task completed successfully: {task.name}, time_taken: {task.time_taken}")
    except Exception as e:
        print(f"Error completing task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")
    return RedirectResponse(url="/pending-tasks", status_code=303)

@app.post("/tasks/{task_id}/delete", response_class=RedirectResponse)
async def delete_task(task_id: int):
    """Deletes a task and stores it in backup table."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Create backup of the task before deletion
        deleted_task = DeletedTask(
            original_task_id=task.id,
            name=task.name,
            priority=task.priority,
            task_type=task.task_type,
            start_date=task.start_date,
            deadline_date=task.deadline_date,
            time_allocated=task.time_allocated,
            time_taken=task.time_taken,
            status=task.status,
            completed_at=task.completed_at,
            deleted_at=datetime.now()
        )
        session.add(deleted_task)
        
        # Delete the original task
        session.delete(task)
        session.commit()
    return RedirectResponse(url="/pending-tasks", status_code=303)

@app.get("/edit-task/{task_id}", response_class=HTMLResponse)
async def edit_task_page(request: Request, task_id: int):
    """Renders the edit task page with pre-filled data."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})

@app.post("/tasks/{task_id}/update", response_class=RedirectResponse)
async def update_task(
    task_id: int,
    name: str = Form(...),
    priority: str = Form(...),
    task_type: str = Form(...),
    start_date: date = Form(...),
    deadline_date: date = Form(...),
    time_allocated: int = Form(...),
    time_taken: int = Form(0), # Allow updating time_taken during edit
    status: str = Form(...),
):
    """Updates an existing task."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.name = name
        task.priority = priority
        task.task_type = task_type
        task.start_date = start_date
        task.deadline_date = deadline_date
        task.time_allocated = time_allocated
        task.time_taken = time_taken
        
        # Handle status change logic
        if task.status != status:
            task.status = status
            if status == "completed" and not task.completed_at:
                task.completed_at = datetime.now()
            elif status == "pending":
                task.completed_at = None # Clear completed_at if moved back to pending

        session.add(task)
        session.commit()
        session.refresh(task)
    
    if task.status == "pending":
        return RedirectResponse(url="/pending-tasks", status_code=303)
    else:
        return RedirectResponse(url="/completed-tasks", status_code=303)


@app.get("/completed-tasks", response_class=HTMLResponse)
async def completed_tasks_page(request: Request):
    """Renders the completed tasks page and fetches completed tasks."""
    with Session(engine) as session:
        completed_tasks = session.exec(select(Task).where(Task.status == "completed")).all()
    return templates.TemplateResponse("completed_tasks.html", {"request": request, "tasks": completed_tasks})

@app.post("/tasks/{task_id}/move-to-pending", response_class=RedirectResponse)
async def move_to_pending(task_id: int):
    """Moves a completed task back to pending."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = "pending"
        task.completed_at = None # Clear completed_at
        session.add(task)
        session.commit()
        session.refresh(task)
    return RedirectResponse(url="/completed-tasks", status_code=303)

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, week_offset: int = 0):
    """Renders the reports page, showing time taken for tasks."""
    start_date, end_date = get_week_range(week_offset)

    with Session(engine) as session:
        # Fetch completed tasks within the selected week
        completed_tasks = session.exec(
            select(Task)
            .where(Task.status == "completed")
            .where(Task.completed_at >= start_date)
            .where(Task.completed_at <= end_date + timedelta(days=1)) # Include end_date fully
        ).all()

    daily_reports = {}
    total_minutes_this_week = 0

    for task in completed_tasks:
        if task.completed_at:
            completion_day = task.completed_at.date()
            if completion_day not in daily_reports:
                daily_reports[completion_day] = []
            daily_reports[completion_day].append(task)
            total_minutes_this_week += task.time_taken

    # Sort daily reports by date
    sorted_daily_reports = dict(sorted(daily_reports.items()))

    # Prepare week options for the dropdown
    week_options = []
    for i in range(-3, 1): # Show current week and last 3 weeks
        start, end = get_week_range(i)
        week_label = ""
        if i == 0:
            week_label = "This Week"
        elif i == -1:
            week_label = "Last Week"
        else:
            week_label = f"Week of {start.strftime('%b %d, %Y')}"
        week_options.append({"offset": i, "label": week_label, "selected": (i == week_offset)})

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "week_offset": week_offset,
            "start_date": start_date,
            "end_date": end_date,
            "daily_reports": sorted_daily_reports,
            "total_minutes_this_week": total_minutes_this_week,
            "week_options": week_options
        }
    )


@app.get("/deleted-tasks", response_class=HTMLResponse)
async def deleted_tasks_page(request: Request):
    """Renders the deleted tasks page showing backup tasks from last 15 days."""
    # Clean up old deleted tasks (older than 15 days)
    cleanup_old_deleted_tasks()
    
    with Session(engine) as session:
        # Get deleted tasks from last 15 days
        cutoff_date = datetime.now() - timedelta(days=15)
        statement = select(DeletedTask).where(DeletedTask.deleted_at >= cutoff_date).order_by(DeletedTask.deleted_at.desc())
        deleted_tasks = session.exec(statement).all()
    
    return templates.TemplateResponse(
        "deleted_tasks.html",
        {
            "request": request, 
            "deleted_tasks": deleted_tasks,
            "today": date.today(),
            "now": datetime.now()
        }
    )

@app.post("/deleted-tasks/{deleted_task_id}/restore", response_class=RedirectResponse)
async def restore_deleted_task(deleted_task_id: int):
    """Restores a deleted task back to the main tasks table."""
    with Session(engine) as session:
        deleted_task = session.get(DeletedTask, deleted_task_id)
        if not deleted_task:
            raise HTTPException(status_code=404, detail="Deleted task not found")
        
        # Create new task from backup
        restored_task = Task(
            name=deleted_task.name,
            priority=deleted_task.priority,
            task_type=deleted_task.task_type,
            start_date=deleted_task.start_date,
            deadline_date=deleted_task.deadline_date,
            time_allocated=deleted_task.time_allocated,
            time_taken=deleted_task.time_taken,
            status=deleted_task.status,
            completed_at=deleted_task.completed_at
        )
        session.add(restored_task)
        
        # Remove from deleted tasks
        session.delete(deleted_task)
        session.commit()
    
    return RedirectResponse(url="/deleted-tasks", status_code=303)

# --- Daily Task Templates ---

@app.get("/daily-templates", response_class=HTMLResponse)
async def daily_templates_page(request: Request):
    """Display daily task templates management page."""
    from datetime import date
    
    # Get error parameters from URL if any
    error = request.query_params.get('error')
    template_name = request.query_params.get('template_name')
    
    try:
        with Session(engine) as session:
            # Try to create the table if it doesn't exist
            try:
                template_list = session.exec(select(DailyTaskTemplate)).all()
            except Exception as e:
                if "no such table" in str(e):
                    # Create the table
                    print("Creating DailyTaskTemplate table...")
                    DailyTaskTemplate.__table__.create(engine, checkfirst=True)
                    template_list = []
                else:
                    raise e
    except Exception as e:
        print(f"Error in daily templates page: {e}")
        template_list = []
        return templates.TemplateResponse("daily_templates.html", {
            "request": request,
            "templates": template_list,
            "today": date.today(),
            "error": error,
            "template_name": template_name
        })
    
    return templates.TemplateResponse("daily_templates.html", {
        "request": request,
        "templates": template_list,
        "today": date.today(),
        "error": error,
        "template_name": template_name
    })

@app.post("/daily-templates", response_class=RedirectResponse)
async def create_daily_template(
    request: Request,
    name: str = Form(...),
    priority: str = Form(...),
    task_type: str = Form(...),
    time_allocated: int = Form(...)
):
    """Create a new daily task template."""
    
    # Validate task_type
    if task_type not in ["BAU", "SRE", "Automation", "Monitoring", "Observability", "Meetings", "PTO", "Holiday", "Other"]:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    with Session(engine) as session:
        # Check for duplicate template name
        existing_template = session.exec(
            select(DailyTaskTemplate)
            .where(DailyTaskTemplate.name == name.strip())
        ).first()
        
        if existing_template:
            # Redirect with error message for duplicate template
            return RedirectResponse(
                url=f"/daily-templates?error=duplicate_template&template_name={name.strip()}", 
                status_code=303
            )
        
        template = DailyTaskTemplate(
            name=name.strip(),
            priority=priority,
            task_type=task_type,
            time_allocated=time_allocated
        )
        session.add(template)
        session.commit()
    
    return RedirectResponse(url="/daily-templates", status_code=303)

@app.post("/daily-templates/{template_id}/toggle", response_class=RedirectResponse)
async def toggle_daily_template(template_id: int):
    """Toggle active status of a daily task template."""
    with Session(engine) as session:
        template = session.get(DailyTaskTemplate, template_id)
        if template:
            template.is_active = not template.is_active
            session.commit()
    
    return RedirectResponse(url="/daily-templates", status_code=303)

@app.post("/daily-templates/{template_id}/delete", response_class=RedirectResponse)
async def delete_daily_template(template_id: int):
    """Delete a daily task template."""
    with Session(engine) as session:
        template = session.get(DailyTaskTemplate, template_id)
        if template:
            session.delete(template)
            session.commit()
    
    return RedirectResponse(url="/daily-templates", status_code=303)

@app.post("/generate-daily-tasks", response_class=RedirectResponse)
async def generate_daily_tasks(target_date: str = Form(...)):
    """Generate daily tasks for a specific date based on active templates."""
    try:
        task_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    try:
        with Session(engine) as session:
            # Ensure tables exist
            try:
                # Check if tables exist by trying to query them
                session.exec(select(DailyTaskTemplate).limit(1)).first()
                session.exec(select(Task).limit(1)).first()
            except Exception as table_error:
                if "no such table" in str(table_error):
                    # Create missing tables
                    print("Creating missing tables for daily task generation...")
                    SQLModel.metadata.create_all(engine)
                else:
                    raise table_error
            
            # Get active templates
            template_list = session.exec(select(DailyTaskTemplate).where(DailyTaskTemplate.is_active == True)).all()
            
            if not template_list:
                print("No active templates found for daily task generation")
                return RedirectResponse(url="/daily-templates?error=no_templates", status_code=303)
            
            # Check if tasks already exist for this date
            existing_tasks = session.exec(
                select(Task).where(
                    Task.start_date == task_date,
                    Task.is_recurring == True
                )
            ).all()
            
            if existing_tasks:
                print(f"Daily tasks for {task_date} already exist")
                return RedirectResponse(url="/daily-templates?error=already_exist", status_code=303)
            
            # Generate tasks from templates
            created_count = 0
            for template in template_list:
                new_task = Task(
                    name=template.name,
                    priority=template.priority,
                    task_type=template.task_type,
                    start_date=task_date,
                    deadline_date=task_date,
                    time_allocated=template.time_allocated,
                    time_taken=0,
                    status="pending",
                    is_recurring=True,
                    recurring_template_id=template.id
                )
                session.add(new_task)
                created_count += 1
            
            session.commit()
            print(f"Generated {created_count} daily tasks for {task_date}")
            
    except Exception as e:
        print(f"Error generating daily tasks: {e}")
        return RedirectResponse(url="/daily-templates?error=generation_failed", status_code=303)
    
    # Redirect to pending tasks with success message
    return RedirectResponse(url=f"/pending-tasks?success=tasks_generated&count={created_count}&date={task_date}", status_code=303)

def cleanup_old_deleted_tasks():
    """Remove deleted tasks older than 15 days."""
    with Session(engine) as session:
        cutoff_date = datetime.now() - timedelta(days=15)
        statement = select(DeletedTask).where(DeletedTask.deleted_at < cutoff_date)
        old_tasks = session.exec(statement).all()
        
        for task in old_tasks:
            session.delete(task)
        
        if old_tasks:
            session.commit()
            print(f"Cleaned up {len(old_tasks)} deleted tasks older than 15 days")


# --- Frontend File Generation ---

def ensure_css_file_exists():
    """Ensure the static directory and CSS file exist."""
    # Create directories if they don't exist
    os.makedirs("static", exist_ok=True)
    
    css_path = "static/style.css"
    if not os.path.exists(css_path):
        print("Warning: CSS file not found at static/style.css")
        print("Please ensure the CSS file exists for proper styling.")


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    debug = DEBUG
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1" if debug else "0.0.0.0")
    
    print(f"🚀 Starting Todo App")
    print(f"📍 Mode: {'Development' if debug else 'Production'}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"📊 API Docs: http://{host}:{port}/docs" if debug else "📊 API Docs: Disabled in production")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )
