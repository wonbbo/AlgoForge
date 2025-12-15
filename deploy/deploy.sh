#!/bin/bash
# AlgoForge 자동 배포 스크립트
# Ubuntu 20.04/22.04용
#
# 사용법:
# chmod +x deploy/deploy.sh
# sudo ./deploy/deploy.sh

set -e  # 에러 발생 시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정
PROJECT_DIR="/var/www/algoforge"
DOMAIN="algoforge.wonbbo.kro.kr"
NGINX_PORT=8080

# 헤더 출력 함수
print_header() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
}

# 성공 메시지
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 경고 메시지
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 에러 메시지
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 진행 메시지
print_info() {
    echo -e "${BLUE}→${NC} $1"
}

# root 권한 확인
if [ "$EUID" -ne 0 ]; then 
    print_error "이 스크립트는 root 권한이 필요합니다. sudo를 사용하세요."
    exit 1
fi

print_header "AlgoForge 배포 시작"

# 1. 시스템 업데이트
print_header "1. 시스템 업데이트"
print_info "패키지 목록 업데이트 중..."
apt update -y > /dev/null 2>&1
print_success "시스템 업데이트 완료"

# 2. 필수 패키지 설치
print_header "2. 필수 패키지 설치"
print_info "필수 패키지 설치 중..."
apt install -y git curl wget build-essential nginx python3-pip python3-venv > /dev/null 2>&1
print_success "필수 패키지 설치 완료"

# 3. Node.js 설치
print_header "3. Node.js 설치"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js가 이미 설치되어 있습니다: $NODE_VERSION"
else
    print_info "Node.js 20.x 설치 중..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt install -y nodejs > /dev/null 2>&1
    print_success "Node.js 설치 완료: $(node --version)"
fi

# 4. pnpm 설치
print_header "4. pnpm 설치"
if command -v pnpm &> /dev/null; then
    print_success "pnpm이 이미 설치되어 있습니다: $(pnpm --version)"
else
    print_info "pnpm 설치 중..."
    npm install -g pnpm > /dev/null 2>&1
    print_success "pnpm 설치 완료: $(pnpm --version)"
fi

# 5. 프로젝트 디렉토리 확인
print_header "5. 프로젝트 설정"
if [ -d "$PROJECT_DIR" ]; then
    print_warning "프로젝트 디렉토리가 이미 존재합니다: $PROJECT_DIR"
    read -p "계속하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "배포 중단"
        exit 1
    fi
else
    print_info "프로젝트 디렉토리 생성: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
    print_success "디렉토리 생성 완료"
fi

# 6. 현재 디렉토리 복사 (배포 스크립트가 프로젝트 내에서 실행된다고 가정)
CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" != "$PROJECT_DIR" ]; then
    print_info "프로젝트 파일 복사 중..."
    # deploy 디렉토리를 제외하고 복사
    rsync -av --exclude='deploy' --exclude='.git' --exclude='node_modules' \
          --exclude='venv' --exclude='__pycache__' \
          "$CURRENT_DIR/" "$PROJECT_DIR/" > /dev/null 2>&1
    print_success "파일 복사 완료"
fi

cd "$PROJECT_DIR"

# 7. Python 가상환경 및 의존성 설치
print_header "6. Backend 설정"
print_info "Python 가상환경 생성 중..."
python3 -m venv venv
source venv/bin/activate

print_info "Python 의존성 설치 중..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python 의존성 설치 완료"

# 8. 데이터베이스 초기화
print_info "데이터베이스 초기화 중..."
python scripts/reset_and_init_db.py > /dev/null 2>&1
print_success "데이터베이스 초기화 완료"

deactivate

# 9. Frontend 빌드
print_header "7. Frontend 빌드"
print_info "Frontend 의존성 설치 중..."
cd apps/web
pnpm install > /dev/null 2>&1
print_success "의존성 설치 완료"

print_info "프로덕션 빌드 중 (3-5분 소요)..."
pnpm build > /dev/null 2>&1
print_success "빌드 완료"

cd "$PROJECT_DIR"

# 10. systemd 서비스 파일 복사
print_header "8. systemd 서비스 등록"
print_info "서비스 파일 복사 중..."
cp "$CURRENT_DIR/deploy/algoforge-api.service" /etc/systemd/system/
cp "$CURRENT_DIR/deploy/algoforge-web.service" /etc/systemd/system/
print_success "서비스 파일 복사 완료"

# 11. 권한 설정
print_header "9. 권한 설정"
print_info "파일 권한 설정 중..."
chown -R www-data:www-data "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
print_success "권한 설정 완료"

# 12. 서비스 시작
print_header "10. 서비스 시작"
systemctl daemon-reload

print_info "Backend API 서비스 시작 중..."
systemctl enable algoforge-api > /dev/null 2>&1
systemctl restart algoforge-api
sleep 3
if systemctl is-active --quiet algoforge-api; then
    print_success "Backend API 서비스 실행 중"
else
    print_error "Backend API 서비스 시작 실패"
    journalctl -u algoforge-api -n 20
    exit 1
fi

print_info "Frontend 서비스 시작 중..."
systemctl enable algoforge-web > /dev/null 2>&1
systemctl restart algoforge-web
sleep 3
if systemctl is-active --quiet algoforge-web; then
    print_success "Frontend 서비스 실행 중"
else
    print_error "Frontend 서비스 시작 실패"
    journalctl -u algoforge-web -n 20
    exit 1
fi

# 13. Nginx 설정
print_header "11. Nginx 설정"
print_info "Nginx 설정 파일 복사 중..."
cp "$CURRENT_DIR/deploy/nginx-algoforge.conf" /etc/nginx/sites-available/algoforge

if [ -f /etc/nginx/sites-enabled/algoforge ]; then
    rm /etc/nginx/sites-enabled/algoforge
fi
ln -s /etc/nginx/sites-available/algoforge /etc/nginx/sites-enabled/

print_info "Nginx 설정 테스트 중..."
nginx -t > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "Nginx 설정 테스트 통과"
else
    print_error "Nginx 설정 테스트 실패"
    nginx -t
    exit 1
fi

print_info "Nginx 재시작 중..."
systemctl restart nginx
print_success "Nginx 재시작 완료"

# 14. 방화벽 설정
print_header "12. 방화벽 설정"
if command -v ufw &> /dev/null; then
    print_info "UFW 방화벽 설정 중..."
    ufw allow 22/tcp > /dev/null 2>&1
    ufw allow ${NGINX_PORT}/tcp > /dev/null 2>&1
    print_success "방화벽 설정 완료 (포트 22, ${NGINX_PORT} 허용)"
else
    print_warning "UFW가 설치되어 있지 않습니다. 수동으로 방화벽을 설정하세요."
fi

# 15. 백업 스크립트 설치
print_header "13. 백업 스크립트 설치"
print_info "백업 스크립트 설치 중..."
cp "$CURRENT_DIR/deploy/backup-algoforge.sh" /usr/local/bin/
chmod +x /usr/local/bin/backup-algoforge.sh
print_success "백업 스크립트 설치 완료"

# 16. 배포 완료
print_header "배포 완료!"

echo ""
echo -e "${GREEN}✓ AlgoForge가 성공적으로 배포되었습니다!${NC}"
echo ""
echo "========================================="
echo "접속 정보:"
echo "========================================="
echo -e "Frontend:     ${BLUE}http://${DOMAIN}:${NGINX_PORT}${NC}"
echo -e "API Docs:     ${BLUE}http://${DOMAIN}:${NGINX_PORT}/docs${NC}"
echo -e "Health Check: ${BLUE}http://${DOMAIN}:${NGINX_PORT}/api/health${NC}"
echo ""
echo "========================================="
echo "유용한 명령어:"
echo "========================================="
echo "서비스 상태 확인:"
echo "  sudo systemctl status algoforge-api"
echo "  sudo systemctl status algoforge-web"
echo ""
echo "로그 확인:"
echo "  sudo journalctl -u algoforge-api -f"
echo "  sudo journalctl -u algoforge-web -f"
echo ""
echo "서비스 재시작:"
echo "  sudo systemctl restart algoforge-api algoforge-web nginx"
echo ""
echo "백업 실행:"
echo "  sudo /usr/local/bin/backup-algoforge.sh"
echo ""
echo "========================================="
echo ""

# 상태 확인
print_info "서비스 상태 확인 중..."
sleep 2
systemctl status algoforge-api --no-pager -l | head -10
echo ""
systemctl status algoforge-web --no-pager -l | head -10
echo ""

print_success "배포 프로세스 완료!"

