"""
Run 실행 테스트 스크립트

SimpleEMA 전략으로 Run을 생성하고 실행하여 결과를 확인합니다.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_run_execution():
    """Run 실행 테스트"""
    
    print("=" * 60)
    print("Run 실행 테스트 시작")
    print("=" * 60)
    
    # 1. 전략 목록 조회
    print("\n1. 전략 목록 조회...")
    response = requests.get(f"{BASE_URL}/strategies")
    if response.status_code != 200:
        print(f"전략 조회 실패: {response.status_code}")
        return
    
    result = response.json()
    strategies = result.get("data", result.get("strategies", []))
    print(f"전략 {len(strategies)}개 발견")
    
    if not strategies:
        print("전략이 없습니다. 먼저 전략을 생성하세요.")
        return
    
    # SimpleEMA 전략 찾기
    strategy = None
    for s in strategies:
        if "EMA" in s["name"] or "ema" in s["name"].lower():
            strategy = s
            break
    
    if not strategy:
        strategy = strategies[0]  # 첫 번째 전략 사용
    
    print(f"   전략 선택: {strategy['name']} (ID: {strategy['strategy_id']})")
    print(f"   전략 정의:")
    print(f"   {json.dumps(strategy['definition'], indent=2, ensure_ascii=False)}")
    
    # 2. 데이터셋 목록 조회
    print("\n2. 데이터셋 목록 조회...")
    response = requests.get(f"{BASE_URL}/datasets")
    if response.status_code != 200:
        print(f"데이터셋 조회 실패: {response.status_code}")
        return
    
    result = response.json()
    datasets = result.get("data", result.get("datasets", []))
    print(f"데이터셋 {len(datasets)}개 발견")
    
    if not datasets:
        print("데이터셋이 없습니다. 먼저 데이터셋을 생성하세요.")
        return
    
    dataset = datasets[0]
    print(f"   데이터셋 선택: {dataset['name']} (ID: {dataset['dataset_id']})")
    
    # 3. Run 생성
    print("\n3. Run 생성...")
    run_data = {
        "dataset_id": dataset["dataset_id"],
        "strategy_id": strategy["strategy_id"],
        "initial_balance": 10000.0
    }
    
    response = requests.post(f"{BASE_URL}/runs", json=run_data)
    if response.status_code != 201:
        print(f"Run 생성 실패: {response.status_code}")
        print(f"   응답: {response.text}")
        return
    
    run = response.json()
    run_id = run["run_id"]
    print(f"Run 생성 성공 (ID: {run_id})")
    print(f"   상태: {run['status']}")
    
    # 4. Run 완료 대기
    print("\n4. Run 실행 대기...")
    max_wait = 30  # 최대 30초 대기
    wait_interval = 1  # 1초마다 체크
    
    for i in range(max_wait):
        time.sleep(wait_interval)
        
        response = requests.get(f"{BASE_URL}/runs/{run_id}")
        if response.status_code != 200:
            print(f"Run 조회 실패: {response.status_code}")
            return
        
        run = response.json()
        status = run["status"]
        
        print(f"   [{i+1}초] 상태: {status}")
        
        if status == "COMPLETED":
            print("Run 실행 완료!")
            break
        elif status == "FAILED":
            print("Run 실행 실패!")
            print(f"   에러: {run.get('run_artifacts', {})}")
            return
    else:
        print(f"{max_wait}초 대기 후에도 완료되지 않음")
        return
    
    # 5. 결과 조회
    print("\n5. 결과 조회...")
    
    # Trades 조회
    response = requests.get(f"{BASE_URL}/runs/{run_id}/trades")
    if response.status_code != 200:
        print(f"Trades 조회 실패: {response.status_code}")
    else:
        result = response.json()
        trades = result.get("data", result.get("trades", []))
        print(f"Trades: {len(trades)}개")
        
        for i, trade in enumerate(trades[:3], 1):  # 처음 3개만 출력
            print(f"\n   Trade {i}:")
            print(f"   - Direction: {trade['direction']}")
            print(f"   - Entry Price: {trade['entry_price']}")
            print(f"   - Position Size: {trade['position_size']}")
            print(f"   - Total PnL: {trade.get('total_pnl', 'N/A')}")
            print(f"   - Legs: {len(trade.get('legs', []))}개")
    
    # Metrics 조회
    response = requests.get(f"{BASE_URL}/runs/{run_id}/metrics")
    if response.status_code != 200:
        print(f"Metrics 조회 실패: {response.status_code}")
    else:
        metrics = response.json()
        print(f"\nMetrics:")
        print(f"   - Trades Count: {metrics.get('trades_count', 0)}")
        print(f"   - Win Rate: {metrics.get('win_rate', 0):.2%}")
        print(f"   - TP1 Hit Rate: {metrics.get('tp1_hit_rate', 0):.2%}")
        print(f"   - Total PnL: {metrics.get('total_pnl', 0):.2f}")
        print(f"   - Final Balance: {metrics.get('final_balance', 0):.2f}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_run_execution()
    except Exception as e:
        print(f"\n예외 발생: {e}")
        import traceback
        traceback.print_exc()

