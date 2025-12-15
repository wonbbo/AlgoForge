"""
Run API Router

Run 생성, 실행, 조회 엔드포인트를 제공합니다.
Background Task로 백테스트 엔진을 실행합니다.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import time
import traceback
import json
import os
from pathlib import Path

from apps.api.db.database import get_database
from apps.api.db.repositories import (
    RunRepository,
    DatasetRepository,
    StrategyRepository,
    TradeRepository,
    TradeLegRepository,
    MetricsRepository,
    PresetRepository
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
from apps.api.schemas.trade import ChartDataResponse, BarData
from apps.api.utils.exceptions import RunNotFoundError, DatasetNotFoundError, StrategyNotFoundError, CancellationRequested

from engine.core.backtest_engine import BacktestEngine
from engine.core.metrics_calculator import MetricsCalculator
from engine.utils.strategy_parser import StrategyParser

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
        preset_repo = PresetRepository(db)
        
        # Run 정보 조회
        run = run_repo.get_by_id(run_id)
        if not run:
            logger.error(f"Run {run_id} not found")
            return
        
        # 프리셋 정보 조회 (preset_id가 있으면)
        preset = None
        if run.get('preset_id'):
            preset = preset_repo.get_by_id(run['preset_id'])
            if not preset:
                logger.warning(f"Preset {run['preset_id']} not found, using default")
                preset = preset_repo.get_default()
        else:
            # preset_id가 없으면 기본 프리셋 사용
            preset = preset_repo.get_default()
        
        # 프리셋이 없으면 기본값 사용 (하드코딩)
        if not preset:
            logger.warning("No preset found, using hardcoded defaults")
            preset = {
                'risk_percent': 0.02,
                'risk_reward_ratio': 1.5,
                'rebalance_interval': 50
            }
        
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
        
        # CSV 파일 로드 (DataFrame 포함)
        bars, df, _ = load_bars_from_csv(dataset["file_path"])
        
        # 전략 파서 생성 및 전략 함수 생성
        try:
            strategy_parser = StrategyParser(
                strategy_definition=strategy["definition"],
                bars=bars,
                df=df
            )
            strategy_func = strategy_parser.create_strategy_function()
            
        except Exception as e:
            logger.error(f"전략 파서 생성 실패: {str(e)}", exc_info=True)
            run_repo.update_status(
                run_id=run_id,
                status="FAILED",
                completed_at=int(time.time()),
                run_artifacts={
                    "error": f"전략 파서 생성 실패: {str(e)}",
                    "traceback": traceback.format_exc()
                }
            )
            return
        
        # 진행률 콜백 함수 정의
        def progress_callback(processed: int, total: int):
            """
            진행률 업데이트 및 중지 체크 콜백
            
            Args:
                processed: 처리된 봉 개수
                total: 전체 봉 개수
            
            Raises:
                CancellationRequested: Run이 중지된 경우
            """
            try:
                # 현재 Run 상태 확인 (중지 체크)
                current_run = run_repo.get_by_id(run_id)
                if current_run and current_run["status"] == "CANCELLED":
                    # 중지 요청이 있으면 예외 발생
                    logger.info(f"Cancellation detected for run {run_id}")
                    raise CancellationRequested(run_id)
                
                # 진행률 업데이트
                run_repo.update_progress(run_id, processed, total)
                logger.debug(f"Progress updated: {run_id} - {processed}/{total} ({processed/total*100:.1f}%)")
            except CancellationRequested:
                # 중지 예외는 다시 던짐
                raise
            except Exception as e:
                logger.error(f"진행률 업데이트 실패: {str(e)}")
        
        # 백테스트 엔진 실행 (DB 연결 전달하여 레버리지 데이터 로드)
        engine = BacktestEngine(
            initial_balance=run["initial_balance"],
            strategy_func=strategy_func,
            progress_callback=progress_callback,
            db_conn=db,  # DB 연결 전달
            risk_percent=preset['risk_percent'],
            risk_reward_ratio=preset['risk_reward_ratio'],
            rebalance_interval=preset['rebalance_interval']
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
        
    except CancellationRequested:
        # 중지 요청 처리 - 이미 CANCELLED 상태이므로 추가 작업 불필요
        logger.info(f"Backtest cancelled: run_id={run_id}")
        return
        
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
        preset_repo = PresetRepository(db)
        
        # Dataset 존재 확인
        dataset = dataset_repo.get_by_id(run_create.dataset_id)
        if not dataset:
            raise DatasetNotFoundError(run_create.dataset_id)
        
        # Strategy 존재 확인
        strategy = strategy_repo.get_by_id(run_create.strategy_id)
        if not strategy:
            raise StrategyNotFoundError(run_create.strategy_id)
        
        # Preset 확인 및 처리
        preset_id = run_create.preset_id
        if preset_id is not None:
            # 지정된 프리셋이 있는지 확인
            preset = preset_repo.get_by_id(preset_id)
            if not preset:
                raise HTTPException(
                    status_code=404,
                    detail=f"Preset {preset_id}를 찾을 수 없습니다"
                )
        else:
            # 기본 프리셋 사용
            preset = preset_repo.get_default()
            if preset:
                preset_id = preset['preset_id']
            else:
                # 기본 프리셋이 없으면 None으로 유지 (하드코딩 값 사용)
                logger.warning("No default preset found, will use hardcoded defaults")
        
        # 프리셋에서 initial_balance 가져오기
        initial_balance = preset['initial_balance'] if preset else 1000.0
        
        # Run 생성
        run_id = run_repo.create(
            dataset_id=run_create.dataset_id,
            strategy_id=run_create.strategy_id,
            engine_version=ENGINE_VERSION,
            initial_balance=initial_balance,
            preset_id=preset_id
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


@router.post("/{run_id}/rerun", response_model=RunResponse)
async def rerun_run(run_id: int, background_tasks: BackgroundTasks):
    """
    Run 재실행 (동일한 Run을 다시 실행)
    
    Args:
        run_id: Run ID
        background_tasks: FastAPI Background Tasks
        
    Returns:
        RunResponse: 재실행될 Run 정보
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        
        # Run 존재 확인
        run = run_repo.get_by_id(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # Run이 실행 중인 경우 에러 처리
        if run["status"] == "RUNNING":
            raise HTTPException(
                status_code=400, 
                detail=f"Run {run_id}가 현재 실행 중입니다. 실행이 완료된 후 재실행하세요."
            )
        
        # Run 결과 데이터 삭제 및 상태 초기화
        run_repo.reset_for_rerun(run_id)
        
        # Background Task로 백테스트 실행
        background_tasks.add_task(execute_backtest, run_id)
        
        # 초기화된 Run 조회
        run = run_repo.get_by_id(run_id)
        
        logger.info(f"Run rerun triggered: ID={run_id}")
        
        return RunResponse(**run)
        
    except RunNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rerun run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Run 재실행 실패: {str(e)}")


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(run_id: int):
    """
    Run 중지
    
    Args:
        run_id: Run ID
        
    Returns:
        RunResponse: 중지된 Run 정보
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        
        # Run 존재 확인
        run = run_repo.get_by_id(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # RUNNING 상태가 아니면 중지 불가
        if run["status"] != "RUNNING":
            raise HTTPException(
                status_code=400,
                detail=f"Run {run_id}는 실행 중이 아닙니다. 현재 상태: {run['status']}"
            )
        
        # 상태를 CANCELLED로 변경
        run_repo.update_status(
            run_id=run_id,
            status="CANCELLED",
            completed_at=int(time.time()),
            run_artifacts={
                "cancelled_by_user": True,
                "message": "사용자가 실행을 중지했습니다."
            }
        )
        
        # 중지된 Run 조회
        run = run_repo.get_by_id(run_id)
        
        logger.info(f"Run cancelled by user: ID={run_id}")
        
        return RunResponse(**run)
        
    except RunNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Run 중지 실패: {str(e)}")


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


@router.get("/{run_id}/trades/{trade_id}/chart-data", response_model=ChartDataResponse)
async def get_trade_chart_data(run_id: int, trade_id: int):
    """
    Trade의 차트 데이터 조회
    
    거래 기간 전후로 각 10개의 봉 데이터와 지표 값을 반환합니다.
    
    Args:
        run_id: Run ID
        trade_id: Trade ID
        
    Returns:
        ChartDataResponse: 차트 데이터 (봉, 지표, 거래 정보)
    """
    try:
        db = get_database()
        run_repo = RunRepository(db)
        trade_repo = TradeRepository(db)
        trade_leg_repo = TradeLegRepository(db)
        dataset_repo = DatasetRepository(db)
        strategy_repo = StrategyRepository(db)
        
        # Run 존재 확인
        run = run_repo.get_by_id(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # Trade 조회
        trade = trade_repo.get_by_id(trade_id)
        if not trade or trade["run_id"] != run_id:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id}를 찾을 수 없습니다")
        
        # Trade Legs 조회
        legs = trade_leg_repo.get_by_trade(trade_id)
        if not legs:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id}의 Leg를 찾을 수 없습니다")
        
        # 마지막 청산 시간 찾기
        last_exit_timestamp = max(leg["exit_timestamp"] for leg in legs)
        
        # Dataset 및 Strategy 조회
        dataset = dataset_repo.get_by_id(run["dataset_id"])
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {run['dataset_id']}를 찾을 수 없습니다")
        
        strategy = strategy_repo.get_by_id(run["strategy_id"])
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {run['strategy_id']}를 찾을 수 없습니다")
        
        # CSV 파일 로드
        bars, df, _ = load_bars_from_csv(dataset["file_path"])
        
        # 전략 파서 생성 (지표 계산)
        strategy_parser = StrategyParser(
            strategy_definition=strategy["definition"],
            bars=bars,
            df=df
        )
        
        # 진입 및 청산 시점의 인덱스 찾기
        entry_idx = None
        exit_idx = None
        
        for i, bar in enumerate(bars):
            if bar.timestamp == trade["entry_timestamp"]:
                entry_idx = i
            if bar.timestamp == last_exit_timestamp:
                exit_idx = i
        
        if entry_idx is None or exit_idx is None:
            raise HTTPException(
                status_code=404, 
                detail="거래 시점의 봉 데이터를 찾을 수 없습니다"
            )
        
        # 차트 범위 계산: 진입 앞 10개 + 거래 기간 + 청산 뒤 10개
        start_idx = max(0, entry_idx - 10)
        end_idx = min(len(bars) - 1, exit_idx + 10)
        
        # 봉 데이터 추출
        chart_bars = []
        for i in range(start_idx, end_idx + 1):
            bar = bars[i]
            chart_bars.append(BarData(
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume
            ))
        
        # 지표 타입 분류 함수
        def classify_indicator_display_type(indicator_type: str) -> str:
            """
            지표의 표시 위치를 결정합니다.
            
            Args:
                indicator_type: 지표 타입 (ema, sma, rsi, atr 등)
                
            Returns:
                str: "overlay" (가격 차트와 함께) 또는 "oscillator" (하단 별도 차트)
            """
            # Oscillator 타입: 독립적인 값 범위를 가지는 지표들
            oscillator_types = {
                "rsi",      # RSI (0-100)
                "atr",      # ATR (독립적인 변동성 값)
                "macd",     # MACD (독립적인 모멘텀 값)
                "stoch",    # Stochastic (0-100)
                "cci",      # Commodity Channel Index
                "mfi",      # Money Flow Index (0-100)
                "roc",      # Rate of Change
                "willr",    # Williams %R (-100~0)
            }
            
            if indicator_type.lower() in oscillator_types:
                return "oscillator"
            
            # Overlay 타입: 가격과 함께 표시되는 지표들
            # EMA, SMA, BB (Bollinger Bands), VWAP 등
            return "overlay"
        
        # 지표 데이터 추출
        indicators_data = {}
        indicator_types = {}
        
        # 지표 메타 정보 로드 (output_fields 확인용)
        indicators_metadata = {}
        try:
            with db.get_connection() as conn:
                cursor = conn.execute("SELECT type, output_fields FROM indicators")
                for row in cursor.fetchall():
                    indicators_metadata[row[0]] = json.loads(row[1])
        except Exception as e:
            logger.warning(f"지표 메타 정보 로드 실패: {e}")
        
        strategy_indicators = strategy["definition"].get("indicators", [])
        for indicator in strategy_indicators:
            indicator_id = indicator.get("id")
            indicator_type = indicator.get("type", "").lower()
            
            if not indicator_id:
                continue
            
            # 지표의 output_fields 확인
            output_fields = indicators_metadata.get(indicator_type, ["main"])
            
            # 각 output_field별로 데이터 추출
            for field in output_fields:
                # 컬럼명 생성: main이면 indicator_id, 아니면 indicator_id_field
                if len(output_fields) == 1 and field == "main":
                    column_name = indicator_id
                    display_key = indicator_id
                else:
                    column_name = f"{indicator_id}_{field}"
                    display_key = f"{indicator_id}.{field}"
                
                # 지표 값 추출
                try:
                    indicator_values = []
                    for i in range(start_idx, end_idx + 1):
                        value = strategy_parser.indicator_calc.get_value(column_name, i)
                        indicator_values.append(value)
                    
                    indicators_data[display_key] = indicator_values
                    
                    # 지표 타입 분류 (각 필드마다)
                    indicator_types[display_key] = classify_indicator_display_type(indicator_type)
                        
                except Exception as e:
                    logger.warning(f"지표 {display_key} (컬럼: {column_name}) 값 추출 실패: {e}")
        
        # 거래 정보
        trade_info = {
            "entry_timestamp": trade["entry_timestamp"],
            "entry_price": trade["entry_price"],
            "direction": trade["direction"],
            "stop_loss": trade["stop_loss"],
            "take_profit_1": trade["take_profit_1"],
            "legs": [
                {
                    "exit_timestamp": leg["exit_timestamp"],
                    "exit_price": leg["exit_price"],
                    "exit_type": leg["exit_type"],
                    "qty_ratio": leg["qty_ratio"]
                }
                for leg in legs
            ]
        }
        
        return ChartDataResponse(
            bars=chart_bars,
            indicators=indicators_data,
            indicator_types=indicator_types,
            trade_info=trade_info
        )
        
    except RunNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chart data for trade {trade_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"차트 데이터 조회 실패: {str(e)}")

