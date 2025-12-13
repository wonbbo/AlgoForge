@echo off
chcp 65001 > nul
echo ================================
echo Backend 서버 시작 중...
echo ================================
echo.

REM 현재 디렉토리 확인
echo 현재 위치: %CD%
echo.

REM 포트 8000이 이미 사용 중인지 확인
netstat -ano | findstr :8000 | findstr LISTENING > nul
if not errorlevel 1 (
    echo [경고] 포트 8000이 이미 사용 중입니다.
    echo 기존 서버를 먼저 종료하시겠습니까? (Y/N)
    choice /C YN /N
    if errorlevel 2 goto :END
    if errorlevel 1 call stop_server.bat
    timeout /t 2 > nul
)

REM Python 가상환경 활성화 (venv가 있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
    echo.
)

REM FastAPI 서버 시작
echo FastAPI 서버 시작...
echo API 문서: http://localhost:8000/docs
echo.
echo [중지하려면 Ctrl+C를 누르세요]
echo ================================
echo.

cd apps\api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

:END

