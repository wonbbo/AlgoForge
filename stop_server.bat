@echo off
chcp 65001 > nul
echo ================================
echo Backend 서버 안전 종료 (Graceful)
echo ================================
echo.

REM 서버 실행 여부 확인
netstat -ano | findstr :8000 | findstr LISTENING > nul
if errorlevel 1 (
    echo [알림] 포트 8000에서 실행 중인 서버가 없습니다.
    echo.
    pause
    exit /b 0
)

echo [확인] 서버가 실행 중입니다.
echo.

REM RUNNING 상태인 작업 확인
if exist "algoforge.db" (
    echo [확인] 실행 중인 백테스팅 작업 확인 중...
    python -c "import sqlite3; conn = sqlite3.connect('algoforge.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM runs WHERE status=\"RUNNING\"'); count = cursor.fetchone()[0]; conn.close(); exit(count)" 2>nul
    
    if not errorlevel 1 (
        echo [안전] 현재 실행 중인 백테스팅 작업이 없습니다.
        echo 서버를 안전하게 종료할 수 있습니다.
    ) else (
        echo.
        echo [경고] 백테스팅 작업이 실행 중입니다!
        echo.
        echo 안전한 종료 방법:
        echo  1. Frontend 또는 API에서 작업이 완료될 때까지 대기
        echo  2. 또는 API를 통해 Run을 CANCEL 처리 후 종료
        echo.
        echo 지금 강제 종료하시겠습니까? (Y/N)
        choice /C YN /N
        if errorlevel 2 (
            echo.
            echo [취소] 서버 종료를 취소했습니다.
            echo.
            echo [팁] 작업 상태 확인: check_running_jobs.bat
            pause
            exit /b 0
        )
    )
)

echo.
echo [진행] 서버에 종료 신호를 보냅니다...
echo [안내] 터미널에서 Ctrl+C를 눌러 안전하게 종료하세요.
echo [안내] 또는 10초 후 강제 종료합니다...
echo.

REM 사용자에게 10초 대기 시간 제공
timeout /t 10

REM 여전히 실행 중이면 강제 종료
netstat -ano | findstr :8000 | findstr LISTENING > nul
if not errorlevel 1 (
    echo [진행] 강제 종료를 실행합니다...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        taskkill /PID %%a /F > nul 2>&1
        if not errorlevel 1 (
            echo [성공] 프로세스 %%a 종료 완료
        )
    )
)

echo.
echo ================================
echo 완료
echo ================================
pause

