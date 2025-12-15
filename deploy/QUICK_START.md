# AlgoForge 빠른 배포 가이드

> 이 문서는 숙련된 사용자를 위한 빠른 배포 체크리스트입니다.  
> 자세한 설명은 [SERVER_DEPLOYMENT_GUIDE.md](../docs/SERVER_DEPLOYMENT_GUIDE.md)를 참조하세요.

## 🚀 배포 체크리스트

### 1️⃣ 사전 준비
```bash
# 서버 정보
- IP: _________________
- 도메인: algoforge.wonbbo.kro.kr
- DNS 설정 완료: [ ]
- SSH 접근: [ ]
```

### 2️⃣ 기본 환경 (서버에서 실행)
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지
sudo apt install -y git curl build-essential nginx python3-pip python3-venv

# Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# pnpm
npm install -g pnpm
```

### 3️⃣ 프로젝트 배포
```bash
# 디렉토리 생성
sudo mkdir -p /var/www/algoforge
sudo chown $USER:$USER /var/www/algoforge

# 코드 업로드 (로컬에서)
scp -r /path/to/AlgoForge/* user@server:/var/www/algoforge/

# 또는 Git (서버에서)
cd /var/www/algoforge
git clone <repo-url> .
```

### 4️⃣ Backend 설정
```bash
cd /var/www/algoforge

# Python 환경
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# DB 초기화
python scripts/reset_and_init_db.py
deactivate

# systemd 서비스
sudo cp deploy/algoforge-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable algoforge-api
sudo systemctl start algoforge-api
sudo systemctl status algoforge-api  # 확인
```

### 5️⃣ Frontend 설정
```bash
cd /var/www/algoforge/apps/web

# 빌드
pnpm install
pnpm build

# systemd 서비스
cd /var/www/algoforge
sudo cp deploy/algoforge-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable algoforge-web
sudo systemctl start algoforge-web
sudo systemctl status algoforge-web  # 확인
```

### 6️⃣ Nginx 설정
```bash
# 설정 파일 복사
sudo cp deploy/nginx-algoforge.conf /etc/nginx/sites-available/algoforge
sudo ln -s /etc/nginx/sites-available/algoforge /etc/nginx/sites-enabled/

# 테스트 및 재시작
sudo nginx -t
sudo systemctl restart nginx
```

### 7️⃣ 방화벽
```bash
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw enable
sudo ufw status
```

### 8️⃣ 권한 설정
```bash
sudo chown -R www-data:www-data /var/www/algoforge
sudo chmod -R 755 /var/www/algoforge
sudo chmod 664 /var/www/algoforge/db/algoforge.db
```

### 9️⃣ 동작 확인
```bash
# 서비스 상태
sudo systemctl status algoforge-api algoforge-web nginx

# 포트 확인
sudo netstat -tulpn | grep -E ':(3000|8000|8080)'

# 로컬 테스트
curl http://localhost:8080/api/health

# 웹 브라우저
# http://algoforge.wonbbo.kro.kr:8080
```

### 🔟 백업 설정 (선택)
```bash
# 백업 스크립트
sudo cp deploy/backup-algoforge.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup-algoforge.sh

# 크론탭 (매일 새벽 2시)
sudo crontab -e
# 추가: 0 2 * * * /usr/local/bin/backup-algoforge.sh >> /var/log/algoforge-backup.log 2>&1
```

## ✅ 완료 확인

- [ ] Backend API 서비스 실행 중
- [ ] Frontend 서비스 실행 중  
- [ ] Nginx 서비스 실행 중
- [ ] 방화벽 8080 포트 오픈
- [ ] 웹 브라우저 접속 성공
- [ ] API Health Check 응답 정상
- [ ] 로그 에러 없음

## 🔧 자주 사용하는 명령어

```bash
# 서비스 재시작
sudo systemctl restart algoforge-api algoforge-web nginx

# 로그 확인
sudo journalctl -u algoforge-api -f
sudo journalctl -u algoforge-web -f
sudo tail -f /var/log/nginx/algoforge_error.log

# 코드 업데이트
cd /var/www/algoforge
git pull
cd apps/web && pnpm install && pnpm build && cd ../..
sudo systemctl restart algoforge-api algoforge-web
```

## 🆘 트러블슈팅

**502 Bad Gateway**
```bash
sudo systemctl status algoforge-api algoforge-web
sudo journalctl -u algoforge-api -n 50
```

**포트 충돌**
```bash
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :8080
```

**권한 문제**
```bash
sudo chown -R www-data:www-data /var/www/algoforge
sudo chmod 664 /var/www/algoforge/db/algoforge.db
```

---

**자세한 내용**: [SERVER_DEPLOYMENT_GUIDE.md](../docs/SERVER_DEPLOYMENT_GUIDE.md)

