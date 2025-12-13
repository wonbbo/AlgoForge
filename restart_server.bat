@echo off
chcp 65001 > nul
echo ================================
echo Backend 서버 재시작 중...
echo ================================
echo.

REM 서버 중지
call stop_server.bat

REM 잠시 대기
echo.
echo 2초 후 서버를 다시 시작합니다...
timeout /t 2 > nul

REM 서버 시작
call start_server.bat

