"""
Strategy API Router

전략 등록, 조회, 삭제 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException
import logging

from apps.api.db.database import get_database
from apps.api.db.repositories import StrategyRepository, RunRepository
from apps.api.db.utils import calculate_strategy_hash
from apps.api.schemas import StrategyCreate, StrategyResponse, StrategyList
from apps.api.utils.exceptions import StrategyNotFoundError, InvalidDataError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=StrategyResponse, status_code=201)
async def create_strategy(strategy: StrategyCreate):
    """
    전략 등록
    
    Args:
        strategy: 전략 생성 요청 데이터
        
    Returns:
        StrategyResponse: 생성된 전략 정보
    """
    try:
        # 전략 정의 검증
        if not strategy.definition:
            raise InvalidDataError("전략 정의가 비어있습니다")
        
        # 해시 계산
        strategy_hash = calculate_strategy_hash(strategy.definition)
        
        # 데이터베이스 저장
        db = get_database()
        repo = StrategyRepository(db)
        
        # 전략 생성 (중복 허용)
        strategy_id = repo.create(
            name=strategy.name,
            strategy_hash=strategy_hash,
            definition=strategy.definition,
            description=strategy.description
        )
        
        # 생성된 전략 조회
        created_strategy = repo.get_by_id(strategy_id)
        
        logger.info(f"Strategy created: ID={strategy_id}, name={strategy.name}, hash={strategy_hash}")
        
        return StrategyResponse(**created_strategy)
        
    except InvalidDataError:
        raise
    except Exception as e:
        logger.error(f"Failed to create strategy: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"전략 생성 실패: {str(e)}")


@router.get("", response_model=StrategyList)
async def get_strategies():
    """
    전략 목록 조회
    
    Returns:
        StrategyList: 전략 목록
    """
    try:
        db = get_database()
        repo = StrategyRepository(db)
        
        strategies = repo.get_all()
        
        return StrategyList(
            strategies=[StrategyResponse(**s) for s in strategies],
            total=len(strategies)
        )
        
    except Exception as e:
        logger.error(f"Failed to get strategies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"전략 목록 조회 실패: {str(e)}")


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int):
    """
    전략 상세 조회
    
    Args:
        strategy_id: 전략 ID
        
    Returns:
        StrategyResponse: 전략 정보
    """
    try:
        db = get_database()
        repo = StrategyRepository(db)
        
        strategy = repo.get_by_id(strategy_id)
        
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        
        return StrategyResponse(**strategy)
        
    except StrategyNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy {strategy_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"전략 조회 실패: {str(e)}")


@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(strategy_id: int):
    """
    전략 삭제
    
    Args:
        strategy_id: 전략 ID
        
    Raises:
        HTTPException 409: 해당 전략으로 생성된 Run이 존재하는 경우
    """
    try:
        db = get_database()
        strategy_repo = StrategyRepository(db)
        run_repo = RunRepository(db)
        
        # 전략 조회
        strategy = strategy_repo.get_by_id(strategy_id)
        
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        
        # 연관된 Run 개수 확인
        related_runs = run_repo.get_by_strategy(strategy_id)
        
        if related_runs:
            # Run이 존재하면 삭제 차단
            run_count = len(related_runs)
            error_message = f"이 전략으로 생성된 Run이 {run_count}개 존재합니다. 전략을 삭제하려면 먼저 관련 Run을 삭제해주세요."
            
            logger.warning(f"Strategy deletion blocked: ID={strategy_id}, related_runs={run_count}")
            
            raise HTTPException(
                status_code=409,
                detail={
                    "message": error_message,
                    "strategy_id": strategy_id,
                    "related_runs_count": run_count
                }
            )
        
        # 데이터베이스에서 삭제
        strategy_repo.delete(strategy_id)
        
        logger.info(f"Strategy deleted: ID={strategy_id}")
        
        return None
        
    except StrategyNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete strategy {strategy_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"전략 삭제 실패: {str(e)}")

