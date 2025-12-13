"""
데이터베이스 유틸리티 함수

이 모듈은 데이터베이스 작업을 위한 유틸리티 함수들을 제공합니다.
- 해시 계산 (dataset_hash, strategy_hash)
- CSV 파일 처리
- 데이터 검증
"""

import hashlib
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import json
from datetime import datetime
import pandas as pd

from engine.models.bar import Bar


def calculate_dataset_hash(bars: List[Bar]) -> str:
    """
    봉 데이터로부터 dataset_hash 계산
    
    결정성 보장:
    - 동일한 봉 데이터 → 동일한 해시
    - timestamp 오름차순 정렬 보장
    
    Args:
        bars: 봉 데이터 리스트
        
    Returns:
        str: SHA256 해시 (16진수 문자열)
    """
    # timestamp 오름차순 정렬
    sorted_bars = sorted(bars, key=lambda b: b.timestamp)
    
    # 모든 봉 데이터를 문자열로 결합
    data_str = ""
    for bar in sorted_bars:
        # 각 봉의 모든 필드를 문자열로 변환하여 결합
        data_str += f"{bar.timestamp},{bar.open},{bar.high},{bar.low},{bar.close},{bar.volume},{bar.direction}|"
    
    # SHA256 해시 계산
    hash_obj = hashlib.sha256(data_str.encode('utf-8'))
    return hash_obj.hexdigest()


def calculate_strategy_hash(definition: Dict[str, Any]) -> str:
    """
    전략 정의로부터 strategy_hash 계산
    
    결정성 보장:
    - 동일한 전략 정의 → 동일한 해시
    - JSON 직렬화 시 키 정렬
    
    Args:
        definition: 전략 정의 딕셔너리
        
    Returns:
        str: SHA256 해시 (16진수 문자열)
    """
    # JSON 직렬화 (키 정렬, ASCII 이스케이프 없음)
    json_str = json.dumps(definition, sort_keys=True, ensure_ascii=False)
    
    # SHA256 해시 계산
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    return hash_obj.hexdigest()


def load_bars_from_csv(file_path: str) -> Tuple[List[Bar], pd.DataFrame, Dict[str, Any]]:
    """
    CSV 파일에서 봉 데이터 로드
    
    CSV 형식:
    - 헤더: dt,do,dh,dl,dc,dv,dd
    - dt: UNIX timestamp (오름차순 정렬 필수)
    - do: 시가 (open)
    - dh: 고가 (high)
    - dl: 저가 (low)
    - dc: 종가 (close)
    - dv: 거래량 (volume)
    - dd: 봉 방향 (direction: 1=상승, -1=하락, 0=보합)
    
    Args:
        file_path: CSV 파일 경로
        
    Returns:
        Tuple[List[Bar], pd.DataFrame, Dict[str, Any]]: 
            (봉 데이터 리스트, OHLCV DataFrame, 메타데이터)
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        ValueError: CSV 형식이 잘못된 경우
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {file_path}")
    
    bars = []
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # 헤더 검증
        expected_headers = {'dt', 'do', 'dh', 'dl', 'dc', 'dv', 'dd'}
        if not expected_headers.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"CSV 헤더가 잘못되었습니다. "
                f"필요한 헤더: {expected_headers}, "
                f"실제 헤더: {reader.fieldnames}"
            )
        
        for row in reader:
            try:
                # dt를 datetime 문자열에서 UNIX timestamp로 변환
                # 형식: '2024-05-31 00:00:00'
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
            except (ValueError, KeyError) as e:
                raise ValueError(f"CSV 데이터 파싱 오류 (행 {len(bars) + 2}): {e}")
    
    if not bars:
        raise ValueError("CSV 파일에 데이터가 없습니다")
    
    # timestamp 오름차순 정렬
    bars.sort(key=lambda b: b.timestamp)
    
    # DataFrame 생성 (지표 계산을 위해)
    df = pd.DataFrame({
        'timestamp': [b.timestamp for b in bars],
        'open': [b.open for b in bars],
        'high': [b.high for b in bars],
        'low': [b.low for b in bars],
        'close': [b.close for b in bars],
        'volume': [b.volume for b in bars],
        'direction': [b.direction for b in bars]
    })
    
    # 메타데이터 계산
    metadata = {
        'bars_count': len(bars),
        'start_timestamp': bars[0].timestamp,
        'end_timestamp': bars[-1].timestamp,
    }
    
    return bars, df, metadata


def validate_bars(bars: List[Bar]) -> Tuple[bool, List[str]]:
    """
    봉 데이터 검증
    
    검증 항목:
    - timestamp 오름차순 정렬
    - timestamp 중복 없음
    - OHLC 관계 유효성 (Bar 모델에서 검증됨)
    
    Args:
        bars: 봉 데이터 리스트
        
    Returns:
        Tuple[bool, List[str]]: (검증 성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    if not bars:
        errors.append("봉 데이터가 비어있습니다")
        return False, errors
    
    # timestamp 오름차순 정렬 확인
    for i in range(len(bars) - 1):
        if bars[i].timestamp >= bars[i + 1].timestamp:
            errors.append(
                f"timestamp가 오름차순으로 정렬되지 않았습니다 "
                f"(index {i}: {bars[i].timestamp} >= "
                f"index {i+1}: {bars[i+1].timestamp})"
            )
    
    # timestamp 중복 확인
    timestamps = [bar.timestamp for bar in bars]
    unique_timestamps = set(timestamps)
    if len(timestamps) != len(unique_timestamps):
        errors.append("중복된 timestamp가 있습니다")
    
    return len(errors) == 0, errors


def save_bars_to_csv(bars: List[Bar], file_path: str) -> None:
    """
    봉 데이터를 CSV 파일로 저장
    
    Args:
        bars: 봉 데이터 리스트
        file_path: 저장할 CSV 파일 경로
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # timestamp 오름차순 정렬
    sorted_bars = sorted(bars, key=lambda b: b.timestamp)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 헤더 작성
        writer.writerow(['dt', 'do', 'dh', 'dl', 'dc', 'dv', 'dd'])
        
        # 데이터 작성
        for bar in sorted_bars:
            # timestamp를 datetime 문자열로 변환
            dt_str = datetime.fromtimestamp(bar.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([
                dt_str,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
                bar.direction
            ])


def create_strategy_definition(
    name: str,
    signals: List[Dict[str, Any]],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    전략 정의 딕셔너리 생성
    
    Args:
        name: 전략 이름
        signals: 신호 리스트
        description: 설명 (선택)
        
    Returns:
        Dict[str, Any]: 전략 정의 딕셔너리
    """
    return {
        'name': name,
        'description': description,
        'signals': signals
    }


def load_strategy_from_json(file_path: str) -> Dict[str, Any]:
    """
    JSON 파일에서 전략 정의 로드
    
    Args:
        file_path: JSON 파일 경로
        
    Returns:
        Dict[str, Any]: 전략 정의 딕셔너리
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        ValueError: JSON 형식이 잘못된 경우
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            definition = json.load(f)
        return definition
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 오류: {e}")


def save_strategy_to_json(definition: Dict[str, Any], file_path: str) -> None:
    """
    전략 정의를 JSON 파일로 저장
    
    Args:
        definition: 전략 정의 딕셔너리
        file_path: 저장할 JSON 파일 경로
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(definition, f, ensure_ascii=False, indent=2)

