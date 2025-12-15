"""
Indicators Router - 지표 관리 API

지표 조회, 등록, 수정, 삭제 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json
import time
import logging

from apps.api.schemas.indicator import (
    IndicatorResponse,
    IndicatorList,
    CustomIndicatorCreate,
    CustomIndicatorUpdate,
    IndicatorValidationResult,
    CodeValidationRequest
)
from apps.api.db.database import get_database
from apps.api.utils.code_validator import (
    validate_indicator_code,
    validate_indicator_code_simple
)
from apps.api.utils.responses import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=IndicatorList)
def list_indicators(
    category: Optional[str] = Query(None, description="카테고리 필터 (trend/momentum/volatility/volume)"),
    implementation_type: Optional[str] = Query(None, description="구현 타입 필터 (builtin/custom)")
):
    """
    등록된 지표 목록 조회
    
    Query Parameters:
        - category: 카테고리 필터 (선택)
        - implementation_type: 구현 타입 필터 (선택)
    
    Returns:
        IndicatorList: 지표 목록 및 전체 개수
    """
    db = get_database()
    
    # 쿼리 빌드
    query = "SELECT * FROM indicators WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if implementation_type:
        query += " AND implementation_type = ?"
        params.append(implementation_type)
    
    query += " ORDER BY category, name"
    
    # 실행
    with db.get_connection() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
    
    # 응답 생성
    indicators = []
    for row in rows:
        indicators.append(
            IndicatorResponse(
                indicator_id=row[0],
                name=row[1],
                type=row[2],
                description=row[3],
                category=row[4],
                implementation_type=row[5],
                code=row[6],  # code 필드 포함
                params_schema=row[7],
                output_fields=json.loads(row[8]),
                created_at=row[9]
            )
        )
    
    return IndicatorList(indicators=indicators, total=len(indicators))


@router.get("/{indicator_type}", response_model=IndicatorResponse)
def get_indicator(indicator_type: str):
    """
    지표 상세 정보 조회
    
    Path Parameters:
        - indicator_type: 지표 타입 (예: 'ema', 'rsi')
    
    Returns:
        IndicatorResponse: 지표 상세 정보
    
    Raises:
        HTTPException 404: 지표를 찾을 수 없는 경우
    """
    db = get_database()
    
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM indicators WHERE type = ?",
            (indicator_type,)
        )
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"지표를 찾을 수 없습니다: {indicator_type}"
        )
    
    return IndicatorResponse(
        indicator_id=row[0],
        name=row[1],
        type=row[2],
        description=row[3],
        category=row[4],
        implementation_type=row[5],
        code=row[6],  # code 필드 포함
        params_schema=row[7],
        output_fields=json.loads(row[8]),
        created_at=row[9]
    )


@router.post("/custom", response_model=IndicatorResponse, status_code=201)
def register_custom_indicator(indicator: CustomIndicatorCreate):
    """
    커스텀 지표 등록
    
    Body:
        CustomIndicatorCreate: 커스텀 지표 정보
    
    Returns:
        IndicatorResponse: 등록된 지표 정보
    
    Raises:
        HTTPException 400: 중복된 지표 타입 또는 코드 검증 실패
    """
    db = get_database()
    
    # 1. 중복 체크
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT indicator_id FROM indicators WHERE type = ?",
            (indicator.type,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"이미 등록된 지표 타입입니다: {indicator.type}"
            )
    
    # 2. 코드 검증
    try:
        validate_indicator_code_simple(indicator.code)
    except ValueError as e:
        logger.warning(f"지표 코드 검증 실패: {indicator.type}, {e}")
        raise HTTPException(
            status_code=400,
            detail=f"코드 검증 실패: {str(e)}"
        )
    
    # 3. params_schema JSON 검증
    try:
        json.loads(indicator.params_schema)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"params_schema가 유효한 JSON이 아닙니다: {str(e)}"
        )
    
    # 4. 등록
    now = int(time.time())
    
    with db.get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO indicators 
            (name, type, description, category, implementation_type, code, 
             params_schema, output_fields, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'custom', ?, ?, ?, ?, ?)
            """,
            (
                indicator.name,
                indicator.type,
                indicator.description,
                indicator.category,
                indicator.code,
                indicator.params_schema,
                json.dumps(indicator.output_fields),
                now,
                now
            )
        )
        conn.commit()
        indicator_id = cursor.lastrowid
    
    logger.info(f"커스텀 지표 등록 완료: {indicator.type} (ID: {indicator_id})")
    
    # 5. 등록된 지표 반환
    return get_indicator(indicator.type)


@router.patch("/{indicator_type}", response_model=IndicatorResponse)
def update_custom_indicator(indicator_type: str, update_data: CustomIndicatorUpdate):
    """
    커스텀 지표 수정 (builtin 지표는 수정 불가)
    
    Path Parameters:
        - indicator_type: 지표 타입
    
    Body:
        CustomIndicatorUpdate: 수정할 필드 (선택적)
    
    Returns:
        IndicatorResponse: 수정된 지표 정보
    
    Raises:
        HTTPException 404: 지표를 찾을 수 없는 경우
        HTTPException 400: builtin 지표 수정 시도 또는 코드 검증 실패
    """
    db = get_database()
    
    # 1. 지표 존재 및 타입 확인
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT indicator_id, implementation_type FROM indicators WHERE type = ?",
            (indicator_type,)
        )
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"지표를 찾을 수 없습니다: {indicator_type}"
        )
    
    indicator_id, impl_type = row
    
    if impl_type == 'builtin':
        raise HTTPException(
            status_code=400,
            detail="내장 지표는 수정할 수 없습니다"
        )
    
    # 2. 수정할 필드 수집
    update_fields = []
    update_values = []
    
    if update_data.name is not None:
        update_fields.append("name = ?")
        update_values.append(update_data.name)
    
    if update_data.description is not None:
        update_fields.append("description = ?")
        update_values.append(update_data.description)
    
    if update_data.category is not None:
        # 카테고리 유효성 검증
        valid_categories = ['trend', 'momentum', 'volatility', 'volume']
        if update_data.category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 카테고리입니다. 허용된 값: {', '.join(valid_categories)}"
            )
        update_fields.append("category = ?")
        update_values.append(update_data.category)
    
    if update_data.code is not None:
        # 코드 검증
        try:
            validate_indicator_code_simple(update_data.code)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"코드 검증 실패: {str(e)}"
            )
        update_fields.append("code = ?")
        update_values.append(update_data.code)
    
    if update_data.params_schema is not None:
        # JSON 검증
        try:
            json.loads(update_data.params_schema)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"params_schema가 유효한 JSON이 아닙니다: {str(e)}"
            )
        update_fields.append("params_schema = ?")
        update_values.append(update_data.params_schema)
    
    if update_data.output_fields is not None:
        update_fields.append("output_fields = ?")
        update_values.append(json.dumps(update_data.output_fields))
    
    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="수정할 필드가 없습니다"
        )
    
    # 3. updated_at 추가
    update_fields.append("updated_at = ?")
    update_values.append(int(time.time()))
    
    # 4. 업데이트 실행
    update_values.append(indicator_type)
    
    with db.get_connection() as conn:
        conn.execute(
            f"UPDATE indicators SET {', '.join(update_fields)} WHERE type = ?",
            update_values
        )
        conn.commit()
    
    logger.info(f"커스텀 지표 수정 완료: {indicator_type}")
    
    # 5. 수정된 지표 반환
    return get_indicator(indicator_type)


@router.delete("/{indicator_type}", status_code=204)
def delete_custom_indicator(indicator_type: str):
    """
    커스텀 지표 삭제 (builtin 지표는 삭제 불가)
    
    Path Parameters:
        - indicator_type: 지표 타입
    
    Raises:
        HTTPException 404: 지표를 찾을 수 없는 경우
        HTTPException 400: builtin 지표 삭제 시도
    """
    db = get_database()
    
    # 1. 지표 존재 및 타입 확인
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT indicator_id, implementation_type FROM indicators WHERE type = ?",
            (indicator_type,)
        )
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"지표를 찾을 수 없습니다: {indicator_type}"
        )
    
    indicator_id, impl_type = row
    
    if impl_type == 'builtin':
        raise HTTPException(
            status_code=400,
            detail="내장 지표는 삭제할 수 없습니다"
        )
    
    # 2. 삭제
    with db.get_connection() as conn:
        conn.execute(
            "DELETE FROM indicators WHERE type = ?",
            (indicator_type,)
        )
        conn.commit()
    
    logger.info(f"커스텀 지표 삭제 완료: {indicator_type}")


@router.post("/validate", response_model=IndicatorValidationResult)
def validate_code_endpoint(request: CodeValidationRequest):
    """
    지표 코드 검증 (등록 전 미리 검증)
    
    Body:
        CodeValidationRequest: 검증할 코드
    
    Returns:
        IndicatorValidationResult: 검증 결과
    """
    is_valid, message, errors = validate_indicator_code(request.code)
    
    return IndicatorValidationResult(
        is_valid=is_valid,
        message=message,
        errors=errors if errors else None
    )

