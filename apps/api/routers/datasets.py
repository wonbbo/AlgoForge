"""
Dataset API Router

데이터셋 업로드, 조회, 삭제 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging
import os
import time
from pathlib import Path

from apps.api.db.database import get_database
from apps.api.db.repositories import DatasetRepository
from apps.api.db.utils import load_bars_from_csv, calculate_dataset_hash, validate_bars
from apps.api.schemas import DatasetCreate, DatasetResponse, DatasetList
from apps.api.utils.exceptions import DatasetNotFoundError, InvalidDataError, DuplicateDataError

router = APIRouter()
logger = logging.getLogger(__name__)

# 데이터셋 파일 저장 디렉토리
DATASET_DIR = Path("datasets")
DATASET_DIR.mkdir(exist_ok=True)


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
    - dt: datetime 문자열 'YYYY-MM-DD HH:MM:SS' (예: '2024-05-31 00:00:00')
    - do: 시가 (open)
    - dh: 고가 (high)
    - dl: 저가 (low)
    - dc: 종가 (close)
    - dv: 거래량 (volume)
    - dd: 봉 방향 (1=상승, -1=하락, 0=보합)
    
    Note:
        dt는 내부적으로 UNIX timestamp로 변환되어 저장됩니다.
    
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
            bars, df, metadata = load_bars_from_csv(str(temp_file_path))
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

