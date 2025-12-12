# AlgoForge Web Frontend

AlgoForge의 Next.js 기반 웹 프론트엔드입니다.

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **UI Library**: ShadCN UI
- **Styling**: TailwindCSS
- **Package Manager**: pnpm
- **Language**: TypeScript

## 시작하기

### 1. 의존성 설치

```bash
pnpm install
```

### 2. 개발 서버 실행

```bash
pnpm dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

### 3. 백엔드 서버 실행 (필수)

프론트엔드가 작동하려면 FastAPI 백엔드가 실행 중이어야 합니다.

```bash
# 프로젝트 루트에서
cd apps/api
uvicorn main:app --reload --port 8000
```

## 프로젝트 구조

```
apps/web/
├─ app/                  # Next.js App Router 페이지
│  ├─ page.tsx          # 대시보드
│  ├─ datasets/         # 데이터셋 관리
│  ├─ strategies/       # 전략 관리
│  └─ runs/             # Run 목록 및 상세
├─ components/          # React 컴포넌트
│  ├─ ui/              # ShadCN UI 컴포넌트
│  └─ layout/          # 레이아웃 컴포넌트
├─ lib/                 # 유틸리티 및 API 클라이언트
│  ├─ types.ts         # TypeScript 타입 정의
│  ├─ api-client.ts    # API 클라이언트
│  └─ utils.ts         # 유틸리티 함수
└─ public/              # 정적 파일

## 주요 페이지

### 대시보드 (`/`)
- 전체 통계 개요
- 빠른 액션
- 시작 가이드

### 데이터셋 (`/datasets`)
- 데이터셋 목록
- CSV 파일 업로드
- 데이터셋 삭제

### 전략 (`/strategies`)
- 전략 목록
- 전략 생성 (JSON 정의)
- 전략 삭제

### Run (`/runs`)
- Run 목록
- Run 생성 및 실행
- Run 상세 보기 (`/runs/[id]`)
  - Run 정보
  - 성과 지표 (Metrics)
  - 거래 내역 (Trades)

## API 통신

FastAPI 백엔드와 통신합니다:
- **개발**: `http://localhost:8000`
- **프록시**: Next.js의 rewrites 기능 사용

### API 클라이언트 사용 예시

```typescript
import { datasetApi, strategyApi, runApi } from '@/lib/api-client'

// 데이터셋 목록 조회
const datasets = await datasetApi.list()

// 전략 생성
const strategy = await strategyApi.create({
  name: "My Strategy",
  definition: { /* ... */ }
})

// Run 생성
const run = await runApi.create({
  dataset_id: 1,
  strategy_id: 1
})
```

## 스타일 가이드

### UI 컴포넌트
ShadCN 컴포넌트를 우선적으로 사용합니다.

```tsx
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

<Button variant="default">생성하기</Button>
<Button variant="outline">취소</Button>
<Button variant="destructive">삭제</Button>
```

### 색상 시스템
- **Primary**: 주요 액션 (파란색)
- **Success**: 수익, 성공 (초록색)
- **Destructive**: 손실, 삭제 (빨간색)
- **Muted**: 보조 정보 (회색)

### 유틸리티 함수

```typescript
import { formatCurrency, formatPercent, formatTimestamp } from '@/lib/utils'

formatCurrency(10000)     // "$10,000"
formatPercent(15.234)     // "+15.23%"
formatTimestamp(1704067200) // "2024-01-01 12:00:00"
```

## 빌드

```bash
# 프로덕션 빌드
pnpm build

# 프로덕션 서버 실행
pnpm start
```

## 환경 변수

`.env.local` 파일 생성:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 주의사항

1. **백엔드 필수**: 프론트엔드는 FastAPI 백엔드 없이 작동하지 않습니다.
2. **pnpm 사용**: npm이나 yarn 대신 pnpm을 사용하세요.
3. **타입 안전성**: TypeScript 타입 에러는 반드시 수정하세요.

## 향후 개선 사항

- [ ] 차트 통합 (TradingView Lightweight Charts)
- [ ] 전략 빌더 UI
- [ ] 다크 모드 토글
- [ ] 실시간 Run 상태 업데이트 (폴링 또는 WebSocket)
- [ ] 에러 토스트 알림
- [ ] 로딩 스피너 개선

## 문의

프로젝트 관련 문의는 이슈를 생성해주세요.

