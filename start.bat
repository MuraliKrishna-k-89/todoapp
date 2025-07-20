@echo off
echo 🚀 Starting Todo App on Windows...

REM Set environment variables
if not defined DEBUG set DEBUG=false
if not defined DATABASE_URL set DATABASE_URL=sqlite:///todo.db
if not defined HOST set HOST=0.0.0.0
if not defined PORT set PORT=8111

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Run database setup
echo 🗄️ Setting up database...
python -c "from main import create_db_and_tables, migrate_database; create_db_and_tables(); migrate_database(); print('Database setup complete!')"

REM Start the application with Uvicorn (Windows-compatible)
echo 🌟 Starting application with Uvicorn...
echo 📍 Access your app at: http://localhost:%PORT%
echo 📍 Press Ctrl+C to stop the server

uvicorn main:app --host %HOST% --port %PORT% --reload
