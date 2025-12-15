"""
AlgoForge FastAPI 메인 애플리케이션

백테스트 엔진과 데이터베이스를 연결하는 RESTful API를 제공합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from apps.api.routers import datasets, strategies, runs, indicators, presets
from apps.api.utils.exceptions import AlgoForgeException
from apps.api.utils.responses import error_response
from apps.api.db.database import get_database

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="AlgoForge API",
    version="1.0.0",
    description="백테스트 엔진 API - 전략 개발·비교·개선 목적의 백테스팅 도구",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False  # trailing slash 자동 리다이렉트 비활성화 (CORS 문제 방지)
)


@app.on_event("startup")
async def startup_event():
    """
    API 서버 시작 시 초기화 작업
    - 데이터베이스 초기화
    - 필요한 디렉토리 생성
    """
    logger.info("Initializing AlgoForge API...")
    
    # 데이터베이스 초기화
    try:
        db = get_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # datasets 디렉토리 생성
    datasets_dir = Path("datasets")
    datasets_dir.mkdir(exist_ok=True)
    logger.info(f"Datasets directory ready: {datasets_dir.absolute()}")
    
    logger.info("AlgoForge API initialization completed")

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5001",  # Next.js 개발 서버
        "http://127.0.0.1:5001",
        "http://algoforge.wonbbo.kro.kr",  # 프로덕션 서버
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 글로벌 예외 핸들러
@app.exception_handler(AlgoForgeException)
async def algoforge_exception_handler(request: Request, exc: AlgoForgeException):
    """AlgoForge 커스텀 예외 처리"""
    logger.error(f"AlgoForge Exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Internal server error",
            status_code=500,
            details={"error": str(exc)}
        )
    )


# 라우터 등록
app.include_router(
    datasets.router,
    prefix="/api/datasets",
    tags=["datasets"]
)

app.include_router(
    strategies.router,
    prefix="/api/strategies",
    tags=["strategies"]
)

app.include_router(
    runs.router,
    prefix="/api/runs",
    tags=["runs"]
)

app.include_router(
    indicators.router,
    prefix="/api/indicators",
    tags=["indicators"]
)

app.include_router(
    presets.router,
    prefix="/api/presets",
    tags=["presets"]
)


# 루트 엔드포인트
@app.get("/")
def root():
    """
    API 루트 엔드포인트
    
    Returns:
        dict: API 정보
    """
    return {
        "name": "AlgoForge API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# 헬스 체크
@app.get("/health")
def health_check():
    """
    헬스 체크 엔드포인트
    
    Returns:
        dict: 서버 상태
    """
    from apps.api.db.database import get_database
    
    try:
        # 데이터베이스 연결 테스트
        db = get_database()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM datasets")
            dataset_count = cursor.fetchone()[0]
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "datasets_count": dataset_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": "1.0.0",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=6000,
        reload=True
    )

