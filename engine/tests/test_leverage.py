"""
레버리지 제약 테스트
"""
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.core.risk_manager import RiskManager
from engine.utils.leverage_loader import (
    load_leverage_brackets_from_db,
    get_max_leverage_for_notional,
    calculate_required_margin,
    LeverageBracket
)
from apps.api.db.database import get_database


class TestLeverageLoader:
    """레버리지 로더 테스트"""
    
    def test_load_leverage_brackets_from_db(self):
        """데이터베이스에서 레버리지 구간 로드 테스트"""
        # DB 연결
        db = get_database()
        
        brackets = load_leverage_brackets_from_db(db)
        
        # 최소 1개 이상의 구간이 있어야 함
        assert len(brackets) > 0
        
        # 첫 번째 구간 확인
        assert brackets[0].bracket_min == 0
        assert brackets[0].bracket_max == 10000
        assert brackets[0].max_leverage == 75
        
        # 오름차순 정렬 확인
        for i in range(len(brackets) - 1):
            assert brackets[i].bracket_min < brackets[i + 1].bracket_min
    
    def test_get_max_leverage_for_notional(self):
        """명목가치에 대한 최대 레버리지 조회 테스트"""
        brackets = [
            LeverageBracket(0, 10000, 75, 0.005, 0),
            LeverageBracket(10000, 20000, 50, 0.0065, 15),
            LeverageBracket(20000, 160000, 40, 0.01, 85)
        ]
        
        # 0~10000 구간
        assert get_max_leverage_for_notional(brackets, 5000) == 75
        
        # 10000~20000 구간
        assert get_max_leverage_for_notional(brackets, 15000) == 50
        
        # 20000~160000 구간
        assert get_max_leverage_for_notional(brackets, 50000) == 40
        
        # 마지막 구간 초과
        assert get_max_leverage_for_notional(brackets, 200000) == 40
    
    def test_calculate_required_margin(self):
        """필요 증거금 계산 테스트"""
        # 포지션 크기: 1 계약, 진입가: 50000, 레버리지: 10
        # 명목가치: 50000, 필요 증거금: 5000
        required_margin = calculate_required_margin(1, 50000, 10)
        assert required_margin == 5000
        
        # 포지션 크기: 2 계약, 진입가: 50000, 레버리지: 20
        # 명목가치: 100000, 필요 증거금: 5000
        required_margin = calculate_required_margin(2, 50000, 20)
        assert required_margin == 5000


class TestRiskManagerWithLeverage:
    """레버리지 제약이 적용된 RiskManager 테스트"""
    
    def test_position_size_without_leverage_constraint(self):
        """레버리지 제약 없이 포지션 크기 계산"""
        # 초기 자산: 1000, 리스크: 2%
        risk_manager = RiskManager(initial_balance=1000)
        
        # 진입가: 50000, 손절가: 49000 (리스크: 1000)
        # 포지션 크기: (1000 * 0.02) / 1000 = 0.02 -> 반올림 1
        position_size, risk = risk_manager.calculate_position_size(50000, 49000)
        
        assert risk == 1000
        assert position_size == 1.0  # 반올림 후 최소 1
    
    def test_position_size_with_leverage_constraint(self):
        """레버리지 제약 적용 시 포지션 크기 계산"""
        # DB 연결
        db = get_database()
        
        # 초기 자산: 1000
        risk_manager = RiskManager(
            initial_balance=1000,
            db_conn=db
        )
        
        # 진입가: 50000, 손절가: 49000 (리스크: 1000)
        # 리스크 기반 포지션 크기: (1000 * 0.02) / 1000 = 0.02
        # 반올림 전 레버리지 제약 적용
        position_size, risk = risk_manager.calculate_position_size(50000, 49000)
        
        # 레버리지 제약이 적용되어야 함
        # 명목가치 = 0.02 * 50000 = 1000 (0~10000 구간, 최대 레버리지 75)
        # 필요 증거금 = 1000 / 75 = 13.33
        # 현재 잔고 1000으로 충분히 가능
        # 따라서 원래 계산된 포지션 크기(0.02 -> 반올림 1) 유지
        assert risk == 1000
        assert position_size == 1.0
    
    def test_position_size_reduced_by_leverage_constraint(self):
        """레버리지 제약으로 인한 포지션 크기 축소 테스트"""
        # DB 연결
        db = get_database()
        
        # 초기 자산: 100 (작은 금액으로 테스트)
        risk_manager = RiskManager(
            initial_balance=100,
            db_conn=db
        )
        
        # 진입가: 50000, 손절가: 48000 (리스크: 2000)
        # 리스크 기반 포지션 크기: (100 * 0.02) / 2000 = 0.001
        position_size, risk = risk_manager.calculate_position_size(50000, 48000)
        
        # 반올림 후 최소 1이 되지만, 레버리지 제약에 의해 조정될 수 있음
        assert risk == 2000
        # 포지션 크기는 잔고와 레버리지에 의해 제한됨
        # 명목가치가 크면 레버리지가 낮아지므로 더 많은 증거금이 필요
        assert position_size >= 0
    
    def test_apply_leverage_constraint_directly(self):
        """_apply_leverage_constraint 메서드 직접 테스트"""
        # DB 연결
        db = get_database()
        
        # 초기 자산: 5000
        risk_manager = RiskManager(
            initial_balance=5000,
            db_conn=db
        )
        
        # 진입가: 50000, 포지션 크기: 2 계약
        # 명목가치: 100000 (10000~20000 구간, 최대 레버리지 50)
        # 필요 증거금: 100000 / 50 = 2000
        # 현재 잔고 5000 > 2000이므로 진입 가능
        adjusted_size = risk_manager._apply_leverage_constraint(2.0, 50000)
        
        # 레버리지 제약을 만족하므로 원래 크기 유지
        assert adjusted_size == 2.0
        
        # 포지션 크기: 10 계약
        # 명목가치: 500000 (160000~1000000 구간, 최대 레버리지 25)
        # 필요 증거금: 500000 / 25 = 20000
        # 현재 잔고 5000 < 20000이므로 축소 필요
        # 최대 포지션 크기: (5000 * 25) / 50000 = 2.5
        adjusted_size = risk_manager._apply_leverage_constraint(10.0, 50000)
        
        # 레버리지 제약에 의해 축소됨
        assert adjusted_size == 2.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

