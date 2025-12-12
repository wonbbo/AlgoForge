# AlgoForge 구현 가이드 v1.0

## 목차
1. [개발 철학 및 원칙](#1-개발-철학-및-원칙)
2. [프로젝트 구조](#2-프로젝트-구조)
3. [단계별 구현 순서](#3-단계별-구현-순서)
4. [Phase 1: 백테스트 엔진 핵심](#phase-1-백테스트-엔진-핵심-최우선)
5. [Phase 2: 테스트 데이터 및 검증](#phase-2-테스트-데이터-및-검증)
6. [Phase 3: 데이터베이스](#phase-3-데이터베이스)
7. [Phase 4: FastAPI 백엔드](#phase-4-fastapi-백엔드)
8. [Phase 5: Next.js 프론트엔드](#phase-5-nextjs-프론트엔드)
9. [Phase 6: 통합 및 배포](#phase-6-통합-및-배포)
10. [핵심 알고리즘 구현 가이드](#핵심-알고리즘-구현-가이드)
11. [테스트 데이터 사양](#테스트-데이터-사양)
12. [트러블슈팅 가이드](#트러블슈팅-가이드)

---

## 1. 개발 철학 및 원칙

### 1.1 백테스트 엔진 우선 개발 (Engine-First Strategy)

AlgoForge의 핵심 가치는 **결정적이고 재현 가능한 백테스트 결과**입니다. 따라서 개발은 반드시 백테스트 엔진부터 시작해야 합니다.

**Why Engine-First?**
- UI나 API는 엔진의 래퍼(wrapper)에 불과
- 엔진이 검증되지 않으면 나머지 개발은 무의미
- 테스트 데이터 A~G로 엔진 검증이 최우선

### 1.2 결정성(Deterministic) 보장 원칙

**절대 규칙**:
```
동일 입력 → 동일 출력 (항상)
dataset_hash + strategy_hash + engine_version = 동일 결과
```

**금지 사항**:
- ❌ 난수 사용 (`random`, `uuid`)
- ❌ 병렬 실행 (멀티스레드, 멀티프로세스)
- ❌ 시스템 시간 의존 (`datetime.now()`)
- ❌ 순서 보장 안 되는 자료구조 (dict 순회 시 정렬 필수)

**허용 사항**:
- ✅ Python 기본 float (floating point 계산)
- ✅ 오름차순 정렬된 timestamp 기준 처리
- ✅ 단일 스레드 순차 실행

### 1.3 테스트 주도 개발 (TDD)

```
1. 테스트 데이터 작성 (expected 결과 정의)
2. 테스트 케이스 작성
3. 구현
4. 테스트 통과
5. 리팩토링
```

**중요**: 테스트 실패 시 **구현을 수정**하지, 테스트를 수정하지 않습니다.

---

## 2. 프로젝트 구조

### 2.1 권장 폴더 구조

```
AlgoForge/
├─ engine/                    # 백테스트 엔진 (최우선 구현)
│  ├─ __init__.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ backtest_engine.py   # 메인 엔진
│  │  ├─ position_manager.py  # 포지션 관리
│  │  ├─ risk_manager.py      # 리스크 계산
│  │  └─ metrics_calculator.py # Metrics 계산
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ bar.py               # Bar 데이터 모델
│  │  ├─ position.py          # Position 모델
│  │  ├─ trade.py             # Trade 모델
│  │  └─ trade_leg.py         # TradeLeg 모델
│  └─ tests/
│     ├─ __init__.py
│     ├─ test_engine.py
│     ├─ test_position.py
│     └─ test_metrics.py
│
├─ apps/
│  ├─ api/                    # FastAPI 백엔드
│  │  ├─ main.py
│  │  ├─ routers/
│  │  │  ├─ datasets.py
│  │  │  ├─ strategies.py
│  │  │  └─ runs.py
│  │  ├─ models/
│  │  ├─ schemas/
│  │  └─ db/
│  │     ├─ database.py
│  │     └─ crud.py
│  │
│  └─ web/                    # Next.js 프론트엔드
│     ├─ app/
│     ├─ components/
│     ├─ lib/
│     └─ public/
│
├─ tests/
│  ├─ fixtures/               # 테스트 데이터 A~G
│  │  ├─ test_data_A.csv
│  │  ├─ test_data_A_signals.json
│  │  ├─ test_data_A_expected.json
│  │  ├─ test_data_B.csv
│  │  └─ ...
│  └─ integration/
│
├─ db/                        # SQLite 데이터베이스
│  └─ algoforge.db
│
├─ docs/                      # 문서
│  ├─ AlgoForge_PRD_v1.0.md
│  ├─ AlgoForge_TRD_v1.0.md
│  ├─ AlgoForge_ADR_v1.0.md
│  └─ AlgoForge_Implementation_Guide_v1.0.md
│
├─ .cursor/rules/             # Cursor AI 규칙
│  ├─ project-overview.mdc
│  ├─ architecture.mdc
│  ├─ backtest-engine-rules.mdc
│  ├─ trading-model-rules.mdc
│  ├─ code-quality.mdc
│  └─ nextjs-usage.mdc
│
├─ .gitignore
├─ requirements.txt           # Python 의존성
├─ pyproject.toml            # Python 프로젝트 설정
└─ README.md
```

### 2.2 환경 설정

**Python 환경**:
```bash
# Python 3.10+ 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**requirements.txt** (초기):
```txt
# 백테스트 엔진
pandas>=2.0.0
numpy>=1.24.0

# 테스트
pytest>=7.4.0
pytest-cov>=4.1.0

# API (Phase 4)
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0

# 타입 체크
mypy>=1.5.0
```

**Frontend 환경** (Phase 5):
```bash
cd apps/web
pnpm install
```

---

## 3. 단계별 구현 순서

### 개발 로드맵

```
Phase 1: 백테스트 엔진 핵심 (2-3주) ★★★★★
   ↓
Phase 2: 테스트 데이터 및 검증 (1주) ★★★★★
   ↓
Phase 3: 데이터베이스 (1주) ★★★
   ↓
Phase 4: FastAPI 백엔드 (1-2주) ★★★
   ↓
Phase 5: Next.js 프론트엔드 (2-3주) ★★
   ↓
Phase 6: 통합 및 배포 (1주) ★★
```

**중요도**:
- ★★★★★ = 필수 중의 필수 (MVP)
- ★★★ = MVP에 필요
- ★★ = MVP 이후 개선 가능

---

## Phase 1: 백테스트 엔진 핵심 (최우선)

### 목표
- 봉 단위 시뮬레이션 엔진 구현
- 결정적 결과 보장
- PRD/TRD의 모든 규칙 준수

### 1.1 데이터 모델 정의

**engine/models/bar.py**:
```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class Bar:
    """
    봉(Bar) 데이터 모델
    
    Attributes:
        timestamp: 봉의 시작 시간 (UNIX timestamp)
        open: 시가 (do)
        high: 고가 (dh)
        low: 저가 (dl)
        close: 종가 (dc)
        volume: 거래량 (dv)
        direction: 봉 방향 (dd: 1=상승, -1=하락, 0=보합)
    """
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    direction: int
```

**engine/models/position.py**:
```python
from dataclasses import dataclass
from typing import Literal, Optional

Direction = Literal['LONG', 'SHORT']

@dataclass
class Position:
    """
    포지션 모델
    
    Attributes:
        trade_id: 거래 ID
        direction: 포지션 방향 (LONG/SHORT)
        entry_price: 진입 가격
        entry_timestamp: 진입 시각
        position_size: 포지션 크기
        stop_loss: 손절가
        take_profit_1: 1차 익절가
        initial_risk: 초기 리스크
        tp1_hit: TP1 도달 여부
        tp1_occurred_this_bar: 현재 봉에서 TP1 발생 여부
    """
    trade_id: int
    direction: Direction
    entry_price: float
    entry_timestamp: int
    position_size: float
    stop_loss: float
    take_profit_1: float
    initial_risk: float
    tp1_hit: bool = False
    tp1_occurred_this_bar: bool = False
```

**engine/models/trade.py**:
```python
from dataclasses import dataclass, field
from typing import List, Literal
from .trade_leg import TradeLeg

Direction = Literal['LONG', 'SHORT']

@dataclass
class Trade:
    """
    거래(Trade) 모델
    
    하나의 trade는 진입부터 최종 종료까지의 전체 과정
    """
    trade_id: int
    direction: Direction
    entry_price: float
    entry_timestamp: int
    position_size: float
    initial_risk: float
    stop_loss: float
    take_profit_1: float
    
    # 거래 종료 정보
    legs: List[TradeLeg] = field(default_factory=list)
    is_closed: bool = False
    
    def add_leg(self, leg: TradeLeg) -> None:
        """trade_leg 추가"""
        self.legs.append(leg)
    
    def close_trade(self) -> None:
        """거래 종료 처리"""
        self.is_closed = True
    
    def calculate_total_pnl(self) -> float:
        """총 PnL 계산"""
        return sum(leg.pnl for leg in self.legs)
    
    def is_winning_trade(self) -> bool:
        """승리 거래 여부"""
        return self.calculate_total_pnl() > 0
    
    def has_tp1_hit(self) -> bool:
        """TP1 도달 여부"""
        return any(leg.exit_type == 'TP1' for leg in self.legs)
    
    def has_be_exit(self) -> bool:
        """BE 청산 여부"""
        return any(leg.exit_type == 'BE' for leg in self.legs)
```

**engine/models/trade_leg.py**:
```python
from dataclasses import dataclass
from typing import Literal

ExitType = Literal['SL', 'TP1', 'BE', 'REVERSE']

@dataclass
class TradeLeg:
    """
    거래 구간(Trade Leg) 모델
    
    하나의 trade는 최대 2개의 leg를 가짐:
    - TP1 leg (qty_ratio=0.5)
    - FINAL leg (잔여 수량)
    """
    trade_id: int
    exit_type: ExitType
    exit_timestamp: int
    exit_price: float
    qty_ratio: float  # 0~1 사이 값 (0.5 = 50%)
    pnl: float
```

### 1.2 리스크 관리 로직

**engine/core/risk_manager.py**:
```python
from typing import Optional, Tuple
from ..models.position import Position, Direction

class RiskManager:
    """리스크 관리 클래스"""
    
    def __init__(self, initial_balance: float, risk_percent: float = 0.02):
        """
        Args:
            initial_balance: 초기 자산
            risk_percent: 1 트레이드 최대 손실 비율 (기본 2%)
        """
        self.initial_balance = initial_balance
        self.risk_percent = risk_percent
        self.risk_reward_ratio = 1.5  # 고정값
    
    def calculate_position_size(
        self, 
        entry_price: float, 
        stop_loss: float
    ) -> Tuple[float, float]:
        """
        포지션 크기 계산
        
        Args:
            entry_price: 진입 가격
            stop_loss: 손절 가격
        
        Returns:
            (position_size, risk)
            
        Note:
            risk == 0 인 경우 position_size = 0 반환
        """
        # 리스크 계산
        risk = abs(entry_price - stop_loss)
        
        # risk가 0인 경우 처리 (division by zero 방지)
        if risk == 0:
            return 0.0, 0.0
        
        # 포지션 크기 계산: (초기 자산 * 2%) / 리스크
        position_size = (self.initial_balance * self.risk_percent) / risk
        
        return position_size, risk
    
    def calculate_tp1_price(
        self, 
        entry_price: float, 
        stop_loss: float, 
        direction: Direction
    ) -> float:
        """
        TP1 가격 계산
        
        Args:
            entry_price: 진입 가격
            stop_loss: 손절 가격
            direction: 포지션 방향
        
        Returns:
            TP1 가격
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * self.risk_reward_ratio
        
        if direction == 'LONG':
            return entry_price + reward
        else:  # SHORT
            return entry_price - reward
    
    def move_sl_to_be(self, position: Position) -> None:
        """
        손절가를 진입가(BE)로 이동
        
        Args:
            position: 현재 포지션
        """
        position.stop_loss = position.entry_price
        position.tp1_hit = True
```

### 1.3 봉 처리 엔진

**engine/core/backtest_engine.py**:
```python
from typing import List, Optional, Callable, Literal
from ..models.bar import Bar
from ..models.position import Position, Direction
from ..models.trade import Trade
from ..models.trade_leg import TradeLeg, ExitType
from .risk_manager import RiskManager

class BacktestEngine:
    """
    백테스트 엔진
    
    봉 단위 시뮬레이션 기반의 결정적(deterministic) 백테스트 엔진
    """
    
    def __init__(
        self, 
        initial_balance: float,
        strategy_func: Callable[[Bar], Optional[Direction]]
    ):
        """
        Args:
            initial_balance: 초기 자산
            strategy_func: 전략 함수 (Bar -> 'LONG' | 'SHORT' | None)
        """
        self.initial_balance = initial_balance
        self.strategy_func = strategy_func
        self.risk_manager = RiskManager(initial_balance)
        
        # 상태 관리
        self.current_position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.trade_id_counter = 1
        
        # 경고 메시지 저장
        self.warnings: List[str] = []
    
    def run(self, bars: List[Bar]) -> List[Trade]:
        """
        백테스트 실행
        
        Args:
            bars: 봉 데이터 리스트 (timestamp 오름차순 정렬 필수)
        
        Returns:
            거래 목록
        """
        # 입력 검증
        if not bars:
            raise ValueError("bars가 비어있습니다")
        
        # timestamp 오름차순 정렬 확인
        for i in range(len(bars) - 1):
            if bars[i].timestamp >= bars[i + 1].timestamp:
                raise ValueError("bars는 timestamp 오름차순으로 정렬되어야 합니다")
        
        # 봉 단위 처리
        for bar in bars:
            self._process_bar(bar)
        
        return self.trades
    
    def _process_bar(self, bar: Bar) -> None:
        """
        봉 처리 (핵심 로직)
        
        처리 순서:
        1. 기존 포지션 관리
        2. SL / TP1 / Reverse 판정
        3. 포지션 종료 처리
        4. 신규 진입 판정
        """
        # 1. 기존 포지션이 있는 경우
        if self.current_position:
            # TP1 발생 플래그 초기화 (새로운 봉 시작)
            self.current_position.tp1_occurred_this_bar = False
            
            # 2. SL / TP1 / Reverse 판정 (우선순위 적용)
            exit_type = self._check_exit_conditions(bar)
            
            # 3. 포지션 종료 처리
            if exit_type:
                self._close_position(bar, exit_type)
        
        # 4. 신규 진입 판정 (포지션이 없을 때만)
        if not self.current_position:
            self._check_entry_signal(bar)
    
    def _check_exit_conditions(self, bar: Bar) -> Optional[ExitType]:
        """
        청산 조건 체크
        
        우선순위:
        1. Stop Loss
        2. TP1
        3. Reverse Signal
        
        Returns:
            청산 타입 또는 None
        """
        pos = self.current_position
        if not pos:
            return None
        
        # 1. Stop Loss 체크 (최우선)
        if self._check_stop_loss(bar, pos):
            return 'SL'
        
        # 2. TP1 체크
        if not pos.tp1_hit and self._check_tp1(bar, pos):
            # TP1 발생 처리
            self._handle_tp1(bar, pos)
            # TP1은 부분 청산이므로 계속 진행
            # (FINAL 종료는 아님)
            return None
        
        # 3. Reverse Signal 체크
        # TP1 발생 봉에서는 reverse 평가 안 함
        if not pos.tp1_occurred_this_bar:
            if self._check_reverse_signal(bar, pos):
                # TP1 후 잔여 포지션이면 BE 청산
                if pos.tp1_hit:
                    return 'BE'
                else:
                    return 'REVERSE'
        
        return None
    
    def _check_stop_loss(self, bar: Bar, pos: Position) -> bool:
        """SL 도달 여부 체크"""
        if pos.direction == 'LONG':
            # 롱: 저가가 SL 이하
            return bar.low <= pos.stop_loss
        else:  # SHORT
            # 숏: 고가가 SL 이상
            return bar.high >= pos.stop_loss
    
    def _check_tp1(self, bar: Bar, pos: Position) -> bool:
        """TP1 도달 여부 체크"""
        if pos.direction == 'LONG':
            # 롱: 고가가 TP1 이상
            return bar.high >= pos.take_profit_1
        else:  # SHORT
            # 숏: 저가가 TP1 이하
            return bar.low <= pos.take_profit_1
    
    def _handle_tp1(self, bar: Bar, pos: Position) -> None:
        """
        TP1 처리
        
        1. 50% 부분 청산
        2. SL을 BE로 이동
        3. 플래그 설정
        """
        # 현재 trade 가져오기
        current_trade = next(
            (t for t in self.trades if t.trade_id == pos.trade_id), 
            None
        )
        if not current_trade:
            return
        
        # 1. TP1 leg 생성 (50% 청산)
        qty_ratio = 0.5
        pnl = self._calculate_pnl(
            pos.entry_price, 
            bar.close,  # Close Fill
            pos.direction, 
            pos.position_size * qty_ratio
        )
        
        tp1_leg = TradeLeg(
            trade_id=pos.trade_id,
            exit_type='TP1',
            exit_timestamp=bar.timestamp,
            exit_price=bar.close,
            qty_ratio=qty_ratio,
            pnl=pnl
        )
        current_trade.add_leg(tp1_leg)
        
        # 2. SL을 BE로 이동
        self.risk_manager.move_sl_to_be(pos)
        
        # 3. 플래그 설정 (이 봉에서는 reverse 평가 안 함)
        pos.tp1_occurred_this_bar = True
    
    def _check_reverse_signal(self, bar: Bar, pos: Position) -> bool:
        """반대 방향 신호 체크"""
        signal = self.strategy_func(bar)
        
        if signal is None:
            return False
        
        # 반대 방향인지 체크
        if pos.direction == 'LONG' and signal == 'SHORT':
            return True
        elif pos.direction == 'SHORT' and signal == 'LONG':
            return True
        
        return False
    
    def _close_position(self, bar: Bar, exit_type: ExitType) -> None:
        """
        포지션 종료 처리
        
        FINAL leg 생성 및 trade 종료
        """
        pos = self.current_position
        if not pos:
            return
        
        # 현재 trade 가져오기
        current_trade = next(
            (t for t in self.trades if t.trade_id == pos.trade_id), 
            None
        )
        if not current_trade:
            return
        
        # 잔여 수량 계산
        # TP1이 발생했으면 50%, 아니면 100%
        remaining_qty_ratio = 0.5 if pos.tp1_hit else 1.0
        
        # FINAL leg 생성
        pnl = self._calculate_pnl(
            pos.entry_price,
            bar.close,  # Close Fill
            pos.direction,
            pos.position_size * remaining_qty_ratio
        )
        
        final_leg = TradeLeg(
            trade_id=pos.trade_id,
            exit_type=exit_type,
            exit_timestamp=bar.timestamp,
            exit_price=bar.close,
            qty_ratio=remaining_qty_ratio,
            pnl=pnl
        )
        current_trade.add_leg(final_leg)
        current_trade.close_trade()
        
        # 포지션 초기화
        self.current_position = None
    
    def _check_entry_signal(self, bar: Bar) -> None:
        """신규 진입 신호 체크 및 처리"""
        signal = self.strategy_func(bar)
        
        if signal is None:
            return
        
        # 포지션 진입 (Close Fill)
        self._enter_position(bar, signal)
    
    def _enter_position(self, bar: Bar, direction: Direction) -> None:
        """
        포지션 진입
        
        Args:
            bar: 현재 봉
            direction: 진입 방향
        """
        entry_price = bar.close  # Close Fill
        
        # 임시 SL 계산 (전략에서 제공되어야 하지만, 여기서는 단순화)
        # 실제로는 strategy_func에서 SL도 함께 반환해야 함
        # 임시로 2% SL 사용
        if direction == 'LONG':
            stop_loss = entry_price * 0.98
        else:  # SHORT
            stop_loss = entry_price * 1.02
        
        # 포지션 크기 계산
        position_size, risk = self.risk_manager.calculate_position_size(
            entry_price, 
            stop_loss
        )
        
        # risk == 0 인 경우 진입 스킵
        if risk == 0:
            self.warnings.append(
                f"timestamp={bar.timestamp}: risk=0이므로 진입 스킵"
            )
            return
        
        # TP1 계산
        tp1_price = self.risk_manager.calculate_tp1_price(
            entry_price, 
            stop_loss, 
            direction
        )
        
        # Position 생성
        position = Position(
            trade_id=self.trade_id_counter,
            direction=direction,
            entry_price=entry_price,
            entry_timestamp=bar.timestamp,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit_1=tp1_price,
            initial_risk=risk
        )
        self.current_position = position
        
        # Trade 생성
        trade = Trade(
            trade_id=self.trade_id_counter,
            direction=direction,
            entry_price=entry_price,
            entry_timestamp=bar.timestamp,
            position_size=position_size,
            initial_risk=risk,
            stop_loss=stop_loss,
            take_profit_1=tp1_price
        )
        self.trades.append(trade)
        
        # trade_id 증가
        self.trade_id_counter += 1
    
    def _calculate_pnl(
        self, 
        entry_price: float, 
        exit_price: float, 
        direction: Direction, 
        position_size: float
    ) -> float:
        """
        PnL 계산
        
        Args:
            entry_price: 진입 가격
            exit_price: 청산 가격
            direction: 방향
            position_size: 포지션 크기
        
        Returns:
            PnL
        """
        if direction == 'LONG':
            return (exit_price - entry_price) * position_size
        else:  # SHORT
            return (entry_price - exit_price) * position_size
```

### 1.4 Metrics 계산 엔진

**engine/core/metrics_calculator.py**:
```python
from typing import List
from dataclasses import dataclass
from ..models.trade import Trade

@dataclass
class Metrics:
    """성과 지표"""
    trades_count: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    tp1_hit_rate: float
    be_exit_rate: float
    total_pnl: float
    average_pnl: float
    profit_factor: float
    max_drawdown: float
    score: float
    grade: str

class MetricsCalculator:
    """Metrics 계산 클래스"""
    
    def calculate(self, trades: List[Trade]) -> Metrics:
        """
        거래 목록으로부터 성과 지표를 계산합니다.
        
        Args:
            trades: 거래 목록
        
        Returns:
            Metrics 객체
        
        Note:
            trades_count가 0인 경우:
            - win_rate = 0
            - tp1_hit_rate = 0
            - be_exit_rate = 0
        """
        trades_count = len(trades)
        
        # trades가 없는 경우
        if trades_count == 0:
            return Metrics(
                trades_count=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                tp1_hit_rate=0,
                be_exit_rate=0,
                total_pnl=0,
                average_pnl=0,
                profit_factor=0,
                max_drawdown=0,
                score=0,
                grade='D'
            )
        
        # 기본 통계
        winning_trades = sum(1 for t in trades if t.is_winning_trade())
        losing_trades = trades_count - winning_trades
        win_rate = winning_trades / trades_count
        
        # TP1 hit rate
        tp1_hit_trades = sum(1 for t in trades if t.has_tp1_hit())
        tp1_hit_rate = tp1_hit_trades / trades_count
        
        # BE exit rate
        be_exit_trades = sum(1 for t in trades if t.has_be_exit())
        be_exit_rate = be_exit_trades / trades_count
        
        # PnL 계산
        total_pnl = sum(t.calculate_total_pnl() for t in trades)
        average_pnl = total_pnl / trades_count
        
        # Profit Factor
        total_profit = sum(
            t.calculate_total_pnl() for t in trades 
            if t.calculate_total_pnl() > 0
        )
        total_loss = abs(sum(
            t.calculate_total_pnl() for t in trades 
            if t.calculate_total_pnl() <= 0
        ))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # Max Drawdown (간단 버전)
        max_drawdown = self._calculate_max_drawdown(trades)
        
        # Score 계산
        score = self._calculate_score(
            win_rate, 
            tp1_hit_rate, 
            profit_factor, 
            max_drawdown
        )
        
        # Grade 매핑
        grade = self._get_grade(score)
        
        return Metrics(
            trades_count=trades_count,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            tp1_hit_rate=tp1_hit_rate,
            be_exit_rate=be_exit_rate,
            total_pnl=total_pnl,
            average_pnl=average_pnl,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            score=score,
            grade=grade
        )
    
    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """최대 낙폭 계산"""
        if not trades:
            return 0
        
        cumulative_pnl = 0
        peak = 0
        max_dd = 0
        
        for trade in trades:
            cumulative_pnl += trade.calculate_total_pnl()
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            dd = peak - cumulative_pnl
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_score(
        self, 
        win_rate: float, 
        tp1_hit_rate: float, 
        profit_factor: float, 
        max_drawdown: float
    ) -> float:
        """
        전략 점수 계산 (0~100)
        
        가중치:
        - win_rate: 30%
        - tp1_hit_rate: 20%
        - profit_factor: 30%
        - max_drawdown: 20%
        """
        # 정규화
        win_rate_score = win_rate * 100
        tp1_hit_rate_score = tp1_hit_rate * 100
        profit_factor_score = min(profit_factor * 20, 100)  # PF 5 이상은 100점
        
        # Max DD는 낮을수록 좋음 (간단 처리)
        dd_score = max(100 - max_drawdown / 10, 0)
        
        # 가중 평균
        score = (
            win_rate_score * 0.3 +
            tp1_hit_rate_score * 0.2 +
            profit_factor_score * 0.3 +
            dd_score * 0.2
        )
        
        return round(score, 2)
    
    def _get_grade(self, score: float) -> str:
        """점수에 따른 등급 반환"""
        if score >= 85:
            return 'S'
        elif score >= 70:
            return 'A'
        elif score >= 55:
            return 'B'
        elif score >= 40:
            return 'C'
        else:
            return 'D'
```

### 1.5 Phase 1 체크리스트

구현 완료 후 다음 항목들을 확인하세요:

- [ ] 모든 데이터 모델 정의 완료 (Bar, Position, Trade, TradeLeg)
- [ ] 봉 처리 순서 준수 (포지션 관리 → 청산 판정 → 신규 진입)
- [ ] 우선순위 규칙 구현 (SL > TP1 > Reverse)
- [ ] TP1 처리 로직 구현 (50% 청산, SL→BE, 플래그 설정)
- [ ] Reverse Signal 평가 스킵 구현 (TP1 발생 봉)
- [ ] risk==0 처리 (진입 스킵, warning 기록)
- [ ] Type Hints 모두 적용
- [ ] 한글 주석 작성
- [ ] 에러 처리 완료

---

## Phase 2: 테스트 데이터 및 검증

### 목표
- 테스트 데이터 A~G 생성
- 단위 테스트 작성
- 엔진 결정성 검증

### 2.1 테스트 데이터 구조

각 테스트 데이터는 3개 파일로 구성:

1. **test_data_X.csv**: 봉 데이터
2. **test_data_X_signals.json**: 신호 정의
3. **test_data_X_expected.json**: 기대 결과

**예: test_data_A.csv**:
```csv
dt,do,dh,dl,dc,dv,dd
1704067200,100,105,99,103,1000,1
1704067500,103,108,102,107,1200,1
1704067800,107,107,100,101,1500,-1
1704068100,101,104,98,99,1100,-1
...
```

**test_data_A_signals.json**:
```json
{
  "strategy_name": "Simple EMA Cross",
  "signals": [
    {
      "timestamp": 1704067200,
      "direction": "LONG",
      "stop_loss": 98
    },
    {
      "timestamp": 1704068100,
      "direction": "SHORT",
      "stop_loss": 102
    }
  ]
}
```

**test_data_A_expected.json**:
```json
{
  "trades_count": 2,
  "trades": [
    {
      "trade_id": 1,
      "direction": "LONG",
      "entry_price": 103,
      "entry_timestamp": 1704067200,
      "legs": [
        {
          "exit_type": "TP1",
          "exit_price": 107,
          "qty_ratio": 0.5
        },
        {
          "exit_type": "BE",
          "exit_price": 103,
          "qty_ratio": 0.5
        }
      ]
    }
  ],
  "metrics": {
    "win_rate": 0.5,
    "tp1_hit_rate": 0.5
  }
}
```

### 2.2 단위 테스트 작성

**engine/tests/test_engine.py**:
```python
import pytest
import json
import csv
from pathlib import Path
from engine.core.backtest_engine import BacktestEngine
from engine.models.bar import Bar
from typing import Optional, List, Dict

class TestBacktestEngine:
    """백테스트 엔진 테스트"""
    
    @pytest.fixture
    def test_data_dir(self) -> Path:
        """테스트 데이터 디렉토리"""
        return Path(__file__).parent.parent.parent / 'tests' / 'fixtures'
    
    def load_bars(self, csv_path: Path) -> List[Bar]:
        """CSV에서 Bar 데이터 로드"""
        bars = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bar = Bar(
                    timestamp=int(row['dt']),
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
        """신호 정의 로드"""
        with open(json_path, 'r') as f:
            return json.load(f)
    
    def load_expected(self, json_path: Path) -> Dict:
        """기대 결과 로드"""
        with open(json_path, 'r') as f:
            return json.load(f)
    
    def test_data_a(self, test_data_dir: Path):
        """테스트 데이터 A 검증"""
        # 데이터 로드
        bars = self.load_bars(test_data_dir / 'test_data_A.csv')
        signals = self.load_signals(test_data_dir / 'test_data_A_signals.json')
        expected = self.load_expected(test_data_dir / 'test_data_A_expected.json')
        
        # 전략 함수 생성 (신호 기반)
        signal_map = {s['timestamp']: s for s in signals['signals']}
        def strategy_func(bar: Bar) -> Optional[str]:
            if bar.timestamp in signal_map:
                return signal_map[bar.timestamp]['direction']
            return None
        
        # 엔진 실행
        engine = BacktestEngine(
            initial_balance=10000,
            strategy_func=strategy_func
        )
        trades = engine.run(bars)
        
        # 검증
        assert len(trades) == expected['trades_count']
        
        # 각 trade 검증
        for i, trade in enumerate(trades):
            expected_trade = expected['trades'][i]
            assert trade.trade_id == expected_trade['trade_id']
            assert trade.direction == expected_trade['direction']
            assert trade.entry_price == expected_trade['entry_price']
            
            # legs 검증
            assert len(trade.legs) == len(expected_trade['legs'])
            for j, leg in enumerate(trade.legs):
                expected_leg = expected_trade['legs'][j]
                assert leg.exit_type == expected_leg['exit_type']
                assert leg.qty_ratio == expected_leg['qty_ratio']
    
    def test_determinism(self, test_data_dir: Path):
        """결정성 테스트: 동일 입력 → 동일 출력"""
        bars = self.load_bars(test_data_dir / 'test_data_A.csv')
        signals = self.load_signals(test_data_dir / 'test_data_A_signals.json')
        
        signal_map = {s['timestamp']: s for s in signals['signals']}
        def strategy_func(bar: Bar) -> Optional[str]:
            if bar.timestamp in signal_map:
                return signal_map[bar.timestamp]['direction']
            return None
        
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
            assert len(results[i]) == len(results[i + 1])
            for j in range(len(results[i])):
                trade1 = results[i][j]
                trade2 = results[i + 1][j]
                assert trade1.entry_price == trade2.entry_price
                assert trade1.calculate_total_pnl() == trade2.calculate_total_pnl()
    
    def test_tp1_reverse_skip(self):
        """TP1 발생 봉에서 reverse 평가 스킵 테스트"""
        # 특수 시나리오 테스트
        # TP1 도달 봉에서 반대 신호가 있어도 무시해야 함
        pass  # 구체적 구현 필요
```

### 2.3 Phase 2 체크리스트

- [ ] 테스트 데이터 A~G 모두 생성
- [ ] 각 테스트 데이터에 대한 단위 테스트 작성
- [ ] 결정성 테스트 통과 (3회 실행 동일 결과)
- [ ] Edge case 테스트 작성 (risk=0, TP1 후 reverse 등)
- [ ] 모든 테스트 통과
- [ ] 코드 커버리지 80% 이상

---

## Phase 3: 데이터베이스

### 목표
- SQLite 스키마 설계
- DDL 작성
- CRUD 로직 구현

### 3.1 데이터베이스 스키마

**db/schema.sql**:
```sql
-- WAL mode 활성화
PRAGMA journal_mode=WAL;

-- datasets 테이블
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    timeframe TEXT NOT NULL DEFAULT '5m',
    dataset_hash TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    bars_count INTEGER NOT NULL,
    start_timestamp INTEGER NOT NULL,
    end_timestamp INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

-- strategies 테이블
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    strategy_hash TEXT NOT NULL,
    definition TEXT NOT NULL,  -- JSON
    created_at INTEGER NOT NULL
);

-- runs 테이블
CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    status TEXT NOT NULL,  -- PENDING, RUNNING, COMPLETED, FAILED
    engine_version TEXT NOT NULL,
    initial_balance REAL NOT NULL,
    started_at INTEGER,
    completed_at INTEGER,
    run_artifacts TEXT,  -- JSON (warnings 등)
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- trades 테이블
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    direction TEXT NOT NULL,  -- LONG, SHORT
    entry_timestamp INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    position_size REAL NOT NULL,
    initial_risk REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit_1 REAL NOT NULL,
    is_closed INTEGER NOT NULL DEFAULT 0,
    total_pnl REAL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- trade_legs 테이블
CREATE TABLE IF NOT EXISTS trade_legs (
    leg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    exit_type TEXT NOT NULL,  -- SL, TP1, BE, REVERSE
    exit_timestamp INTEGER NOT NULL,
    exit_price REAL NOT NULL,
    qty_ratio REAL NOT NULL,
    pnl REAL NOT NULL,
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
);

-- metrics 테이블
CREATE TABLE IF NOT EXISTS metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL UNIQUE,
    trades_count INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    tp1_hit_rate REAL NOT NULL,
    be_exit_rate REAL NOT NULL,
    total_pnl REAL NOT NULL,
    average_pnl REAL NOT NULL,
    profit_factor REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    score REAL NOT NULL,
    grade TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- 인덱스
CREATE INDEX idx_runs_dataset ON runs(dataset_id);
CREATE INDEX idx_runs_strategy ON runs(strategy_id);
CREATE INDEX idx_trades_run ON trades(run_id);
CREATE INDEX idx_trade_legs_trade ON trade_legs(trade_id);
```

### 3.2 데이터베이스 연결

**apps/api/db/database.py**:
```python
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

class Database:
    """SQLite 데이터베이스 관리"""
    
    def __init__(self, db_path: str = "db/algoforge.db"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self) -> None:
        """데이터베이스 파일 및 스키마 생성"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 스키마 적용
        schema_path = Path(__file__).parent.parent.parent.parent / 'db' / 'schema.sql'
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
```

### 3.3 Phase 3 체크리스트

- [ ] 스키마 설계 완료
- [ ] DDL 작성 및 테스트
- [ ] 데이터베이스 연결 클래스 구현
- [ ] CRUD 로직 구현
- [ ] 트랜잭션 처리 구현
- [ ] 마이그레이션 스크립트 작성

---

## Phase 4: FastAPI 백엔드

### 목표
- RESTful API 엔드포인트 구현
- 엔진 통합
- 비동기 Run 실행

### 4.1 API 구조

**apps/api/main.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import datasets, strategies, runs

app = FastAPI(title="AlgoForge API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])

@app.get("/")
def root():
    return {"message": "AlgoForge API v1.0"}
```

### 4.2 주요 엔드포인트

**Dataset 관리**:
- `POST /api/datasets` - 데이터셋 업로드
- `GET /api/datasets` - 데이터셋 목록 조회
- `GET /api/datasets/{dataset_id}` - 데이터셋 상세 조회

**Strategy 관리**:
- `POST /api/strategies` - 전략 등록
- `GET /api/strategies` - 전략 목록 조회
- `GET /api/strategies/{strategy_id}` - 전략 상세 조회

**Run 실행**:
- `POST /api/runs` - Run 생성 및 실행 트리거
- `GET /api/runs/{run_id}` - Run 상태 조회
- `GET /api/runs/{run_id}/trades` - 거래 내역 조회
- `GET /api/runs/{run_id}/metrics` - Metrics 조회

### 4.3 Phase 4 체크리스트

- [ ] FastAPI 프로젝트 설정
- [ ] API 엔드포인트 구현
- [ ] 엔진 통합
- [ ] Background Task로 Run 실행
- [ ] 에러 핸들링
- [ ] API 문서화 (OpenAPI)

---

## Phase 5: Next.js 프론트엔드

### 목표
- 전략 빌더 UI
- 결과 시각화
- 대시보드

### 5.1 주요 페이지

```
/                    # 대시보드
/datasets            # 데이터셋 관리
/strategies          # 전략 관리
/strategies/builder  # 전략 빌더
/runs                # Run 목록
/runs/[id]           # Run 상세 (차트, Metrics)
```

### 5.2 Phase 5 체크리스트

- [ ] Next.js 프로젝트 설정
- [ ] ShadCN 설치 및 설정
- [ ] 주요 페이지 구현
- [ ] 전략 빌더 구현
- [ ] TradingView Charts 통합
- [ ] API 연동

---

## Phase 6: 통합 및 배포

### 목표
- End-to-End 테스트
- 성능 최적화
- 문서화

### 6.1 Phase 6 체크리스트

- [ ] E2E 테스트 작성
- [ ] 성능 프로파일링
- [ ] 병목 지점 최적화
- [ ] 사용자 매뉴얼 작성
- [ ] README 업데이트
- [ ] 배포 스크립트 작성

---

## 핵심 알고리즘 구현 가이드

### 봉 처리 순서 (의사코드)

```python
for bar in sorted_bars:
    # 1. 기존 포지션이 있는 경우
    if current_position:
        # TP1 플래그 초기화
        current_position.tp1_occurred_this_bar = False
        
        # 2. 청산 조건 체크 (우선순위)
        if check_stop_loss(bar):
            close_position(bar, 'SL')
        elif not tp1_hit and check_tp1(bar):
            handle_tp1(bar)  # 50% 청산, SL→BE, 플래그 설정
        elif not tp1_occurred_this_bar and check_reverse(bar):
            if tp1_hit:
                close_position(bar, 'BE')
            else:
                close_position(bar, 'REVERSE')
    
    # 3. 신규 진입 (포지션 없을 때만)
    if not current_position:
        signal = strategy_func(bar)
        if signal:
            enter_position(bar, signal)
```

### TP1 처리 상세

```python
def handle_tp1(bar, position):
    # 1. TP1 leg 생성 (50% 청산)
    qty_ratio = 0.5
    pnl = calculate_pnl(
        position.entry_price,
        bar.close,  # Close Fill!
        position.direction,
        position.position_size * qty_ratio
    )
    
    tp1_leg = TradeLeg(
        trade_id=position.trade_id,
        exit_type='TP1',
        exit_timestamp=bar.timestamp,
        exit_price=bar.close,
        qty_ratio=qty_ratio,
        pnl=pnl
    )
    current_trade.add_leg(tp1_leg)
    
    # 2. SL을 BE로 이동
    position.stop_loss = position.entry_price
    position.tp1_hit = True
    
    # 3. 플래그 설정 (이 봉에서 reverse 평가 안 함)
    position.tp1_occurred_this_bar = True
```

---

## 테스트 데이터 사양

### 테스트 데이터 A~G 시나리오

**Test A**: 기본 롱 진입 → TP1 → BE 청산
**Test B**: 기본 숏 진입 → SL 청산
**Test C**: 롱 진입 → TP1 → Reverse 청산
**Test D**: 동일 봉에서 SL/TP1 동시 조건 (우선순위 테스트)
**Test E**: TP1 발생 봉에서 Reverse 신호 (스킵 테스트)
**Test F**: risk=0 진입 스킵
**Test G**: 복합 시나리오 (여러 거래)

각 테스트는 **명확한 기대 결과**를 가져야 하며, 엔진이 이를 정확히 재현해야 합니다.

---

## 트러블슈팅 가이드

### 1. Floating Point 불일치

**문제**: 동일 입력인데 미세하게 다른 결과
**원인**: Floating point 계산 순서 차이
**해결**:
```python
# 나쁜 예
result = a + b + c + d  # 순서에 따라 미세한 차이

# 좋은 예
result = sum([a, b, c, d])  # 일관된 순서
```

### 2. 순서 보장 문제

**문제**: dict 순회 시 순서가 달라짐
**원인**: Python 3.7+ 이전 버전 또는 다른 환경
**해결**:
```python
# 나쁜 예
for key in my_dict:
    process(key)

# 좋은 예
for key in sorted(my_dict.keys()):
    process(key)
```

### 3. TP1 후 Reverse 처리

**문제**: TP1 발생 봉에서 reverse 신호가 처리됨
**원인**: 플래그 설정 누락
**해결**:
```python
# TP1 처리 시
position.tp1_occurred_this_bar = True

# 봉 시작 시 초기화
position.tp1_occurred_this_bar = False

# Reverse 체크 시
if not position.tp1_occurred_this_bar:
    check_reverse_signal()
```

### 4. Risk = 0 처리

**문제**: division by zero 에러
**원인**: entry_price == stop_loss
**해결**:
```python
risk = abs(entry_price - stop_loss)
if risk == 0:
    # 진입 스킵
    warnings.append("risk=0, 진입 스킵")
    return
```

---

## 마치며

이 가이드는 AlgoForge 프로젝트의 체계적인 구현을 위한 로드맵입니다.

**핵심 원칙**:
1. 엔진 우선 개발
2. 결정성 보장
3. 테스트 주도 개발

**개발 시작 순서**:
```
1. engine/models/ 정의
2. engine/core/risk_manager.py
3. engine/core/backtest_engine.py
4. engine/core/metrics_calculator.py
5. tests/fixtures/ 생성
6. engine/tests/ 작성
```

PRD/TRD의 규칙을 절대 위반하지 말고, 테스트 데이터 A~G를 모두 통과할 때까지 엔진을 개선하세요.

**Good Luck!** 🚀

