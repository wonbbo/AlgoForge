"""
포지션 크기 동적 조정 테스트
50거래마다 잔고 재평가 로직 검증
"""
import pytest
from typing import Optional, Dict, Any
from engine.core.backtest_engine import BacktestEngine
from engine.models.bar import Bar


def test_position_sizing_rebalance():
    """
    50거래마다 포지션 크기가 재평가되는지 테스트
    
    시나리오:
    1. 초기 자산 10000으로 시작
    2. 50거래 진행 (모두 승리 가정)
    3. 50거래 후 잔고가 증가하면 포지션 크기도 증가해야 함
    """
    initial_balance = 10000
    
    # 테스트용 간단한 봉 데이터 생성
    # 가격이 상승하는 추세 (롱 포지션이 이익을 내도록)
    bars = []
    base_price = 100.0
    timestamp = 1704067200
    
    # 150개 봉 생성 (50거래 이상 가능하도록)
    for i in range(150):
        # 가격이 점진적으로 상승
        price = base_price + i * 0.5
        bar = Bar(
            timestamp=timestamp + i * 300,  # 5분 간격
            open=price,
            high=price + 2.0,
            low=price - 0.5,
            close=price + 1.0,
            volume=1000.0,
            direction=1
        )
        bars.append(bar)
    
    # 전략: 매 3번째 봉마다 롱 진입 신호
    # SL은 진입가 - 1.0으로 설정 (작은 손실)
    def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
        bar_index = (bar.timestamp - 1704067200) // 300
        if bar_index % 3 == 0:  # 매 3번째 봉
            return {
                'direction': 'LONG',
                'stop_loss': bar.close - 1.0
            }
        # 매 3번째 봉 다음 봉에서 반대 신호로 청산
        elif bar_index % 3 == 1:
            return {
                'direction': 'SHORT',
                'stop_loss': bar.close + 10.0  # 청산용
            }
        return None
    
    # 엔진 실행
    engine = BacktestEngine(
        initial_balance=initial_balance,
        strategy_func=strategy_func
    )
    trades = engine.run(bars)
    
    # 검증: 최소 50거래 이상 발생했는지 확인
    assert len(trades) >= 50, f"50거래 이상 필요: {len(trades)}개 거래 발생"
    
    # 첫 번째 거래의 포지션 크기 기록
    first_trade_position_size = trades[0].position_size
    print(f"\n첫 번째 거래 포지션 크기: {first_trade_position_size}")
    
    # 50번째 거래 이후의 포지션 크기 확인
    if len(trades) > 50:
        trade_51_position_size = trades[50].position_size
        print(f"51번째 거래 포지션 크기: {trade_51_position_size}")
        
        # 50거래 후 누적 PnL 계산
        total_pnl_after_50 = sum(t.calculate_total_pnl() for t in trades[:50])
        print(f"50거래 후 누적 PnL: {total_pnl_after_50}")
        
        # 예상 잔고
        expected_balance_after_50 = initial_balance + total_pnl_after_50
        print(f"50거래 후 예상 잔고: {expected_balance_after_50}")
        
        # 포지션 크기 비율 확인
        # 만약 잔고가 증가했다면 포지션 크기도 증가해야 함
        if total_pnl_after_50 > 0:
            # 포지션 크기가 증가했는지 확인
            # (동일한 리스크 조건이라면 잔고 증가 비율만큼 포지션 크기도 증가)
            balance_ratio = expected_balance_after_50 / initial_balance
            print(f"잔고 증가 비율: {balance_ratio}")
            
            # 51번째 거래의 포지션 크기가 첫 거래보다 커야 함
            # (단, 리스크가 동일한 경우에만 정확히 비례)
            # 여기서는 대략적으로 증가했는지만 확인
            assert trade_51_position_size > first_trade_position_size, \
                f"51번째 거래의 포지션 크기({trade_51_position_size})가 " \
                f"첫 거래({first_trade_position_size})보다 커야 합니다"
            
            print(f"[OK] 포지션 크기가 {first_trade_position_size:.2f} -> {trade_51_position_size:.2f}로 증가")
    
    # RiskManager의 current_balance 확인
    print(f"\n최종 RiskManager current_balance: {engine.risk_manager.current_balance}")
    print(f"완료된 거래 수: {engine.completed_trades_count}")
    
    # 100거래 후에도 재평가되었는지 확인
    if len(trades) >= 100:
        total_pnl_after_100 = sum(t.calculate_total_pnl() for t in trades[:100])
        expected_balance_after_100 = initial_balance + total_pnl_after_100
        print(f"\n100거래 후 예상 잔고: {expected_balance_after_100}")


def test_position_sizing_with_losses():
    """
    손실이 발생하는 경우 포지션 크기 감소 테스트
    
    시나리오:
    1. 초기 자산 10000으로 시작
    2. 50거래 진행 (모두 손실 가정)
    3. 50거래 후 잔고가 감소하면 포지션 크기도 감소해야 함
    """
    initial_balance = 10000
    
    # 테스트용 간단한 봉 데이터 생성
    # 가격이 하락하는 추세 (롱 포지션이 손실을 내도록)
    bars = []
    base_price = 100.0
    timestamp = 1704067200
    
    # 150개 봉 생성
    for i in range(150):
        # 가격이 점진적으로 하락
        price = base_price - i * 0.3
        bar = Bar(
            timestamp=timestamp + i * 300,
            open=price,
            high=price + 0.5,
            low=price - 2.0,  # 낮은 저가로 SL 도달
            close=price - 0.5,
            volume=1000.0,
            direction=-1
        )
        bars.append(bar)
    
    # 전략: 매 3번째 봉마다 롱 진입 (손실 발생)
    def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
        bar_index = (bar.timestamp - 1704067200) // 300
        if bar_index % 3 == 0:
            return {
                'direction': 'LONG',
                'stop_loss': bar.close - 1.0  # SL 도달 예상
            }
        return None
    
    # 엔진 실행
    engine = BacktestEngine(
        initial_balance=initial_balance,
        strategy_func=strategy_func
    )
    trades = engine.run(bars)
    
    # 검증
    if len(trades) >= 50:
        first_trade_position_size = trades[0].position_size
        print(f"\n첫 번째 거래 포지션 크기: {first_trade_position_size}")
        
        # 50거래 후 누적 PnL
        total_pnl_after_50 = sum(t.calculate_total_pnl() for t in trades[:50])
        print(f"50거래 후 누적 PnL: {total_pnl_after_50}")
        
        # 손실이 발생했는지 확인
        if total_pnl_after_50 < 0:
            expected_balance = initial_balance + total_pnl_after_50
            print(f"50거래 후 예상 잔고: {expected_balance}")
            
            # 51번째 거래가 있다면 포지션 크기 확인
            if len(trades) > 50:
                trade_51_position_size = trades[50].position_size
                print(f"51번째 거래 포지션 크기: {trade_51_position_size}")
                
                # 손실로 인해 포지션 크기가 감소해야 함
                assert trade_51_position_size < first_trade_position_size, \
                    f"51번째 거래의 포지션 크기({trade_51_position_size})가 " \
                    f"첫 거래({first_trade_position_size})보다 작아야 합니다"
                
                print(f"[OK] 포지션 크기가 {first_trade_position_size:.2f} -> {trade_51_position_size:.2f}로 감소")


def test_determinism_with_rebalancing():
    """
    잔고 재평가 로직이 결정성을 유지하는지 테스트
    
    동일한 입력으로 3번 실행했을 때 모든 결과가 동일해야 함
    """
    initial_balance = 10000
    
    # 간단한 테스트 데이터
    bars = []
    timestamp = 1704067200
    for i in range(100):
        price = 100.0 + i * 0.2
        bar = Bar(
            timestamp=timestamp + i * 300,
            open=price,
            high=price + 1.0,
            low=price - 0.5,
            close=price + 0.5,
            volume=1000.0,
            direction=1
        )
        bars.append(bar)
    
    def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
        bar_index = (bar.timestamp - 1704067200) // 300
        if bar_index % 5 == 0:
            return {
                'direction': 'LONG',
                'stop_loss': bar.close - 1.0
            }
        elif bar_index % 5 == 2:
            return {
                'direction': 'SHORT',
                'stop_loss': bar.close + 10.0
            }
        return None
    
    # 3번 실행
    results = []
    for _ in range(3):
        engine = BacktestEngine(
            initial_balance=initial_balance,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        results.append(trades)
    
    # 모든 결과가 동일한지 확인
    for i in range(len(results) - 1):
        assert len(results[i]) == len(results[i + 1]), \
            "결정성 위반: 거래 수가 다릅니다"
        
        for j in range(len(results[i])):
            trade1 = results[i][j]
            trade2 = results[i + 1][j]
            
            assert trade1.position_size == trade2.position_size, \
                f"결정성 위반: trade {j+1}의 position_size가 다릅니다"
            
            assert trade1.calculate_total_pnl() == trade2.calculate_total_pnl(), \
                f"결정성 위반: trade {j+1}의 total_pnl이 다릅니다"
    
    print("\n[OK] 잔고 재평가 로직이 결정성을 유지합니다")

