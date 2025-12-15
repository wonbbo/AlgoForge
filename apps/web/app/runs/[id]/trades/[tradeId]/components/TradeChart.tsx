"use client"

import { useEffect, useRef } from 'react'
import { 
  createChart, 
  ColorType, 
  IChartApi,
  Time,
  CandlestickData,
  LineData,
  SeriesMarker
} from 'lightweight-charts'
import type { ChartDataResponse } from '@/lib/types'

interface TradeChartProps {
  chartData: ChartDataResponse
}

/**
 * Trade 차트 컴포넌트
 * 
 * TradingView Lightweight Charts를 사용하여 거래 차트를 표시합니다.
 * - 캔들스틱 차트
 * - Overlay 지표 (EMA, SMA 등)
 * - 진입/청산 마커
 * - SL/TP1 라인
 * - Oscillator 지표 (하단, 조건부)
 */
export function TradeChart({ chartData }: TradeChartProps) {
  const mainChartContainerRef = useRef<HTMLDivElement>(null)
  const oscillatorChartContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!mainChartContainerRef.current) return

    // Cleanup 플래그 (컴포넌트가 언마운트되는 중인지 추적)
    let isCleaningUp = false

    // 메인 차트 생성
    const chart = createChart(mainChartContainerRef.current, {
      width: mainChartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#666',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })

    // Oscillator 지표가 있는지 확인
    const hasOscillator = Object.values(chartData.indicator_types).some(
      type => type === 'oscillator'
    )

    let oscChart: IChartApi | null = null
    if (hasOscillator && oscillatorChartContainerRef.current) {
      oscChart = createChart(oscillatorChartContainerRef.current, {
        width: oscillatorChartContainerRef.current.clientWidth,
        height: 150,
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#666',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
        timeScale: {
          timeVisible: true,
          secondsVisible: false,
        },
      })

      // 메인 차트와 oscillator 차트의 타임스케일 동기화
      chart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        // Cleanup 중이거나 oscChart가 없으면 무시
        if (isCleaningUp || !oscChart) return

        // lightweight-charts에서 timeRange가 null로 전달될 수 있으므로 방어 로직 추가
        if (!timeRange) return

        try {
          oscChart.timeScale().setVisibleRange(timeRange)
        } catch (error) {
          // 타이밍 이슈로 인한 에러 무시 (디버깅용 로그)
          console.debug('Chart sync error:', error)
        }
      })
    }

    // === 차트 데이터 추가 ===
    
    // 캔들스틱 데이터 생성
    const candlestickData: CandlestickData[] = chartData.bars.map(bar => ({
      time: bar.timestamp as Time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }))

    // 캔들스틱 시리즈 추가
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })
    candlestickSeries.setData(candlestickData)

    // Overlay 지표 추가
    const overlayIndicators = Object.entries(chartData.indicators).filter(
      ([id]) => chartData.indicator_types[id] === 'overlay'
    )

    const colors = ['#2962FF', '#FF6D00', '#00E676', '#D500F9', '#FFD600']
    overlayIndicators.forEach(([indicatorId, values], index) => {
      const lineData: LineData[] = values.map((value, i) => ({
        time: chartData.bars[i].timestamp as Time,
        value: value,
      }))

      const lineSeries = chart.addLineSeries({
        color: colors[index % colors.length],
        lineWidth: 2,
        title: indicatorId,
      })
      lineSeries.setData(lineData)
    })

    // 마커 추가
    const markers: SeriesMarker<Time>[] = []

    // 진입 마커
    const entryMarker: SeriesMarker<Time> = {
      time: chartData.trade_info.entry_timestamp as Time,
      position: chartData.trade_info.direction === 'LONG' ? 'belowBar' : 'aboveBar',
      color: chartData.trade_info.direction === 'LONG' ? '#26a69a' : '#ef5350',
      shape: chartData.trade_info.direction === 'LONG' ? 'arrowUp' : 'arrowDown',
      text: `${chartData.trade_info.direction} 진입`,
    }
    markers.push(entryMarker)

    // 청산 마커들
    chartData.trade_info.legs.forEach(leg => {
      let color = '#666'
      let text = leg.exit_type

      if (leg.exit_type === 'TP1') {
        color = '#2196F3'
        text = 'TP1'
      } else if (leg.exit_type === 'SL') {
        color = '#ef5350'
        text = 'SL'
      } else if (leg.exit_type === 'BE') {
        color = '#FFC107'
        text = 'BE'
      } else if (leg.exit_type === 'REVERSE') {
        color = '#9C27B0'
        text = 'REVERSE'
      }

      const exitMarker: SeriesMarker<Time> = {
        time: leg.exit_timestamp as Time,
        position: chartData.trade_info.direction === 'LONG' ? 'aboveBar' : 'belowBar',
        color: color,
        shape: 'circle',
        text: text,
      }
      markers.push(exitMarker)
    })

    candlestickSeries.setMarkers(markers)

    // SL 라인 추가 (진입부터 청산까지)
    const lastExitTimestamp = Math.max(
      ...chartData.trade_info.legs.map(leg => leg.exit_timestamp)
    )
    
    const slLineData: LineData[] = chartData.bars
      .filter(bar => 
        bar.timestamp >= chartData.trade_info.entry_timestamp && 
        bar.timestamp <= lastExitTimestamp
      )
      .map(bar => ({
        time: bar.timestamp as Time,
        value: chartData.trade_info.stop_loss,
      }))

    const slLineSeries = chart.addLineSeries({
      color: '#ef5350',
      lineWidth: 1,
      lineStyle: 2, // 점선
      title: 'SL',
      lastValueVisible: false,
      priceLineVisible: false,
    })
    slLineSeries.setData(slLineData)

    // TP1 라인 추가 (진입부터 TP1 도달 또는 청산까지)
    const tp1Leg = chartData.trade_info.legs.find(leg => leg.exit_type === 'TP1')
    const tp1EndTimestamp = tp1Leg 
      ? tp1Leg.exit_timestamp 
      : lastExitTimestamp

    const tp1LineData: LineData[] = chartData.bars
      .filter(bar => 
        bar.timestamp >= chartData.trade_info.entry_timestamp && 
        bar.timestamp <= tp1EndTimestamp
      )
      .map(bar => ({
        time: bar.timestamp as Time,
        value: chartData.trade_info.take_profit_1,
      }))

    const tp1LineSeries = chart.addLineSeries({
      color: '#2196F3',
      lineWidth: 1,
      lineStyle: 2, // 점선
      title: 'TP1',
      lastValueVisible: false,
      priceLineVisible: false,
    })
    tp1LineSeries.setData(tp1LineData)

    // BE 라인 추가 (TP1 도달 후부터 청산까지, 해당되는 경우만)
    if (tp1Leg) {
      const beLineData: LineData[] = chartData.bars
        .filter(bar => 
          bar.timestamp > tp1Leg.exit_timestamp && 
          bar.timestamp <= lastExitTimestamp
        )
        .map(bar => ({
          time: bar.timestamp as Time,
          value: chartData.trade_info.entry_price, // BE = 진입가
        }))

      if (beLineData.length > 0) {
        const beLineSeries = chart.addLineSeries({
          color: '#FFC107',
          lineWidth: 1,
          lineStyle: 2, // 점선
          title: 'BE',
          lastValueVisible: false,
          priceLineVisible: false,
        })
        beLineSeries.setData(beLineData)
      }
    }

    // Oscillator 지표 추가 (하단 차트)
    if (oscChart) {
      const oscillatorIndicators = Object.entries(chartData.indicators).filter(
        ([id]) => chartData.indicator_types[id] === 'oscillator'
      )

      oscillatorIndicators.forEach(([indicatorId, values], index) => {
        const lineData: LineData[] = values.map((value, i) => ({
          time: chartData.bars[i].timestamp as Time,
          value: value,
        }))

        const lineSeries = oscChart.addLineSeries({
          color: colors[index % colors.length],
          lineWidth: 2,
          title: indicatorId,
        })
        lineSeries.setData(lineData)
      })

      // RSI의 경우 30, 70 참조 라인 추가
      const hasRSI = oscillatorIndicators.some(([id]) => 
        id.toLowerCase().includes('rsi')
      )

      if (hasRSI) {
        // 30 라인
        const ref30Data: LineData[] = chartData.bars.map(bar => ({
          time: bar.timestamp as Time,
          value: 30,
        }))
        const ref30Series = oscChart.addLineSeries({
          color: '#666',
          lineWidth: 1,
          lineStyle: 2,
          lastValueVisible: false,
          priceLineVisible: false,
        })
        ref30Series.setData(ref30Data)

        // 70 라인
        const ref70Data: LineData[] = chartData.bars.map(bar => ({
          time: bar.timestamp as Time,
          value: 70,
        }))
        const ref70Series = oscChart.addLineSeries({
          color: '#666',
          lineWidth: 1,
          lineStyle: 2,
          lastValueVisible: false,
          priceLineVisible: false,
        })
        ref70Series.setData(ref70Data)
      }
    }

    // 차트 fitting
    chart.timeScale().fitContent()
    if (oscChart) {
      oscChart.timeScale().fitContent()
    }

    // 리사이즈 핸들러
    const handleResize = () => {
      if (mainChartContainerRef.current) {
        chart.applyOptions({ 
          width: mainChartContainerRef.current.clientWidth 
        })
      }
      if (oscChart && oscillatorChartContainerRef.current) {
        oscChart.applyOptions({ 
          width: oscillatorChartContainerRef.current.clientWidth 
        })
      }
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      isCleaningUp = true
      window.removeEventListener('resize', handleResize)
      chart.remove()
      if (oscChart) {
        oscChart.remove()
      }
    }
  }, [chartData])

  // Oscillator 지표 존재 여부 확인
  const hasOscillator = Object.values(chartData.indicator_types).some(
    type => type === 'oscillator'
  )

  return (
    <div className="space-y-4">
      <div ref={mainChartContainerRef} className="w-full" />
      {hasOscillator && (
        <div ref={oscillatorChartContainerRef} className="w-full" />
      )}
    </div>
  )
}
