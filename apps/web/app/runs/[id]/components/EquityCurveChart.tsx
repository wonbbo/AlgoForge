'use client'

import { useEffect, useRef } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts'
import type { Trade } from '@/lib/types'

interface EquityCurveChartProps {
  trades: Trade[]
  initialBalance: number
}

/**
 * 자산 변화 차트 (Equity Curve)
 * 
 * 거래 시간에 따른 자산 변화를 시각화합니다.
 */
export function EquityCurveChart({ trades, initialBalance }: EquityCurveChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af',
      },
      width: chartContainerRef.current.clientWidth,
      height: 300,
      grid: {
        vertLines: { color: '#2a2e39' },
        horzLines: { color: '#2a2e39' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
      },
      crosshair: {
        mode: 1,
      },
    })

    // 라인 시리즈 추가
    const lineSeries = chart.addLineSeries({
      color: '#10b981',
      lineWidth: 2,
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => `$${price.toFixed(2)}`,
      },
    })

    chartRef.current = chart
    seriesRef.current = lineSeries

    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!seriesRef.current || trades.length === 0) return

    // Equity Curve 데이터 생성
    const data: { time: number; value: number }[] = []
    let currentBalance = initialBalance

    // 초기 잔고 추가
    if (trades.length > 0) {
      data.push({
        time: trades[0].entry_timestamp,
        value: currentBalance,
      })
    }

    // 각 거래 후 잔고 계산
    for (const trade of trades) {
      if (trade.total_pnl !== undefined) {
        currentBalance += trade.total_pnl
        
        // 거래 종료 시점의 잔고 추가
        // 마지막 leg의 timestamp 사용
        const lastLeg = trade.legs[trade.legs.length - 1]
        if (lastLeg) {
          data.push({
            time: lastLeg.exit_timestamp,
            value: currentBalance,
          })
        }
      }
    }

    // 데이터 설정
    seriesRef.current.setData(data)

    // 차트 자동 맞춤
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent()
    }
  }, [trades, initialBalance])

  return (
    <div className="w-full">
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}

