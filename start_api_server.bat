@echo off
REM AlgoForge API Server 시작 스크립트

echo Starting AlgoForge API Server...
echo.

REM 가상환경 활성화 및 서버 실행
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

pause

