"""
레버리지 테이블 로더 모듈
"""
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class LeverageBracket:
    """
    레버리지 구간 정보
    
    Attributes:
        bracket_min: 포지션 명목가치 최소값 (USDT)
        bracket_max: 포지션 명목가치 최대값 (USDT)
        max_leverage: 최대 레버리지
        m_margin_rate: 유지 증거금률
        m_amount: 유지 증거금 고정값
    """
    bracket_min: float
    bracket_max: float
    max_leverage: float
    m_margin_rate: float
    m_amount: float


def load_leverage_brackets_from_db(db_conn) -> List[LeverageBracket]:
    """
    데이터베이스에서 레버리지 구간 로드
    
    Args:
        db_conn: 데이터베이스 연결 객체 (Database 인스턴스)
    
    Returns:
        LeverageBracket 객체 리스트 (bracket_min 기준 오름차순)
    
    Raises:
        ValueError: 레버리지 구간 데이터가 없는 경우
    
    Note:
        데이터베이스의 leverage_brackets 테이블에서 조회
        결정성 보장을 위해 bracket_min 기준 오름차순 정렬
    """
    from apps.api.db.repositories import LeverageBracketRepository
    
    repo = LeverageBracketRepository(db_conn)
    bracket_dicts = repo.get_all()
    
    if not bracket_dicts:
        raise ValueError("레버리지 구간 데이터가 데이터베이스에 없습니다. "
                        "scripts/migrate_leverage_data.py를 실행하여 데이터를 마이그레이션하세요.")
    
    # Dictionary를 LeverageBracket 객체로 변환
    brackets = [
        LeverageBracket(
            bracket_min=b['bracket_min'],
            bracket_max=b['bracket_max'],
            max_leverage=b['max_leverage'],
            m_margin_rate=b['m_margin_rate'],
            m_amount=b['m_amount']
        )
        for b in bracket_dicts
    ]
    
    return brackets


def get_max_leverage_for_notional(brackets: List[LeverageBracket], notional_value: float) -> float:
    """
    포지션 명목가치에 대한 최대 레버리지 조회
    
    Args:
        brackets: 레버리지 구간 리스트
        notional_value: 포지션 명목가치 (position_size × entry_price)
    
    Returns:
        최대 레버리지
    
    Note:
        - notional_value가 음수이면 절댓값 사용
        - 어떤 구간에도 속하지 않으면 가장 낮은 레버리지 반환 (안전 장치)
    """
    if not brackets:
        raise ValueError("레버리지 구간 정보가 비어있습니다")
    
    # 명목가치의 절댓값 사용 (롱/숏 모두 동일하게 처리)
    notional = abs(notional_value)
    
    # 해당하는 구간 찾기
    for bracket in brackets:
        if bracket.bracket_min <= notional < bracket.bracket_max:
            return bracket.max_leverage
    
    # 마지막 구간을 초과하는 경우 마지막 구간의 레버리지 사용
    if notional >= brackets[-1].bracket_max:
        return brackets[-1].max_leverage
    
    # 안전 장치: 어떤 구간에도 속하지 않으면 가장 낮은 레버리지 반환
    return min(bracket.max_leverage for bracket in brackets)


def calculate_required_margin(
    position_size: float, 
    entry_price: float, 
    max_leverage: float
) -> float:
    """
    포지션에 필요한 증거금 계산
    
    Args:
        position_size: 포지션 크기 (계약 수)
        entry_price: 진입 가격
        max_leverage: 최대 레버리지
    
    Returns:
        필요 증거금 (USDT)
    
    Note:
        공식: (position_size × entry_price) / max_leverage
    """
    if max_leverage <= 0:
        raise ValueError("max_leverage는 0보다 커야 합니다")
    
    notional_value = abs(position_size * entry_price)
    required_margin = notional_value / max_leverage
    
    return required_margin

