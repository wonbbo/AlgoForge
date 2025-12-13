# AlgoForge 서버 관리 가이드

Backend 서버를 안전하게 관리하기 위한 배치 스크립트 모음입니다.

## 📋 스크립트 목록

### 1. `start_server.bat` - 서버 시작
Backend 서버를 시작합니다.

**기능**:
- 포트 충돌 자동 감지
- 가상환경 자동 활성화 (있는 경우)
- 개발 모드(--reload)로 FastAPI 서버 시작
- API 문서 링크 표시

**사용법**:
```bash
start_server.bat
```

---

### 2. `stop_server.bat` - 서버 안전 종료
백테스팅 작업을 확인하고 안전하게 종료합니다.

**기능**:
- RUNNING 상태인 Run 자동 확인
- 10초 대기 시간 제공 (Ctrl+C 입력 가능)
- 안전 종료 가이드 제공

**권장 사용법**:
이 스크립트를 실행한 후:
1. 백테스팅이 없으면 바로 종료
2. 백테스팅이 있으면 경고 → 10초 대기 → 필요시 Ctrl+C로 취소

**사용법**:
```bash
graceful_stop_server.bat
```

---

### 3. `restart_server.bat` - 서버 재시작
서버를 중지한 후 다시 시작합니다.

**기능**:
- stop_server.bat 실행
- 2초 대기
- start_server.bat 실행

**사용법**:
```bash
restart_server.bat
```

---

### 4. `check_running_jobs.bat` - 백테스팅 작업 상태 확인
현재 실행 중인 백테스팅 작업을 확인합니다.

**기능**:
- 서버 실행 여부 확인
- SQLite DB에서 RUNNING 상태인 Run 조회
- Run ID, Dataset ID, Strategy ID, 시작 시간 표시

**사용법**:
```bash
check_running_jobs.bat
```

**출력 예시**:
```
=== RUNNING 상태인 작업 ===
Run ID: 42, Dataset: 5, Strategy: 3, 시작: 1702456789
Run ID: 43, Dataset: 5, Strategy: 4, 시작: 1702456800

총 2개의 작업이 실행 중입니다.
```

---

## 🎯 사용 시나리오

### 시나리오 1: 일반적인 개발 작업
```bash
# 1. 서버 시작
start_server.bat

# 2. 개발 작업...

# 3. 서버 종료
stop_server.bat
```

### 시나리오 2: 백테스팅 실행 중
```bash
# 1. 작업 상태 확인
check_running_jobs.bat

# 2. 작업이 있으면 완료 대기 또는 취소

# 3. 안전하게 종료
stop_server.bat
```

### 시나리오 3: 긴급 종료 필요
```bash
# Ctrl+C가 작동하지 않을 때
stop_server.bat  # Y를 눌러 강제 종료 확인
```

### 시나리오 4: 코드 변경 후 재시작
```bash
# 빠른 재시작
restart_server.bat
```

---

## ⚠️ 주의사항

### 백테스팅 작업 중단 시 영향
서버를 강제 종료하면:
- ✅ 서버 프로세스 종료
- ❌ 실행 중인 백테스팅 작업 중단
- ❌ 부분적인 결과만 DB에 저장될 수 있음
- ❌ Run 상태가 'RUNNING'으로 남을 수 있음

### 중단된 Run 처리 방법
1. 서버 재시작
2. Frontend 또는 API에서 'RUNNING' 상태인 Run 확인
3. 해당 Run을 다시 실행하거나 삭제

---

## 🔧 문제 해결

### Q1. 포트 8000이 이미 사용 중입니다
**해결책**:
```bash
stop_server.bat  # 기존 서버 종료
start_server.bat  # 다시 시작
```

### Q2. Python을 찾을 수 없습니다
**원인**: Python이 PATH에 등록되지 않음

**해결책**:
- Python 설치 확인
- 가상환경 활성화 확인
- 수동으로 API 접속: http://localhost:8000/docs

### Q3. 스크립트 실행이 안 됩니다
**해결책**:
- 관리자 권한으로 실행
- 프로젝트 루트 폴더에서 실행
- 한글 경로 확인 (UTF-8 인코딩 사용)

### Q4. Ctrl+C가 작동하지 않습니다
**해결책**:
```bash
stop_server.bat  # 강제 종료
```

---

## 🚀 Best Practices

### 권장 사항
1. ✅ 개발 시작: `start_server.bat`
2. ✅ 개발 종료: `stop_server.bat`
3. ✅ 긴 백테스팅 전: `check_running_jobs.bat`로 확인
4. ✅ 코드 변경 후: `restart_server.bat`

### 지양 사항
1. ❌ 백테스팅 실행 중 강제 종료
2. ❌ 작업 관리자에서 직접 프로세스 종료
3. ❌ 상태 확인 없이 재시작

---

## 📚 관련 문서
- [AlgoForge PRD](docs/AlgoForge_PRD_v1.0.md)
- [AlgoForge TRD](docs/AlgoForge_TRD_v1.0.md)
- [API 문서](http://localhost:8000/docs) (서버 실행 시)

---

## 💡 팁

### 터미널에서 직접 관리
스크립트 없이 수동으로 관리하려면:

```bash
# 서버 시작
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 서버 중지 (터미널에서)
Ctrl+C

# 포트 확인
netstat -ano | findstr :8000

# 프로세스 강제 종료
taskkill /PID <프로세스ID> /F
```

### 로그 확인
서버 실행 시 터미널에 로그가 실시간으로 표시됩니다.
오류 발생 시 로그를 확인하세요.

---

## 📝 버전 정보
- 작성일: 2025-01-13
- 대상: AlgoForge v1.0
- OS: Windows 10/11

