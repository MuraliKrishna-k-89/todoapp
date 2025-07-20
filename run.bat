@echo off
REM Simple script to run the Todo App quickly on Windows

echo 🚀 Quick Start - Todo App

REM Use your existing Python environment or virtual environment
echo 🌟 Starting Todo App...
echo 📍 Your app will be available at: http://localhost:800
echo 📍 Press Ctrl+C to stop

python -m uvicorn main:app --host 0.0.0.0 --port 800 --reload
