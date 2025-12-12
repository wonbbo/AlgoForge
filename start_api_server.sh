#!/bin/bash
# AlgoForge API Server 시작 스크립트

echo "Starting AlgoForge API Server..."
echo

# 프로젝트 루트로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 및 서버 실행
source .venv/bin/activate
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

