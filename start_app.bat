@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Python launcher not found. Install Python 3.11 or later.& pause & exit /b 1)
if not exist .venv py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (echo Package installation failed.& pause & exit /b 1)
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
pause
