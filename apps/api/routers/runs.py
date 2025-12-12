"""
Run API Router

Run 생성, 실행, 조회 엔드포인트를 제공합니다.
Background Task로 백테스트 엔진을 실행합니다.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import time
import traceback

from apps.api.db.database import get_database
from apps.api.db.repositories import (
    RunRepository,
    DatasetRepository,
    StrategyRepository,
    TradeRepository,
    TradeLegRepository,
    MetricsRepository
)
from apps.api.db.utils import load_bars_from_csv
from apps.api.schemas import (
    RunCreate,
    RunResponse,
    RunList,
    TradeResponse,
    TradeList,
    TradeLegResponse,
    MetricsResponse
)
from apps.api.utils.exceptions import RunNotFoundError, DatasetNotFoundError, StrategyNotFoundError

from engine.core.backtest_engine import BacktestEngine
from engine.core.metrics_calculator import MetricsCalculator

router = APIRouter()
logger = logging.getLogger(__name__)

# 엔진 버전
ENGINE_VERSION = "1.0.0"


def execute_backtest(run_id: int):
    """
    백테스트 실행 (Background Task)
    
    Args:
        run_id: Run ID
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        dataset_repo = DatasetRepository(db)
        strategy_repo = StrategyRepository(db)
        trade_repo = TradeRepository(db)
        trade_leg_repo = TradeLegRepository(db)
        metrics_repo = MetricsRepository(db)
        
        # Run 정보 조회
        run = run_repo.get_by_id(run_id)
        if not run:
            logger.error(f"Run {run_id} not found")
            return
        
        # 상태를 RUNNING으로 변경
        run_repo.update_status(
            run_id=run_id,
            status="RUNNING",
            started_at=int(time.time())
        )
        
        # Dataset 조회
        dataset = dataset_repo.get_by_id(run["dataset_id"])
        if not dataset:
            logger.error(f"Dataset {run['dataset_id']} not found")
            run_repo.update_status(
                run_id=run_id,
                status="FAILED",
                completed_at=int(time.time()),
                run_artifacts={"error": "Dataset not found"}
            )
            return
        
        # Strategy 조회
        strategy = strategy_repo.get_by_id(run["strategy_id"])
        if not strategy:
            logger.error(f"Strategy {run['strategy_id']} not found")
            run_repo.update_status(
                run_id=run_id,
                status="FAILED",
                completed_at=int(time.time()),
                run_artifacts={"error": "Strategy not found"}
            )
            return
        
        # CSV 파일 로드
        bars, _ = load_bars_from_csv(dataset["file_path"])
        
        # 전략 함수 생성 (단순화된 버전)
        # 실제로는 strategy definition을 파싱해서 신호 생성 로직을 만들어야 함
        # MVP에서는 테스트용 신호만 생성
        def strategy_func(bar):
            """
            전략 함수 (MVP: 테스트용)
            
            실제 구현에서는 strategy definition을 파싱하여
            규칙 기반 신호를 생성해야 합니다.
            """
            # TODO: strategy definition 파싱 및 신호 생성 로직 구현
            # 현재는 None 반환 (신호 없음)
            return None
        
        # 백테스트 엔진 실행
        engine = BacktestEngine(
            initial_balance=run["initial_balance"],
            strategy_func=strategy_func
        )
        
        trades = engine.run(bars)
        
        # Trades 및 TradeLeg 저장
        for trade in trades:
            # Trade 저장
            db_trade_id = trade_repo.create_from_trade(run_id, trade)
            
            # TradeLeg 저장
            for leg in trade.legs:
                trade_leg_repo.create_from_trade_leg(db_trade_id, leg)
        
        # Metrics 계산 및 저장
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        metrics_repo.create_from_metrics(run_id, metrics)
        
        # 상태를 COMPLETED로 변경
        run_repo.update_status(
            run_id=run_id,
            status="COMPLETED",
            completed_at=int(time.time()),
            run_artifacts={
                "warnings": engine.warnings,
                "trades_count": len(trades)
            }
        )
        
        logger.info(f"Backtest completed: run_id={run_id}, trades={len(trades)}")
        
    except Exception as e:
        logger.error(f"Backtest failed for run {run_id}: {str(e)}", exc_info=True)
        
        # 상태를 FAILED로 변경
        try:
            db = get_database()
            run_repo = RunRepository(db)
            run_repo.update_status(
                run_id=run_id,
                status="FAILED",
                completed_at=int(time.time()),
                run_artifacts={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
        except Exception as update_error:
            logger.error(f"Failed to update run status: {str(update_error)}", exc_info=True)


@router.post("", response_model=RunResponse, status_code=201)
async def create_run(run_create: RunCreate, background_tasks: BackgroundTasks):
    """
    Run 생성 및 실행 트리거
    
    Args:
        run_create: Run 생성 요청 데이터
        background_tasks: FastAPI Background Tasks
        
    Returns:
        RunResponse: 생성된 Run 정보
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        dataset_repo = DatasetRepository(db)
        strategy_repo = StrategyRepository(db)
        
        # Dataset 존재 확인
        dataset = dataset_repo.get_by_id(run_create.dataset_id)
        if not dataset:
            raise DatasetNotFoundError(run_create.dataset_id)
        
        # Strategy 존재 확인
        strategy = strategy_repo.get_by_id(run_create.strategy_id)
        if not strategy:
            raise StrategyNotFoundError(run_create.strategy_id)
        
        # Run 생성
        run_id = run_repo.create(
            dataset_id=run_create.dataset_id,
            strategy_id=run_create.strategy_id,
            engine_version=ENGINE_VERSION,
            initial_balance=run_create.initial_balance
        )
        
        # Background Task로 백테스트 실행
        background_tasks.add_task(execute_backtest, run_id)
        
        # 생성된 Run 조회
        run = run_repo.get_by_id(run_id)
        
        logger.info(f"Run created: ID={run_id}, dataset={run_create.dataset_id}, strategy={run_create.strategy_id}")
        
        return RunResponse(**run)
        
    except (DatasetNotFoundError, StrategyNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Failed to create run: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Run 생성 실패: {str(e)}")


@router.get("", response_model=RunList)
async def get_runs():
    """
    Run 목록 조회
    
    Returns:
        RunList: Run 목록
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        
        runs = run_repo.get_all()
        
        return RunList(
            runs=[RunResponse(**r) for r in runs],
            total=len(runs)
        )
        
    except Exception as e:
        logger.error(f"Failed to get runs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Run 목록 조회 실패: {str(e)}")


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: int):
    """
    Run 상세 조회
    
    Args:
        run_id: Run ID
        
    Returns:
        RunResponse: Run 정보
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        
        run = run_repo.get_by_id(run_id)
        
        if not run:
            raise RunNotFoundError(run_id)
        
        return RunResponse(**run)
        
    except RunNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Run 조회 실패: {str(e)}")


@router.get("/{run_id}/trades", response_model=TradeList)
async def get_run_trades(run_id: int):
    """
    Run의 거래 내역 조회
    
    Args:
        run_id: Run ID
        
    Returns:
        TradeList: 거래 목록
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        trade_repo = TradeRepository(db)
        trade_leg_repo = TradeLegRepository(db)
        
        # Run 존재 확인
        run = run_repo.get_by_id(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # Trades 조회
        trades = trade_repo.get_by_run(run_id)
        
        # 각 Trade의 Legs 조회
        trade_responses = []
        for trade in trades:
            legs = trade_leg_repo.get_by_trade(trade["trade_id"])
            
            trade_response = TradeResponse(
                **trade,
                legs=[TradeLegResponse(**leg) for leg in legs]
            )
            trade_responses.append(trade_response)
        
        return TradeList(
            trades=trade_responses,
            total=len(trades)
        )
        
    except RunNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get trades for run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"거래 내역 조회 실패: {str(e)}")


@router.get("/{run_id}/metrics", response_model=MetricsResponse)
async def get_run_metrics(run_id: int):
    """
    Run의 Metrics 조회
    
    Args:
        run_id: Run ID
        
    Returns:
        MetricsResponse: Metrics 정보
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        metrics_repo = MetricsRepository(db)
        
        # Run 존재 확인
        run = run_repo.get_by_id(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # Metrics 조회
        metrics = metrics_repo.get_by_run(run_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Run {run_id}의 Metrics를 찾을 수 없습니다")
        
        return MetricsResponse(**metrics)
        
    except RunNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Metrics 조회 실패: {str(e)}")


@router.delete("/{run_id}", status_code=204)
async def delete_run(run_id: int):
    """
    Run 삭제
    
    Args:
        run_id: Run ID
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        
        # Run 조회
        run = run_repo.get_by_id(run_id)
        
        if not run:
            raise RunNotFoundError(run_id)
        
        # 데이터베이스에서 삭제 (Cascade로 관련 데이터도 삭제됨)
        run_repo.delete(run_id)
        
        logger.info(f"Run deleted: ID={run_id}")
        
        return None
        
    except RunNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Run 삭제 실패: {str(e)}")

