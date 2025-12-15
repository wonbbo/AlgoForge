"""
백테스트 엔진 테스트
"""
import pytest
import json
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from engine.core.backtest_engine import BacktestEngine
from engine.core.metrics_calculator import MetricsCalculator
from engine.models.bar import Bar


class TestBacktestEngine:
    """백테스트 엔진 테스트"""
    
    @pytest.fixture
    def test_data_dir(self) -> Path:
        """테스트 데이터 디렉토리"""
        return Path(__file__).parent.parent.parent / 'tests' / 'fixtures'
    
    def load_bars(self, csv_path: Path) -> List[Bar]:
        """
        CSV에서 Bar 데이터 로드
        
        Args:
            csv_path: CSV 파일 경로
        
        Returns:
            Bar 리스트
        """
        bars = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # dt를 datetime 문자열에서 UNIX timestamp로 변환
                dt_str = row['dt'].strip()
                dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                timestamp = int(dt_obj.timestamp())
                
                bar = Bar(
                    timestamp=timestamp,
                    open=float(row['do']),
                    high=float(row['dh']),
                    low=float(row['dl']),
                    close=float(row['dc']),
                    volume=float(row['dv']),
                    direction=int(row['dd'])
                )
                bars.append(bar)
        return bars
    
    def load_signals(self, json_path: Path) -> Dict:
        """
        신호 정의 로드
        
        Args:
            json_path: JSON 파일 경로
        
        Returns:
            신호 정의 딕셔너리
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_expected(self, json_path: Path) -> Dict:
        """
        기대 결과 로드
        
        Args:
            json_path: JSON 파일 경로
        
        Returns:
            기대 결과 딕셔너리
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_strategy_func(
        self, 
        signals: Dict
    ) -> callable:
        """
        신호 기반 전략 함수 생성
        
        Args:
            signals: 신호 정의
        
        Returns:
            전략 함수
        """
        # timestamp → signal 매핑
        signal_map = {}
        for signal in signals['signals']:
            signal_map[signal['timestamp']] = {
                'direction': signal['direction'],
                'stop_loss': signal['stop_loss']
            }
        
        def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
            """
            전략 함수
            
            Args:
                bar: 현재 봉
            
            Returns:
                신호 딕셔너리 또는 None
            """
            if bar.timestamp in signal_map:
                return signal_map[bar.timestamp]
            return None
        
        return strategy_func
    
    def test_data_a(self, test_data_dir: Path):
        """
        테스트 데이터 A 검증
        
        시나리오: 기본 롱 진입 → TP1 → BE 청산
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_A.csv')
        signals = self.load_signals(test_data_dir / 'test_data_A_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_A_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증: 거래 수
        assert len(trades) == expected['trades_count'], \
            f"거래 수가 일치하지 않습니다: {len(trades)} != {expected['trades_count']}"
        
        # 각 trade 검증
        for i, trade in enumerate(trades):
            expected_trade = expected['trades'][i]
            
            # trade_id
            assert trade.trade_id == expected_trade['trade_id'], \
                f"trade_id가 일치하지 않습니다: {trade.trade_id} != {expected_trade['trade_id']}"
            
            # direction
            assert trade.direction == expected_trade['direction'], \
                f"direction이 일치하지 않습니다: {trade.direction} != {expected_trade['direction']}"
            
            # entry_price
            assert trade.entry_price == expected_trade['entry_price'], \
                f"entry_price가 일치하지 않습니다: {trade.entry_price} != {expected_trade['entry_price']}"
            
            # entry_timestamp
            assert trade.entry_timestamp == expected_trade['entry_timestamp'], \
                f"entry_timestamp가 일치하지 않습니다: {trade.entry_timestamp} != {expected_trade['entry_timestamp']}"
            
            # legs 검증
            assert len(trade.legs) == expected_trade['legs_count'], \
                f"legs 수가 일치하지 않습니다: {len(trade.legs)} != {expected_trade['legs_count']}"
            
            for j, leg in enumerate(trade.legs):
                expected_leg = expected_trade['legs'][j]
                
                # exit_type
                assert leg.exit_type == expected_leg['exit_type'], \
                    f"leg {j}: exit_type이 일치하지 않습니다: {leg.exit_type} != {expected_leg['exit_type']}"
                
                # qty_ratio
                assert leg.qty_ratio == expected_leg['qty_ratio'], \
                    f"leg {j}: qty_ratio가 일치하지 않습니다: {leg.qty_ratio} != {expected_leg['qty_ratio']}"
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.win_rate == expected['metrics']['win_rate'], \
            f"win_rate가 일치하지 않습니다: {metrics.win_rate} != {expected['metrics']['win_rate']}"
        
        assert metrics.tp1_hit_rate == expected['metrics']['tp1_hit_rate'], \
            f"tp1_hit_rate가 일치하지 않습니다: {metrics.tp1_hit_rate} != {expected['metrics']['tp1_hit_rate']}"
        
        assert metrics.be_exit_rate == expected['metrics']['be_exit_rate'], \
            f"be_exit_rate가 일치하지 않습니다: {metrics.be_exit_rate} != {expected['metrics']['be_exit_rate']}"
    
    def test_data_b(self, test_data_dir: Path):
        """
        테스트 데이터 B 검증
        
        시나리오: 기본 숏 진입 → SL 청산
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_B.csv')
        signals = self.load_signals(test_data_dir / 'test_data_B_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_B_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증: 거래 수
        assert len(trades) == expected['trades_count'], \
            f"거래 수가 일치하지 않습니다: {len(trades)} != {expected['trades_count']}"
        
        # trade 검증
        trade = trades[0]
        expected_trade = expected['trades'][0]
        
        assert trade.direction == expected_trade['direction']
        assert trade.entry_price == expected_trade['entry_price']
        
        # legs 검증
        assert len(trade.legs) == expected_trade['legs_count']
        assert trade.legs[0].exit_type == expected_trade['legs'][0]['exit_type']
        assert trade.legs[0].qty_ratio == expected_trade['legs'][0]['qty_ratio']
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.win_rate == expected['metrics']['win_rate']
        assert metrics.tp1_hit_rate == expected['metrics']['tp1_hit_rate']
        assert metrics.be_exit_rate == expected['metrics']['be_exit_rate']
    
    def test_determinism(self, test_data_dir: Path):
        """
        결정성 테스트: 동일 입력 → 동일 출력
        
        동일한 bars와 strategy로 3번 실행했을 때
        모든 결과가 동일해야 함
        """
        bars = self.load_bars(test_data_dir / 'test_data_A.csv')
        signals = self.load_signals(test_data_dir / 'test_data_A_signals.json')
        strategy_func = self.create_strategy_func(signals)
        
        # 3번 실행
        results = []
        for _ in range(3):
            engine = BacktestEngine(
                initial_balance=10000,
                strategy_func=strategy_func
            )
            trades = engine.run(bars)
            results.append(trades)
        
        # 모든 결과가 동일한지 확인
        for i in range(len(results) - 1):
            # 거래 수 동일
            assert len(results[i]) == len(results[i + 1]), \
                "결정성 위반: 거래 수가 다릅니다"
            
            # 각 거래 검증
            for j in range(len(results[i])):
                trade1 = results[i][j]
                trade2 = results[i + 1][j]
                
                # entry_price 동일
                assert trade1.entry_price == trade2.entry_price, \
                    "결정성 위반: entry_price가 다릅니다"
                
                # entry_timestamp 동일
                assert trade1.entry_timestamp == trade2.entry_timestamp, \
                    "결정성 위반: entry_timestamp가 다릅니다"
                
                # PnL 동일
                assert trade1.calculate_total_pnl() == trade2.calculate_total_pnl(), \
                    "결정성 위반: total_pnl이 다릅니다"
                
                # legs 수 동일
                assert len(trade1.legs) == len(trade2.legs), \
                    "결정성 위반: legs 수가 다릅니다"
    
    def test_no_trades(self):
        """
        거래가 없는 경우 테스트
        
        신호가 없을 때 trades_count = 0
        """
        bars = [
            Bar(1704067200, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),
            Bar(1704067500, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
        ]
        
        # 신호가 없는 전략
        def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
            return None
        
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 거래가 없어야 함
        assert len(trades) == 0
        
        # Metrics 계산
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        # trades_count = 0인 경우 지표들이 0이어야 함
        assert metrics.trades_count == 0
        assert metrics.win_rate == 0.0
        assert metrics.tp1_hit_rate == 0.0
        assert metrics.be_exit_rate == 0.0
    
    def test_invalid_bars_empty(self):
        """빈 bars 리스트 테스트"""
        def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
            return None
        
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        
        # 빈 리스트는 에러 발생해야 함
        with pytest.raises(ValueError, match="bars가 비어있습니다"):
            engine.run([])
    
    def test_invalid_bars_not_sorted(self):
        """timestamp가 정렬되지 않은 bars 테스트"""
        bars = [
            Bar(1704067500, 103.0, 108.0, 102.0, 107.0, 1200.0, 1),
            Bar(1704067200, 100.0, 105.0, 99.0, 103.0, 1000.0, 1),  # 역순
        ]
        
        def strategy_func(bar: Bar) -> Optional[Dict[str, Any]]:
            return None
        
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        
        # timestamp 정렬 에러 발생해야 함
        with pytest.raises(ValueError, match="오름차순으로 정렬"):
            engine.run(bars)
    
    def test_data_c(self, test_data_dir: Path):
        """
        테스트 데이터 C 검증
        
        시나리오: 롱 진입 → TP1 → Reverse 청산 (TP1 이후 다른 봉에서)
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_C.csv')
        signals = self.load_signals(test_data_dir / 'test_data_C_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_C_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증: 거래 수
        assert len(trades) == expected['trades_count'], \
            f"거래 수가 일치하지 않습니다: {len(trades)} != {expected['trades_count']}"
        
        # trade 검증
        trade = trades[0]
        expected_trade = expected['trades'][0]
        
        assert trade.direction == expected_trade['direction']
        assert trade.entry_price == expected_trade['entry_price']
        
        # legs 검증
        assert len(trade.legs) == expected_trade['legs_count']
        assert trade.legs[0].exit_type == expected_trade['legs'][0]['exit_type']
        assert trade.legs[1].exit_type == expected_trade['legs'][1]['exit_type']
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.win_rate == expected['metrics']['win_rate']
        assert metrics.tp1_hit_rate == expected['metrics']['tp1_hit_rate']
        assert metrics.be_exit_rate == expected['metrics']['be_exit_rate']
    
    def test_data_d(self, test_data_dir: Path):
        """
        테스트 데이터 D 검증
        
        시나리오: 동일 봉에서 SL/TP1 동시 조건 (우선순위: SL 우선)
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_D.csv')
        signals = self.load_signals(test_data_dir / 'test_data_D_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_D_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증: 거래 수
        assert len(trades) == expected['trades_count']
        
        # trade 검증
        trade = trades[0]
        expected_trade = expected['trades'][0]
        
        assert trade.direction == expected_trade['direction']
        assert trade.entry_price == expected_trade['entry_price']
        
        # legs 검증 - SL 우선으로 처리되어야 함
        assert len(trade.legs) == expected_trade['legs_count']
        assert trade.legs[0].exit_type == 'SL', "SL이 TP1보다 우선해야 함"
        assert trade.legs[0].qty_ratio == 1.0, "전량 SL 청산이어야 함"
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.win_rate == expected['metrics']['win_rate']
        assert metrics.tp1_hit_rate == expected['metrics']['tp1_hit_rate']
    
    def test_data_e(self, test_data_dir: Path):
        """
        테스트 데이터 E 검증
        
        시나리오: TP1 발생 봉에서 Reverse 신호 무시 테스트
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_E.csv')
        signals = self.load_signals(test_data_dir / 'test_data_E_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_E_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증: 거래 수
        assert len(trades) == expected['trades_count']
        
        # trade 검증
        trade = trades[0]
        expected_trade = expected['trades'][0]
        
        assert trade.direction == expected_trade['direction']
        assert trade.entry_price == expected_trade['entry_price']
        
        # legs 검증
        assert len(trade.legs) == expected_trade['legs_count']
        assert trade.legs[0].exit_type == 'TP1'
        assert trade.legs[0].exit_timestamp == expected_trade['legs'][0]['exit_timestamp']
        assert trade.legs[1].exit_type == 'BE'
        assert trade.legs[1].exit_timestamp == expected_trade['legs'][1]['exit_timestamp']
        
        # TP1 발생 봉(1704067800)과 BE 청산 봉(1704068400)이 다름을 확인
        assert trade.legs[0].exit_timestamp != trade.legs[1].exit_timestamp, \
            "TP1 발생 봉에서 reverse 신호가 무시되어야 함"
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.tp1_hit_rate == expected['metrics']['tp1_hit_rate']
        assert metrics.be_exit_rate == expected['metrics']['be_exit_rate']
    
    def test_data_f(self, test_data_dir: Path):
        """
        테스트 데이터 F 검증
        
        시나리오: risk=0 진입 스킵 테스트
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_F.csv')
        signals = self.load_signals(test_data_dir / 'test_data_F_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_F_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 디버그: 경고 메시지 출력
        print(f"\n경고 메시지: {engine.warnings}")
        
        # 검증: 거래 수 (첫 번째 신호는 진입 조건 위반으로 스킵됨)
        assert len(trades) == expected['trades_count']
        
        # 경고 메시지 확인 (stop_loss 검증 또는 risk=0)
        assert len(engine.warnings) >= expected.get('warnings_count', 1), \
            f"경고가 발생해야 함. 실제 경고: {engine.warnings}"
        
        # trade 검증 (두 번째 신호로 진입)
        trade = trades[0]
        expected_trade = expected['trades'][0]
        
        assert trade.entry_price == expected_trade['entry_price']
        assert trade.entry_timestamp == expected_trade['entry_timestamp']
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.tp1_hit_rate == expected['metrics']['tp1_hit_rate']
    
    def test_data_g(self, test_data_dir: Path):
        """
        테스트 데이터 G 검증
        
        시나리오: 복합 시나리오 (여러 거래 + 다양한 청산 타입)
        """
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_G.csv')
        signals = self.load_signals(test_data_dir / 'test_data_G_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_G_expected.json')
        
        # 전략 함수 생성
        strategy_func = self.create_strategy_func(signals)
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증: 거래 수
        assert len(trades) == expected['trades_count'], \
            f"거래 수가 일치하지 않습니다: {len(trades)} != {expected['trades_count']}"
        
        # 각 trade 검증
        for i, trade in enumerate(trades):
            expected_trade = expected['trades'][i]
            
            assert trade.trade_id == expected_trade['trade_id']
            assert trade.direction == expected_trade['direction']
            assert trade.entry_price == expected_trade['entry_price']
            assert trade.entry_timestamp == expected_trade['entry_timestamp']
            
            # legs 검증
            assert len(trade.legs) == expected_trade['legs_count'], \
                f"trade {i+1}: legs 수가 일치하지 않습니다"
            
            for j, leg in enumerate(trade.legs):
                expected_leg = expected_trade['legs'][j]
                assert leg.exit_type == expected_leg['exit_type'], \
                    f"trade {i+1}, leg {j+1}: exit_type이 일치하지 않습니다"
                assert leg.qty_ratio == expected_leg['qty_ratio'], \
                    f"trade {i+1}, leg {j+1}: qty_ratio가 일치하지 않습니다"
        
        # Metrics 검증
        calculator = MetricsCalculator()
        metrics = calculator.calculate(trades)
        
        assert metrics.winning_trades == expected['metrics']['winning_trades']
        assert metrics.losing_trades == expected['metrics']['losing_trades']
        
        # float 비교 (소수점 오차 허용)
        assert abs(metrics.tp1_hit_rate - expected['metrics']['tp1_hit_rate']) < 0.001

