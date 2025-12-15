# AlgoForge 서버 배포 가이드

> **배포 환경**: Ubuntu 20.04/22.04  
> **도메인**: algoforge.wonbbo.kro.kr  
> **Nginx 포트**: 80
> **프로젝트 경로**: /var/www/algoforge

---

## 📋 목차

1. [배포 전 준비사항](#1-배포-전-준비사항)
2. [서버 기본 환경 설정](#2-서버-기본-환경-설정)
3. [프로젝트 배포](#3-프로젝트-배포)
4. [Backend (FastAPI) 설정](#4-backend-fastapi-설정)
5. [Frontend (Next.js) 설정](#5-frontend-nextjs-설정)
6. [Nginx 리버스 프록시 설정](#6-nginx-리버스-프록시-설정)
7. [방화벽 설정](#7-방화벽-설정)
8. [동작 확인](#8-동작-확인)
9. [유지보수 가이드](#9-유지보수-가이드)
10. [트러블슈팅](#10-트러블슈팅)

---

## 1. 배포 전 준비사항

### 1.1 로컬 환경에서 준비

#### ✅ 필수 체크리스트
- [ ] 서버 SSH 접근 정보 확인
- [ ] 도메인 DNS 설정 완료 (algoforge.wonbbo.kro.kr → 서버 IP)
- [ ] 서버 사용 가능한 포트 확인 (80, 5001, 6000)
- [ ] Git 저장소 준비 (또는 파일 직접 전송)

#### 환경 변수 파일 준비

프로젝트 루트에 `.env` 파일 생성:

```bash
# Backend API 설정
API_HOST=0.0.0.0
API_PORT=6000

# Frontend 설정
NEXT_PUBLIC_API_URL=http://algoforge.wonbbo.kro.kr/api

# 데이터베이스 경로
DATABASE_PATH=./db/algoforge.db
```

#### 빌드 테스트 (선택사항)

```bash
# Frontend 빌드 테스트
cd apps/web
pnpm install
pnpm build

# Backend 테스트
cd ../..
python -m pytest tests/
```

---

## 2. 서버 기본 환경 설정

### 2.1 시스템 업데이트

```bash
# 시스템 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y git curl wget build-essential nginx
```

### 2.2 Python 3.10+ 설치

```bash
# Python 버전 확인
python3 --version

# Python 3.10 이상이 아니면 설치
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip
```

### 2.3 Node.js 20+ 설치

```bash
# Node.js 20.x 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 버전 확인
node --version  # v20.x.x 이상
npm --version
```

### 2.4 pnpm 설치

```bash
# pnpm 전역 설치
npm install -g pnpm

# 버전 확인
pnpm --version
```

---

## 3. 프로젝트 배포

### 3.1 작업 디렉토리 생성

```bash
# 배포 디렉토리 생성
sudo mkdir -p /var/www/algoforge
sudo chown $USER:$USER /var/www/algoforge
cd /var/www/algoforge
```

### 3.2 프로젝트 코드 배포

**방법 1: Git 저장소에서 클론**

```bash
git clone <your-repository-url> .
```

**방법 2: 로컬에서 파일 전송**

```bash
# 로컬 터미널에서 실행
scp -r /path/to/AlgoForge/* user@server:/var/www/algoforge/
```

### 3.3 환경 변수 파일 설정

```bash
cd /var/www/algoforge

# .env 파일 생성 (또는 로컬에서 복사한 파일 사용)
nano .env
```

`.env` 파일 내용:

```bash
# Backend API 설정
API_HOST=0.0.0.0
API_PORT=6000

# Frontend 설정
NEXT_PUBLIC_API_URL=http://algoforge.wonbbo.kro.kr/api

# 데이터베이스 경로
DATABASE_PATH=./db/algoforge.db
```

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

---

## 4. Backend (FastAPI) 설정

### 4.1 Python 가상환경 생성 및 의존성 설치

```bash
cd /var/www/algoforge

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# Python 의존성 설치
pip install -r requirements.txt
```

### 4.2 데이터베이스 초기화

```bash
# 데이터베이스 디렉토리 생성
mkdir -p db

# 데이터베이스 초기화 스크립트 실행
python scripts/reset_and_init_db.py
```

### 4.3 API 서버 테스트

```bash
# 테스트 실행 (Ctrl+C로 종료)
cd /var/www/algoforge
source venv/bin/activate
python apps/api/main.py

# 별도 터미널에서 확인
curl http://localhost:6000/health
```

성공 응답 확인 후 `Ctrl + C`로 종료

### 4.4 systemd 서비스 등록

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/algoforge-api.service
```

다음 내용 입력:

```ini
[Unit]
Description=AlgoForge FastAPI Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/algoforge
Environment="PATH=/var/www/algoforge/venv/bin"
Environment="PYTHONPATH=/var/www/algoforge"
ExecStart=/var/www/algoforge/venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 6000 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

저장 후:

```bash
# 파일 및 디렉토리 권한 설정
sudo chown -R www-data:www-data /var/www/algoforge
sudo chmod -R 755 /var/www/algoforge

# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable algoforge-api
sudo systemctl start algoforge-api

# 상태 확인
sudo systemctl status algoforge-api
```

**✅ 성공 확인**: `active (running)` 상태 확인

```bash
# 로그 확인
sudo journalctl -u algoforge-api -f
```

---

## 5. Frontend (Next.js) 설정

### 5.1 의존성 설치 및 빌드

```bash
cd /var/www/algoforge/apps/web

# 의존성 설치
pnpm install

# 프로덕션 빌드
pnpm build
```

**⏱️ 예상 소요 시간**: 3-5분

### 5.2 빌드 결과 테스트

```bash
# 테스트 실행 (Ctrl+C로 종료)
pnpm start
```

별도 터미널에서 확인:

```bash
curl http://localhost:5001
```

성공 응답 확인 후 `Ctrl + C`로 종료

### 5.3 systemd 서비스 등록

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/algoforge-web.service
```

다음 내용 입력:

```ini
[Unit]
Description=AlgoForge Next.js Frontend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/algoforge/apps/web
Environment="NODE_ENV=production"
Environment="PORT=5001"
Environment="NEXT_PUBLIC_API_URL=http://algoforge.wonbbo.kro.kr/api"
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

저장 후:

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable algoforge-web
sudo systemctl start algoforge-web

# 상태 확인
sudo systemctl status algoforge-web
```

**✅ 성공 확인**: `active (running)` 상태 확인

```bash
# 로그 확인
sudo journalctl -u algoforge-web -f
```

---

## 6. Nginx 리버스 프록시 설정

### 6.1 Nginx 설정 파일 생성

```bash
# 설정 파일 생성
sudo nano /etc/nginx/sites-available/algoforge
```

다음 내용 입력:

```nginx
# AlgoForge Nginx 설정
# 포트: 80
# 도메인: algoforge.wonbbo.kro.kr

upstream frontend {
    server localhost:5001;
}

upstream backend {
    server localhost:6000;
}

server {
    listen 80;
    server_name algoforge.wonbbo.kro.kr;

    # 클라이언트 최대 업로드 크기 (데이터셋 파일 업로드용)
    client_max_body_size 100M;

    # 로그 설정
    access_log /var/log/nginx/algoforge_access.log;
    error_log /var/log/nginx/algoforge_error.log;

    # Frontend (Next.js) - 루트 경로
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Backend (FastAPI) - /api 경로
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 타임아웃 설정 (백테스트 실행 시간 고려)
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # FastAPI Docs
    location /docs {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health Check
    location /health {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

### 6.2 Nginx 설정 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/algoforge /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t
```

**✅ 성공 메시지**: `syntax is okay`, `test is successful`

### 6.3 Nginx 재시작

```bash
# Nginx 재시작
sudo systemctl restart nginx

# 상태 확인
sudo systemctl status nginx
```

---

## 7. 방화벽 설정

### 7.1 UFW 방화벽 설정

```bash
# UFW 설치 (이미 설치되어 있으면 스킵)
sudo apt install -y ufw

# 기본 정책 설정
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 필요한 포트 열기
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # Nginx (AlgoForge)

# 방화벽 활성화
sudo ufw enable

# 상태 확인
sudo ufw status verbose
```

**출력 예시:**

```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
```

### 7.2 클라우드 방화벽 설정 (선택사항)

AWS, GCP, Azure 등 클라우드 환경에서는 별도로 보안 그룹/방화벽 규칙 설정 필요:

- **인바운드 규칙 추가**:
  - 포트 22 (SSH)
  - 포트 80 (HTTP)

---

## 8. 동작 확인

### 8.1 서비스 상태 확인

```bash
# 모든 서비스 상태 확인
sudo systemctl status algoforge-api
sudo systemctl status algoforge-web
sudo systemctl status nginx
```

**✅ 모두 `active (running)` 상태여야 함**

### 8.2 포트 리스닝 확인

```bash
# 포트 확인
sudo netstat -tulpn | grep -E ':(5001|6000|80)'
```

**예상 출력:**

```
tcp  0  0 0.0.0.0:5001   0.0.0.0:*   LISTEN   1234/node
tcp  0  0 0.0.0.0:6000   0.0.0.0:*   LISTEN   5678/python
tcp  0  0 0.0.0.0:80     0.0.0.0:*   LISTEN   9012/nginx
```

### 8.3 로컬 테스트

```bash
# Backend API 헬스 체크
curl http://localhost:6000/health

# Frontend 확인
curl http://localhost:5001

# Nginx를 통한 접근 확인
curl http://localhost/health
curl http://localhost/api/health
```

### 8.4 외부 접근 테스트

**웹 브라우저에서 접속:**

1. **Frontend**: http://algoforge.wonbbo.kro.kr
2. **API Docs**: http://algoforge.wonbbo.kro.kr/docs
3. **Health Check**: http://algoforge.wonbbo.kro.kr/api/health

**예상 결과:**

- Frontend: AlgoForge UI 정상 표시
- API Docs: FastAPI Swagger UI 표시
- Health Check: JSON 응답 `{"status": "healthy", ...}`

### 8.5 로그 확인

```bash
# API 로그 (실시간)
sudo journalctl -u algoforge-api -f

# Frontend 로그 (실시간)
sudo journalctl -u algoforge-web -f

# Nginx 로그
sudo tail -f /var/log/nginx/algoforge_access.log
sudo tail -f /var/log/nginx/algoforge_error.log
```

---

## 9. 유지보수 가이드

### 9.1 서비스 관리 명령어

#### 서비스 재시작

```bash
# API 재시작
sudo systemctl restart algoforge-api

# Frontend 재시작
sudo systemctl restart algoforge-web

# Nginx 재시작
sudo systemctl restart nginx

# 모두 재시작
sudo systemctl restart algoforge-api algoforge-web nginx
```

#### 서비스 중지/시작

```bash
# 중지
sudo systemctl stop algoforge-api
sudo systemctl stop algoforge-web

# 시작
sudo systemctl start algoforge-api
sudo systemctl start algoforge-web
```

#### 서비스 상태 확인

```bash
sudo systemctl status algoforge-api
sudo systemctl status algoforge-web
sudo systemctl status nginx
```

### 9.2 코드 업데이트

```bash
# 1. 서비스 중지
sudo systemctl stop algoforge-api algoforge-web

# 2. 코드 업데이트
cd /var/www/algoforge
git pull  # 또는 파일 직접 전송

# 3. Backend 의존성 업데이트 (필요 시)
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 4. Frontend 재빌드 (필요 시)
cd apps/web
pnpm install
pnpm build
cd ../..

# 5. 권한 재설정
sudo chown -R www-data:www-data /var/www/algoforge

# 6. 서비스 재시작
sudo systemctl start algoforge-api algoforge-web
sudo systemctl status algoforge-api algoforge-web
```

### 9.3 데이터베이스 백업

#### 수동 백업

```bash
# 백업 디렉토리 생성
sudo mkdir -p /var/backups/algoforge

# 백업 실행
sudo cp /var/www/algoforge/db/algoforge.db \
    /var/backups/algoforge/algoforge_$(date +%Y%m%d_%H%M%S).db

# 백업 확인
ls -lh /var/backups/algoforge/
```

#### 자동 백업 스크립트

```bash
# 백업 스크립트 생성
sudo nano /usr/local/bin/backup-algoforge.sh
```

스크립트 내용:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/algoforge"
DB_PATH="/var/www/algoforge/db/algoforge.db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/algoforge_$DATE.db"
    echo "$(date): Backup completed - algoforge_$DATE.db"
else
    echo "$(date): ERROR - Database file not found: $DB_PATH"
    exit 1
fi

# 오래된 백업 삭제 (7일 이상)
find "$BACKUP_DIR" -name "algoforge_*.db" -mtime +$RETENTION_DAYS -delete
echo "$(date): Old backups cleaned (older than $RETENTION_DAYS days)"
```

실행 권한 부여 및 크론탭 설정:

```bash
# 실행 권한 부여
sudo chmod +x /usr/local/bin/backup-algoforge.sh

# 테스트 실행
sudo /usr/local/bin/backup-algoforge.sh

# 크론탭 설정 (매일 새벽 2시)
sudo crontab -e

# 다음 줄 추가:
0 2 * * * /usr/local/bin/backup-algoforge.sh >> /var/log/algoforge-backup.log 2>&1
```

### 9.4 로그 관리

#### 로그 확인

```bash
# 최근 100줄 확인
sudo journalctl -u algoforge-api -n 100
sudo journalctl -u algoforge-web -n 100

# 실시간 로그 확인
sudo journalctl -u algoforge-api -f
sudo journalctl -u algoforge-web -f

# 특정 시간대 로그 확인
sudo journalctl -u algoforge-api --since "2024-01-01 00:00:00" --until "2024-01-01 23:59:59"

# Nginx 로그
sudo tail -n 100 /var/log/nginx/algoforge_access.log
sudo tail -n 100 /var/log/nginx/algoforge_error.log
```

#### 로그 로테이션 (자동)

systemd 및 nginx는 자동으로 로그 로테이션 처리

---

## 10. 트러블슈팅

### 10.1 서비스가 시작되지 않을 때

#### API 서비스 실패

```bash
# 상태 확인
sudo systemctl status algoforge-api

# 자세한 로그 확인
sudo journalctl -u algoforge-api -n 50

# 수동 실행으로 에러 확인
cd /var/www/algoforge
source venv/bin/activate
python apps/api/main.py
```

**일반적인 원인:**

1. **Python 의존성 누락**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **데이터베이스 파일 권한 문제**
   ```bash
   sudo chown -R www-data:www-data /var/www/algoforge/db
   sudo chmod 664 /var/www/algoforge/db/algoforge.db
   ```

3. **포트 충돌 (6000 포트)**
   ```bash
   sudo lsof -i :6000
   # 다른 프로세스가 사용 중이면 종료 또는 포트 변경
   ```

#### Frontend 서비스 실패

```bash
# 상태 확인
sudo systemctl status algoforge-web

# 자세한 로그 확인
sudo journalctl -u algoforge-web -n 50

# 수동 실행으로 에러 확인
cd /var/www/algoforge/apps/web
pnpm start
```

**일반적인 원인:**

1. **빌드 안 됨**
   ```bash
   cd /var/www/algoforge/apps/web
   pnpm install
   pnpm build
   ```

2. **포트 충돌 (5001 포트)**
   ```bash
   sudo lsof -i :5001
   ```

3. **환경 변수 누락**
   ```bash
   # systemd 서비스 파일에 환경 변수 확인
   sudo nano /etc/systemd/system/algoforge-web.service
   ```

### 10.2 Nginx 502 Bad Gateway 에러

**증상:** 웹 브라우저에서 접속 시 "502 Bad Gateway" 표시

**원인 및 해결:**

1. **Backend/Frontend 서비스 미실행**
   ```bash
   sudo systemctl status algoforge-api
   sudo systemctl status algoforge-web
   
   # 중지되어 있으면 시작
   sudo systemctl start algoforge-api algoforge-web
   ```

2. **포트 불일치**
   ```bash
   # Nginx 설정 확인
   sudo nano /etc/nginx/sites-available/algoforge
   
   # upstream 부분의 포트가 실제 서비스 포트와 일치하는지 확인
   ```

3. **SELinux 문제 (CentOS/RHEL)**
   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

### 10.3 데이터베이스 에러

#### "Database locked" 에러

```bash
# 데이터베이스 파일 권한 확인
ls -la /var/www/algoforge/db/algoforge.db

# 권한 수정
sudo chown www-data:www-data /var/www/algoforge/db/algoforge.db
sudo chmod 664 /var/www/algoforge/db/algoforge.db
```

#### "Database file not found" 에러

```bash
# 데이터베이스 초기화
cd /var/www/algoforge
source venv/bin/activate
python scripts/reset_and_init_db.py
```

### 10.4 도메인 접속 안 될 때

#### DNS 확인

```bash
# 도메인 DNS 확인
nslookup algoforge.wonbbo.kro.kr
dig algoforge.wonbbo.kro.kr

# 서버 IP와 일치하는지 확인
```

#### 방화벽 확인

```bash
# UFW 상태 확인
sudo ufw status verbose

# 80 포트가 열려있는지 확인
sudo ufw allow 80/tcp
```

#### Nginx 리스닝 확인

```bash
# Nginx가 80 포트에서 리스닝하는지 확인
sudo netstat -tulpn | grep :80

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 10.5 API 호출 CORS 에러

**증상:** 브라우저 콘솔에 CORS 에러 표시

**해결:**

```bash
# API main.py의 CORS 설정 확인
cd /var/www/algoforge
nano apps/api/main.py
```

다음 부분 확인 및 수정:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://algoforge.wonbbo.kro.kr",
        "http://localhost:5001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

수정 후:

```bash
# 서비스 재시작
sudo systemctl restart algoforge-api
```

### 10.6 성능 문제

#### CPU/메모리 사용량 확인

```bash
# 실시간 모니터링
htop

# 또는
top

# 서비스별 리소스 사용량
sudo systemctl status algoforge-api
sudo systemctl status algoforge-web
```

#### 로그 파일 크기 확인

```bash
# Nginx 로그 크기 확인
du -sh /var/log/nginx/

# systemd 로그 크기 확인
sudo journalctl --disk-usage

# 오래된 로그 정리
sudo journalctl --vacuum-time=7d
```

### 10.7 긴급 복구

#### 전체 서비스 재시작

```bash
# 모든 서비스 중지
sudo systemctl stop algoforge-api algoforge-web nginx

# 10초 대기
sleep 10

# 순서대로 재시작
sudo systemctl start algoforge-api
sleep 5
sudo systemctl start algoforge-web
sleep 5
sudo systemctl start nginx

# 상태 확인
sudo systemctl status algoforge-api algoforge-web nginx
```

#### 백업에서 복구

```bash
# 백업 목록 확인
ls -lh /var/backups/algoforge/

# 특정 시점으로 복구
sudo cp /var/backups/algoforge/algoforge_20240101_020000.db \
    /var/www/algoforge/db/algoforge.db

# 권한 재설정
sudo chown www-data:www-data /var/www/algoforge/db/algoforge.db
sudo chmod 664 /var/www/algoforge/db/algoforge.db

# 서비스 재시작
sudo systemctl restart algoforge-api
```

---

## 📌 체크리스트

배포 완료 후 다음 항목을 확인하세요:

- [ ] Python 3.10+ 및 Node.js 20+ 설치 완료
- [ ] 프로젝트 코드 `/var/www/algoforge`에 배포 완료
- [ ] 환경 변수 `.env` 파일 설정 완료
- [ ] Python 의존성 설치 완료
- [ ] 데이터베이스 초기화 완료
- [ ] Backend API 서비스 `active (running)` 상태
- [ ] Frontend 서비스 `active (running)` 상태
- [ ] Nginx 서비스 `active (running)` 상태
- [ ] 방화벽 80 포트 오픈 완료
- [ ] 도메인 DNS 설정 완료 (algoforge.wonbbo.kro.kr)
- [ ] 웹 브라우저로 접속 테스트 통과
- [ ] API Health Check 응답 정상
- [ ] 로그 확인 (에러 없음)
- [ ] 백업 스크립트 설정 완료

---

## 📞 참고 자료

### 주요 경로

```
프로젝트 루트: /var/www/algoforge
데이터베이스: /var/www/algoforge/db/algoforge.db
백업 디렉토리: /var/backups/algoforge
로그 디렉토리: /var/log/nginx/
```

### 서비스 파일

```
API 서비스: /etc/systemd/system/algoforge-api.service
Frontend 서비스: /etc/systemd/system/algoforge-web.service
Nginx 설정: /etc/nginx/sites-available/algoforge
```

### 접속 URL

```
Frontend: http://algoforge.wonbbo.kro.kr
API Docs: http://algoforge.wonbbo.kro.kr/docs
Health Check: http://algoforge.wonbbo.kro.kr/api/health
```

### 유용한 명령어

```bash
# 전체 상태 확인
sudo systemctl status algoforge-api algoforge-web nginx | grep Active

# 전체 로그 실시간 확인 (3개 터미널 필요)
sudo journalctl -u algoforge-api -f
sudo journalctl -u algoforge-web -f
sudo tail -f /var/log/nginx/algoforge_error.log

# 포트 사용 확인
sudo netstat -tulpn | grep -E ':(5001|6000|80)'

# 디스크 사용량 확인
df -h
du -sh /var/www/algoforge
du -sh /var/backups/algoforge
```

---

## 📝 변경 이력

- **2024-12-15**: 초기 배포 가이드 작성 (포트 80 사용, algoforge.wonbbo.kro.kr 도메인)

---

**배포 완료 후 문제가 발생하면 [트러블슈팅](#10-트러블슈팅) 섹션을 참고하세요.**

