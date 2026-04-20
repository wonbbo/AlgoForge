"""
Dataset API Router

데이터셋 업로드, 조회, 삭제 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import os
import time
import uuid
from pathlib import Path

from apps.api.db.database import get_database
from apps.api.db.repositories import DatasetRepository
from apps.api.db.utils import load_bars_from_csv, calculate_dataset_hash, validate_bars
from apps.api.schemas import DatasetCreate, DatasetResponse, DatasetList
from apps.api.schemas.dataset import BinanceFetchRequest
from apps.api.utils.exceptions import DatasetNotFoundError, InvalidDataError, DuplicateDataError
from engine.data.binance.merger import fetch_binance_to_csv

router = APIRouter()
logger = logging.getLogger(__name__)

# 데이터셋 파일 저장 디렉토리
DATASET_DIR = Path("datasets")
DATASET_DIR.mkdir(exist_ok=True)

# 바이낸스 아카이브 ZIP 캐시
BINANCE_CACHE_DIR = Path("datasets/.binance_cache")
BINANCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 바이낸스 fetch 작업 상태 (in-memory)
# job_id -> {"status": "PENDING|RUNNING|COMPLETED|FAILED", "dataset_id": int?, "error": str?, "started_at": int, ...}
_BINANCE_JOBS: Dict[str, Dict[str, Any]] = {}

_KST = ZoneInfo("Asia/Seoul")


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    file: UploadFile = File(..., description="CSV 파일 (dt,do,dh,dl,dc,dv,dd)"),
    name: str = Form(..., description="데이터셋 이름"),
    description: Optional[str] = Form(None, description="데이터셋 설명"),
    timeframe: str = Form(default="5m", description="타임프레임")
):
    """
    데이터셋 업로드 및 등록
    
    CSV 파일 형식:
    - dt: KST(Asia/Seoul) 'YYYY-MM-DD HH:MM:SS' (예: '2024-05-31 09:00:00')
    - do: 시가 (open)
    - dh: 고가 (high)
    - dl: 저가 (low)
    - dc: 종가 (close)
    - dv: 거래량 (volume)
    - dd: 봉 방향 (1=상승, -1=하락, 0=보합)
    
    Note:
        dt는 KST로 해석되어 UNIX timestamp(초)로 저장됩니다 (docs/timezone.md).
    
    Returns:
        DatasetResponse: 생성된 데이터셋 정보
    """
    try:
        logger.info(f"Received dataset upload request: name={name}, filename={file.filename}")
        
        # CSV 파일 확인
        if not file.filename:
            raise InvalidDataError("파일명이 없습니다")
        
        if not file.filename.endswith('.csv'):
            raise InvalidDataError("CSV 파일만 업로드 가능합니다", {"filename": file.filename})
        
        # 임시 파일로 저장
        temp_file_path = DATASET_DIR / f"temp_{int(time.time())}_{file.filename}"
        logger.info(f"Saving file to: {temp_file_path}")
        
        # 파일 저장
        contents = await file.read()
        if len(contents) == 0:
            raise InvalidDataError("업로드된 파일이 비어있습니다")
        
        logger.info(f"File size: {len(contents)} bytes")
        
        with open(temp_file_path, "wb") as f:
            f.write(contents)
        
        # CSV 파일 로드 및 검증
        try:
            # DF 반환이 필요하므로 include_df=True
            bars, df, metadata = load_bars_from_csv(str(temp_file_path), include_df=True)
        except Exception as e:
            # 임시 파일 삭제
            temp_file_path.unlink()
            raise InvalidDataError(f"CSV 파일 로드 실패: {str(e)}")
        
        # 봉 데이터 검증
        is_valid, errors = validate_bars(bars)
        if not is_valid:
            # 임시 파일 삭제
            temp_file_path.unlink()
            raise InvalidDataError(
                "봉 데이터 검증 실패",
                {"errors": errors}
            )
        
        # 해시 계산
        dataset_hash = calculate_dataset_hash(bars)
        
        # 데이터베이스 저장
        db = get_database()
        repo = DatasetRepository(db)
        
        # 중복 체크
        existing = repo.get_by_hash(dataset_hash)
        if existing:
            # 임시 파일 삭제
            temp_file_path.unlink()
            raise DuplicateDataError(
                "동일한 데이터셋이 이미 존재합니다",
                {"existing_dataset_id": existing["dataset_id"]}
            )
        
        # 최종 파일명 결정
        final_file_path = DATASET_DIR / f"{dataset_hash}.csv"
        
        # 파일 이동
        temp_file_path.rename(final_file_path)
        
        # 데이터베이스에 저장
        dataset_id = repo.create(
            name=name,
            dataset_hash=dataset_hash,
            file_path=str(final_file_path),
            bars_count=metadata["bars_count"],
            start_timestamp=metadata["start_timestamp"],
            end_timestamp=metadata["end_timestamp"],
            description=description,
            timeframe=timeframe
        )
        
        # 생성된 데이터셋 조회
        dataset = repo.get_by_id(dataset_id)
        
        logger.info(f"Dataset created: ID={dataset_id}, name={name}, hash={dataset_hash}")
        
        return DatasetResponse(**dataset)
        
    except (InvalidDataError, DuplicateDataError):
        raise
    except Exception as e:
        logger.error(f"Failed to create dataset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"데이터셋 생성 실패: {str(e)}")


@router.get("", response_model=DatasetList)
async def get_datasets():
    """
    데이터셋 목록 조회
    
    Returns:
        DatasetList: 데이터셋 목록
    """
    try:
        db = get_database()
        repo = DatasetRepository(db)
        
        datasets = repo.get_all()
        
        return DatasetList(
            datasets=[DatasetResponse(**d) for d in datasets],
            total=len(datasets)
        )
        
    except Exception as e:
        logger.error(f"Failed to get datasets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"데이터셋 목록 조회 실패: {str(e)}")


def _safe_download_filename(name: str, dataset_id: int) -> str:
    """브라우저 다운로드용 파일명 (경로·특수문자 제거)."""
    safe = "".join(c if c.isalnum() or c in ("-", "_", ".", " ") else "_" for c in (name or "dataset"))
    safe = safe.strip() or f"dataset_{dataset_id}"
    if not safe.lower().endswith(".csv"):
        safe = f"{safe}.csv"
    return safe


@router.get("/{dataset_id}/download")
async def download_dataset_csv(dataset_id: int):
    """
    데이터셋 원본 CSV 파일 다운로드.

    file_path는 프로젝트 datasets/ 디렉터리 하위만 허용합니다.
    """
    try:
        db = get_database()
        repo = DatasetRepository(db)
        dataset = repo.get_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(dataset_id)

        file_path = Path(dataset["file_path"]).resolve()
        datasets_root = DATASET_DIR.resolve()
        try:
            file_path.relative_to(datasets_root)
        except ValueError:
            logger.warning("Download rejected: path outside datasets dir: %s", file_path)
            raise HTTPException(status_code=403, detail="허용되지 않은 파일 경로입니다")

        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="CSV 파일을 찾을 수 없습니다")

        download_name = _safe_download_filename(dataset.get("name") or "", dataset_id)

        return FileResponse(
            path=str(file_path),
            media_type="text/csv; charset=utf-8",
            filename=download_name,
            headers={"Cache-Control": "no-store"},
        )
    except DatasetNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download dataset %s: %s", dataset_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int):
    """
    데이터셋 상세 조회
    
    Args:
        dataset_id: 데이터셋 ID
        
    Returns:
        DatasetResponse: 데이터셋 정보
    """
    try:
        db = get_database()
        repo = DatasetRepository(db)
        
        dataset = repo.get_by_id(dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        
        return DatasetResponse(**dataset)
        
    except DatasetNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"데이터셋 조회 실패: {str(e)}")


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: int):
    """
    데이터셋 삭제
    
    Args:
        dataset_id: 데이터셋 ID
    """
    try:
        db = get_database()
        repo = DatasetRepository(db)
        
        # 데이터셋 조회
        dataset = repo.get_by_id(dataset_id)
        
        if not dataset:
            raise DatasetNotFoundError(dataset_id)
        
        # 파일 삭제
        file_path = Path(dataset["file_path"])
        if file_path.exists():
            file_path.unlink()
        
        # 데이터베이스에서 삭제
        repo.delete(dataset_id)
        
        logger.info(f"Dataset deleted: ID={dataset_id}")
        
        return None
        
    except DatasetNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"데이터셋 삭제 실패: {str(e)}")


# ---------------------------------------------------------------------------
# 바이낸스 자동 수집
# ---------------------------------------------------------------------------

def _parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _run_binance_fetch_job(
    job_id: str,
    req: BinanceFetchRequest,
) -> None:
    """백그라운드에서 바이낸스 데이터를 수집해 dataset으로 등록."""
    job = _BINANCE_JOBS[job_id]
    job["status"] = "RUNNING"
    job["progress_message"] = "준비 중..."
    temp_file_path: Optional[Path] = None
    try:
        start_d = _parse_date(req.start_date)
        end_d = _parse_date(req.end_date)
        if start_d > end_d:
            raise ValueError(f"start_date > end_date: {start_d} > {end_d}")

        # 임시 CSV 경로 (해시 확정 후 최종 이름으로 이동)
        temp_file_path = DATASET_DIR / f"temp_binance_{int(time.time())}_{job_id}.csv"

        logger.info(
            f"[job {job_id}] 바이낸스 수집 시작: "
            f"{req.symbol} {req.market_type} {req.timeframe} {start_d}~{end_d}"
        )
        job["progress_message"] = (
            f"바이낸스에서 봉 다운로드 중 "
            f"({req.symbol} {req.timeframe} {req.start_date}~{req.end_date})..."
        )
        rows = fetch_binance_to_csv(
            symbol=req.symbol,
            market_type=req.market_type,
            interval=req.timeframe,
            start_date=start_d,
            end_date=end_d,
            out_path=temp_file_path,
            cache_dir=BINANCE_CACHE_DIR,
        )
        if rows == 0:
            raise ValueError("수집된 봉이 0개입니다. 기간/심볼을 확인하세요.")

        # 기존 업로드 파이프라인과 동일하게 검증·해시 계산
        job["progress_message"] = f"봉 데이터 검증 중 ({rows:,}개)..."
        bars, df, metadata = load_bars_from_csv(str(temp_file_path), include_df=True)
        is_valid, errors = validate_bars(bars)
        if not is_valid:
            raise ValueError(f"봉 데이터 검증 실패: {errors}")

        job["progress_message"] = "데이터셋 해시 계산 중..."
        dataset_hash = calculate_dataset_hash(bars)

        db = get_database()
        repo = DatasetRepository(db)
        existing = repo.get_by_hash(dataset_hash)
        if existing:
            # 동일 데이터가 이미 있으면 임시 파일만 정리 후 기존 dataset_id 반환
            temp_file_path.unlink(missing_ok=True)
            job["status"] = "COMPLETED"
            job["dataset_id"] = existing["dataset_id"]
            job["bars_count"] = metadata["bars_count"]
            job["progress_message"] = "동일 해시 데이터셋이 이미 존재 — 기존 것 재사용"
            job["note"] = "동일 해시 데이터셋이 이미 존재함 — 기존 dataset_id 재사용"
            return

        job["progress_message"] = "데이터셋 저장 중..."
        final_file_path = DATASET_DIR / f"{dataset_hash}.csv"
        temp_file_path.rename(final_file_path)

        auto_name = req.name or (
            f"{req.symbol}_{req.market_type}_{req.timeframe}_"
            f"{req.start_date}_{req.end_date}"
        )
        dataset_id = repo.create(
            name=auto_name,
            dataset_hash=dataset_hash,
            file_path=str(final_file_path),
            bars_count=metadata["bars_count"],
            start_timestamp=metadata["start_timestamp"],
            end_timestamp=metadata["end_timestamp"],
            description=req.description,
            timeframe=req.timeframe,
            symbol=req.symbol,
            market_type=req.market_type,
        )

        job["status"] = "COMPLETED"
        job["dataset_id"] = dataset_id
        job["bars_count"] = metadata["bars_count"]
        job["progress_message"] = f"완료 ({metadata['bars_count']:,}봉)"
        logger.info(f"[job {job_id}] 완료 → dataset_id={dataset_id}, bars={rows}")

    except Exception as e:
        logger.error(f"[job {job_id}] 실패: {e}", exc_info=True)
        job["status"] = "FAILED"
        job["error"] = str(e)
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)


@router.post("/binance", status_code=202)
async def create_dataset_from_binance(
    req: BinanceFetchRequest,
    background_tasks: BackgroundTasks,
):
    """바이낸스에서 OHLCV를 자동 수집해 데이터셋으로 등록 (비동기).

    아카이브(data.binance.vision)에서 대량 백필 + REST로 최근 봉 보완.
    응답의 job_id로 `GET /datasets/binance/jobs/{job_id}` 폴링하여 진행 확인.
    """
    job_id = uuid.uuid4().hex[:12]
    _BINANCE_JOBS[job_id] = {
        "status": "PENDING",
        "symbol": req.symbol,
        "market_type": req.market_type,
        "timeframe": req.timeframe,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "started_at": int(time.time()),
    }
    background_tasks.add_task(_run_binance_fetch_job, job_id, req)
    return {"job_id": job_id, "status": "PENDING"}


@router.get("/binance/jobs/{job_id}")
async def get_binance_fetch_job(job_id: str):
    """바이낸스 fetch 작업 상태 조회."""
    job = _BINANCE_JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job_id 없음: {job_id}")
    return {"job_id": job_id, **job}


@router.post("/{dataset_id}/refresh", status_code=202)
async def refresh_dataset_from_binance(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    end_date: Optional[str] = None,
):
    """기존 데이터셋의 마지막 봉 이후부터 현재까지 바이낸스에서 증분 수집.

    기존 데이터는 불변 (결정성 보장) — 새로운 dataset_id로 확장된 데이터셋 생성.
    end_date 미지정 시 오늘(KST 달력) 기준.
    """
    db = get_database()
    repo = DatasetRepository(db)
    dataset = repo.get_by_id(dataset_id)
    if not dataset:
        raise DatasetNotFoundError(dataset_id)

    # 마지막 봉 시각(KST) 다음 날짜부터 수집
    last_open_kst = datetime.fromtimestamp(dataset["end_timestamp"], tz=_KST)
    next_day = last_open_kst.date() + timedelta(days=1)
    end_d_str = end_date or datetime.now(_KST).date().isoformat()

    if next_day.isoformat() > end_d_str:
        raise HTTPException(
            status_code=400,
            detail=f"이미 최신 상태입니다 (last_end_kst={last_open_kst.isoformat()})",
        )

    # 참고: 증분분만 담은 별도 dataset 생성 (기존 데이터와 분리해 추적)
    # 결합된 데이터셋이 필요하면 별도 UI/엔드포인트에서 수동 병합
    req = BinanceFetchRequest(
        symbol=dataset["symbol"],
        market_type=dataset["market_type"],
        timeframe=dataset["timeframe"],
        start_date=next_day.isoformat(),
        end_date=end_d_str,
        name=f"{dataset['name']}_refresh_{next_day.isoformat()}_{end_d_str}",
        description=f"증분 수집 from dataset_id={dataset_id}",
    )
    job_id = uuid.uuid4().hex[:12]
    _BINANCE_JOBS[job_id] = {
        "status": "PENDING",
        "symbol": req.symbol,
        "market_type": req.market_type,
        "timeframe": req.timeframe,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "started_at": int(time.time()),
        "refresh_of": dataset_id,
    }
    background_tasks.add_task(_run_binance_fetch_job, job_id, req)
    return {"job_id": job_id, "status": "PENDING", "refresh_of": dataset_id}

