"use client";

import { useEffect, useState } from "react";

interface RunProgress {
  run_id: number;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  progress_percent?: number;
  processed_bars?: number;
  total_bars?: number;
}

interface RunProgressMonitorProps {
  runId: number;
  onComplete?: () => void;
}

/**
 * Run 진행률 모니터링 컴포넌트
 * 
 * 백테스트 실행 중 진행 상황을 실시간으로 표시합니다.
 * 1초마다 API를 폴링하여 진행률을 업데이트합니다.
 */
export function RunProgressMonitor({ runId, onComplete }: RunProgressMonitorProps) {
  const [progress, setProgress] = useState<RunProgress | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    // 초기 데이터 로드
    fetchProgress();

    // 폴링이 활성화되어 있고 상태가 RUNNING이 아니면 폴링 중단
    if (!isPolling) {
      return;
    }

    // 1초마다 진행 상황 폴링
    const interval = setInterval(async () => {
      await fetchProgress();
    }, 1000);

    return () => clearInterval(interval);
  }, [runId, isPolling]);

  const fetchProgress = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/runs/${runId}`);
      if (!response.ok) {
        throw new Error("진행률 조회 실패");
      }

      const data: RunProgress = await response.json();
      setProgress(data);

      // 완료되거나 실패한 경우 폴링 중단
      if (data.status === "COMPLETED" || data.status === "FAILED") {
        setIsPolling(false);
        
        // 완료 콜백 호출
        if (onComplete && data.status === "COMPLETED") {
          onComplete();
        }
      }
    } catch (error) {
      console.error("진행률 조회 실패:", error);
      // 에러가 발생해도 계속 폴링 (일시적인 네트워크 문제일 수 있음)
    }
  };

  if (!progress) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-gray-600" />
        <span>로딩 중...</span>
      </div>
    );
  }

  // 상태별 표시
  if (progress.status === "PENDING") {
    return (
      <div className="flex items-center gap-2 text-sm text-blue-600">
        <div className="animate-pulse rounded-full h-2 w-2 bg-blue-600" />
        <span>대기 중</span>
      </div>
    );
  }

  if (progress.status === "FAILED") {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600">
        <div className="rounded-full h-2 w-2 bg-red-600" />
        <span>실행 실패</span>
      </div>
    );
  }

  if (progress.status === "COMPLETED") {
    return (
      <div className="flex items-center gap-2 text-sm text-green-600">
        <div className="rounded-full h-2 w-2 bg-green-600" />
        <span>완료</span>
      </div>
    );
  }

  // RUNNING 상태: 진행률 표시
  const progressPercent = progress.progress_percent ?? 0;
  const processedBars = progress.processed_bars ?? 0;
  const totalBars = progress.total_bars ?? 0;

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-sm">
        <span className="text-gray-700 font-medium">실행 중</span>
        <span className="text-blue-600 font-semibold">
          {progressPercent.toFixed(1)}%
        </span>
      </div>

      {/* 진행 바 */}
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* 상세 정보 */}
      {totalBars > 0 && (
        <div className="text-xs text-gray-500">
          {processedBars.toLocaleString()} / {totalBars.toLocaleString()} 봉 처리됨
        </div>
      )}
    </div>
  );
}

