'use client'

import { useEffect, useRef } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, Time } from 'lightweight-charts'
import type { Trade } from '@/lib/types'

interface DrawdownChartProps {
  trades: Trade[]
  initialBalance: number
}

/**
 * 손실폭 차트 (Drawdown Chart)
 * 
 * 최고점 대비 손실폭을 시각화합니다.
 */
export function DrawdownChart({ trades, initialBalance }: DrawdownChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af',
      },
      width: chartContainerRef.current.clientWidth,
      height: 200,
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
        scaleMargins: {
          top: 0.1,
          bottom: 0,
        },
      },
      crosshair: {
        mode: 1,
      },
    })

    // Area 시리즈 추가
    const areaSeries = chart.addAreaSeries({
      topColor: 'rgba(239, 68, 68, 0.4)',
      bottomColor: 'rgba(239, 68, 68, 0.0)',
      lineColor: 'rgba(239, 68, 68, 1)',
      lineWidth: 2,
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => `${price.toFixed(2)}%`,
      },
    })

    chartRef.current = chart
    seriesRef.current = areaSeries

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

    // Drawdown 데이터 생성
    const data: { time: Time; value: number }[] = []
    let currentBalance = initialBalance
    let peak = initialBalance

    // 초기값 추가
    if (trades.length > 0) {
      data.push({
        time: Math.floor(trades[0].entry_timestamp) as Time,
        value: 0,
      })
    }

    // 각 거래 후 Drawdown 계산
    for (const trade of trades) {
      if (trade.total_pnl !== undefined) {
        currentBalance += trade.total_pnl
        
        // 새로운 최고점 갱신
        if (currentBalance > peak) {
          peak = currentBalance
        }
        
        // Drawdown 계산 (%)
        const drawdown = peak > 0 ? ((peak - currentBalance) / peak) * 100 : 0
        
        // 거래 종료 시점의 Drawdown 추가
        const lastLeg = trade.legs[trade.legs.length - 1]
        if (lastLeg) {
          data.push({
            time: Math.floor(lastLeg.exit_timestamp) as Time,
            value: -drawdown, // 음수로 표시 (아래로 내려가는 것이 손실)
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

