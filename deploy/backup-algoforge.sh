#!/bin/bash
# AlgoForge 데이터베이스 백업 스크립트
#
# 설치 방법:
# sudo cp deploy/backup-algoforge.sh /usr/local/bin/
# sudo chmod +x /usr/local/bin/backup-algoforge.sh
#
# 크론탭 설정 (매일 새벽 2시):
# sudo crontab -e
# 0 2 * * * /usr/local/bin/backup-algoforge.sh >> /var/log/algoforge-backup.log 2>&1

# 설정
BACKUP_DIR="/var/backups/algoforge"
DB_PATH="/var/www/algoforge/db/algoforge.db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "AlgoForge 백업 시작: $(date)"
echo "========================================="

# 백업 디렉토리 생성
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo -e "${GREEN}✓${NC} 백업 디렉토리 생성: $BACKUP_DIR"
fi

# 데이터베이스 파일 확인
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}✗${NC} 에러: 데이터베이스 파일을 찾을 수 없습니다: $DB_PATH"
    exit 1
fi

# 데이터베이스 백업
BACKUP_FILE="$BACKUP_DIR/algoforge_$DATE.db"
cp "$DB_PATH" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓${NC} 백업 완료: algoforge_$DATE.db ($BACKUP_SIZE)"
else
    echo -e "${RED}✗${NC} 에러: 백업 실패"
    exit 1
fi

# 오래된 백업 삭제
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "algoforge_*.db" -mtime +$RETENTION_DAYS)
if [ -n "$OLD_BACKUPS" ]; then
    echo -e "${YELLOW}→${NC} 오래된 백업 삭제 중 (${RETENTION_DAYS}일 이상)..."
    find "$BACKUP_DIR" -name "algoforge_*.db" -mtime +$RETENTION_DAYS -delete
    echo -e "${GREEN}✓${NC} 오래된 백업 삭제 완료"
else
    echo -e "${GREEN}✓${NC} 삭제할 오래된 백업 없음"
fi

# 백업 목록 및 총 크기
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/algoforge_*.db 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
echo "========================================="
echo -e "백업 파일 수: ${GREEN}$BACKUP_COUNT${NC}"
echo -e "총 백업 크기: ${GREEN}$TOTAL_SIZE${NC}"
echo "========================================="
echo "백업 완료: $(date)"
echo ""

