@echo off
chcp 65001 > nul
echo ================================
echo 백테스팅 작업 상태 확인
echo ================================
echo.

REM 서버 실행 여부 확인
netstat -ano | findstr :8000 | findstr LISTENING > nul
if errorlevel 1 (
    echo [알림] Backend 서버가 실행 중이 아닙니다.
    echo.
    pause
    exit /b 0
)

echo [확인] Backend 서버 실행 중
echo.

REM SQLite DB가 있는지 확인
if not exist "algoforge.db" (
    echo [알림] 데이터베이스 파일이 없습니다.
    echo 아직 백테스팅 작업이 실행된 적이 없는 것 같습니다.
    echo.
    pause
    exit /b 0
)

echo [확인] 데이터베이스 연결 중...
echo.

REM Python으로 RUNNING 상태인 Run 확인
python -c "import sqlite3; conn = sqlite3.connect('algoforge.db'); cursor = conn.cursor(); cursor.execute('SELECT run_id, dataset_id, strategy_id, started_at FROM runs WHERE status=\"RUNNING\"'); rows = cursor.fetchall(); conn.close(); print('=== RUNNING 상태인 작업 ===') if rows else None; [print(f'Run ID: {r[0]}, Dataset: {r[1]}, Strategy: {r[2]}, 시작: {r[3]}') for r in rows]; print(f'\n총 {len(rows)}개의 작업이 실행 중입니다.') if rows else print('[알림] 현재 실행 중인 백테스팅 작업이 없습니다.')" 2>nul

if errorlevel 1 (
    echo [오류] Python을 찾을 수 없거나 데이터베이스 접근 실패
    echo 수동으로 확인하세요: http://localhost:8000/docs
)

echo.
echo ================================
echo 완료
echo ================================
pause

