# AlgoForge 배포 파일

이 디렉토리에는 AlgoForge를 서버에 배포하기 위한 설정 파일들이 포함되어 있습니다.

## 📁 파일 목록

### 1. `env.example`
환경 변수 설정 파일 예시

**사용 방법:**
```bash
cp deploy/env.example .env
nano .env  # 필요에 따라 수정
```

### 2. `nginx-algoforge.conf`
Nginx 리버스 프록시 설정 파일 (포트 80 사용)

**사용 방법:**
```bash
sudo cp deploy/nginx-algoforge.conf /etc/nginx/sites-available/algoforge
sudo ln -s /etc/nginx/sites-available/algoforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. `algoforge-api.service`
Backend (FastAPI) systemd 서비스 파일

**사용 방법:**
```bash
sudo cp deploy/algoforge-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable algoforge-api
sudo systemctl start algoforge-api
```

### 4. `algoforge-web.service`
Frontend (Next.js) systemd 서비스 파일

**사용 방법:**
```bash
sudo cp deploy/algoforge-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable algoforge-web
sudo systemctl start algoforge-web
```

### 5. `backup-algoforge.sh`
데이터베이스 자동 백업 스크립트

**사용 방법:**
```bash
sudo cp deploy/backup-algoforge.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup-algoforge.sh

# 크론탭 설정 (매일 새벽 2시)
sudo crontab -e
# 다음 줄 추가:
# 0 2 * * * /usr/local/bin/backup-algoforge.sh >> /var/log/algoforge-backup.log 2>&1
```

### 6. `deploy.sh`
전체 배포 자동화 스크립트 (실험적)

**사용 방법:**
```bash
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

⚠️ **주의**: 이 스크립트는 자동으로 모든 설정을 수행합니다. 
프로덕션 환경에서는 수동 배포를 권장합니다.

## 📚 배포 가이드

전체 배포 과정은 다음 문서를 참조하세요:
- **[docs/SERVER_DEPLOYMENT_GUIDE.md](../docs/SERVER_DEPLOYMENT_GUIDE.md)** - 상세한 배포 가이드

## 🔧 환경 설정

### 도메인 및 포트
- **도메인**: algoforge.wonbbo.kro.kr
- **Nginx 포트**: 80
- **Backend 포트**: 6000 (내부)
- **Frontend 포트**: 5001 (내부)

### 경로
- **프로젝트 루트**: /var/www/algoforge
- **데이터베이스**: /var/www/algoforge/db/algoforge.db
- **백업 디렉토리**: /var/backups/algoforge

## ⚙️ 커스터마이징

다른 포트나 도메인을 사용하려면 다음 파일들을 수정하세요:

1. **env.example** - `NEXT_PUBLIC_API_URL` 수정
2. **nginx-algoforge.conf** - `listen` 포트 및 `server_name` 수정
3. **algoforge-web.service** - `NEXT_PUBLIC_API_URL` 환경 변수 수정

## 🆘 지원

배포 중 문제가 발생하면:
1. [트러블슈팅 섹션](../docs/SERVER_DEPLOYMENT_GUIDE.md#10-트러블슈팅) 확인
2. 로그 확인:
   ```bash
   sudo journalctl -u algoforge-api -n 50
   sudo journalctl -u algoforge-web -n 50
   sudo tail -f /var/log/nginx/algoforge_error.log
   ```

