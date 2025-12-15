"""
Preset API Router

프리셋 생성, 조회, 수정, 삭제 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException
import logging

from apps.api.db.database import get_database
from apps.api.db.repositories import PresetRepository
from apps.api.schemas import (
    PresetCreate,
    PresetUpdate,
    PresetResponse,
    PresetList
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PresetList)
async def get_presets():
    """
    프리셋 목록 조회
    
    Returns:
        PresetList: 프리셋 목록
    """
    try:
        db = get_database()
        repo = PresetRepository(db)
        
        presets = repo.get_all()
        
        return PresetList(
            presets=[PresetResponse(**p) for p in presets],
            total=len(presets)
        )
        
    except Exception as e:
        logger.error(f"Failed to get presets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"프리셋 목록 조회 실패: {str(e)}")


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: int):
    """
    프리셋 상세 조회
    
    Args:
        preset_id: 프리셋 ID
        
    Returns:
        PresetResponse: 프리셋 정보
    """
    try:
        db = get_database()
        repo = PresetRepository(db)
        
        preset = repo.get_by_id(preset_id)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id}를 찾을 수 없습니다")
        
        return PresetResponse(**preset)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preset {preset_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"프리셋 조회 실패: {str(e)}")


@router.post("", response_model=PresetResponse, status_code=201)
async def create_preset(preset_create: PresetCreate):
    """
    프리셋 생성
    
    Args:
        preset_create: 프리셋 생성 요청 데이터
        
    Returns:
        PresetResponse: 생성된 프리셋 정보
    """
    try:
        db = get_database()
        repo = PresetRepository(db)
        
        # 프리셋 생성
        preset_id = repo.create(
            name=preset_create.name,
            description=preset_create.description,
            initial_balance=preset_create.initial_balance,
            risk_percent=preset_create.risk_percent,
            risk_reward_ratio=preset_create.risk_reward_ratio,
            rebalance_interval=preset_create.rebalance_interval
        )
        
        # 생성된 프리셋 조회
        preset = repo.get_by_id(preset_id)
        
        logger.info(f"Preset created: ID={preset_id}, name={preset_create.name}")
        
        return PresetResponse(**preset)
        
    except Exception as e:
        logger.error(f"Failed to create preset: {str(e)}", exc_info=True)
        
        # 중복 이름 에러 체크
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"프리셋 이름 '{preset_create.name}'이 이미 존재합니다"
            )
        
        raise HTTPException(status_code=500, detail=f"프리셋 생성 실패: {str(e)}")


@router.patch("/{preset_id}", response_model=PresetResponse)
async def update_preset(preset_id: int, preset_update: PresetUpdate):
    """
    프리셋 수정
    
    Args:
        preset_id: 프리셋 ID
        preset_update: 프리셋 수정 요청 데이터
        
    Returns:
        PresetResponse: 수정된 프리셋 정보
    """
    try:
        db = get_database()
        repo = PresetRepository(db)
        
        # 프리셋 존재 확인
        preset = repo.get_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id}를 찾을 수 없습니다")
        
        # is_default 처리 (별도 엔드포인트 사용 권장)
        if preset_update.is_default is not None:
            if preset_update.is_default:
                repo.set_default(preset_id)
            # is_default를 False로 설정하는 것은 허용하지 않음
            # (항상 하나의 기본 프리셋이 있어야 함)
        
        # 프리셋 수정
        repo.update(
            preset_id=preset_id,
            name=preset_update.name,
            description=preset_update.description,
            initial_balance=preset_update.initial_balance,
            risk_percent=preset_update.risk_percent,
            risk_reward_ratio=preset_update.risk_reward_ratio,
            rebalance_interval=preset_update.rebalance_interval
        )
        
        # 수정된 프리셋 조회
        updated_preset = repo.get_by_id(preset_id)
        
        logger.info(f"Preset updated: ID={preset_id}")
        
        return PresetResponse(**updated_preset)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preset {preset_id}: {str(e)}", exc_info=True)
        
        # 중복 이름 에러 체크
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"프리셋 이름 '{preset_update.name}'이 이미 존재합니다"
            )
        
        raise HTTPException(status_code=500, detail=f"프리셋 수정 실패: {str(e)}")


@router.delete("/{preset_id}", status_code=204)
async def delete_preset(preset_id: int):
    """
    프리셋 삭제
    
    Args:
        preset_id: 프리셋 ID
    """
    try:
        db = get_database()
        repo = PresetRepository(db)
        
        # 프리셋 존재 확인
        preset = repo.get_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id}를 찾을 수 없습니다")
        
        # 기본 프리셋인지 확인
        if preset['is_default']:
            raise HTTPException(
                status_code=400,
                detail="기본 프리셋은 삭제할 수 없습니다. 다른 프리셋을 기본으로 설정한 후 삭제하세요."
            )
        
        # 프리셋 삭제
        repo.delete(preset_id)
        
        logger.info(f"Preset deleted: ID={preset_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete preset {preset_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"프리셋 삭제 실패: {str(e)}")


@router.post("/{preset_id}/set-default", response_model=PresetResponse)
async def set_default_preset(preset_id: int):
    """
    기본 프리셋 설정
    
    Args:
        preset_id: 기본으로 설정할 프리셋 ID
        
    Returns:
        PresetResponse: 기본 프리셋으로 설정된 프리셋 정보
    """
    try:
        db = get_database()
        repo = PresetRepository(db)
        
        # 프리셋 존재 확인
        preset = repo.get_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id}를 찾을 수 없습니다")
        
        # 기본 프리셋 설정
        repo.set_default(preset_id)
        
        # 업데이트된 프리셋 조회
        updated_preset = repo.get_by_id(preset_id)
        
        logger.info(f"Default preset set: ID={preset_id}")
        
        return PresetResponse(**updated_preset)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default preset {preset_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"기본 프리셋 설정 실패: {str(e)}")
