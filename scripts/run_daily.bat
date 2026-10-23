
@echo off
cd /d "C:\Users\manid\OneDrive\Documents\Job_Market_Analytics"

call ".venv\Scripts\activate.bat"

python scripts\run_pipeline.py >> reports\pipeline.log 2>&1

exit /b %ERRORLEVEL%
