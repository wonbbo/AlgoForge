"use client"

import { useEffect, useRef } from 'react'
import { 
  createChart, 
  ColorType, 
  IChartApi,
  Time,
  CandlestickData,
  LineData,
  HistogramData,
  SeriesMarker
} from 'lightweight-charts'
import type { ChartDataResponse, ChartSeriesConfig } from '@/lib/types'

interface TradeChartProps {
  chartData: ChartDataResponse
}

/**
 * Trade 차트 컴포넌트
 * 
 * TradingView Lightweight Charts를 사용하여 거래 차트를 표시합니다.
 * - 캔들스틱 차트 (main 차트)
 * - chart_name별로 그룹핑된 지표들
 * - 타입별 렌더링 (line, column, point)
 * - 진입/청산 마커
 * - SL/TP1/BE 라인
 */
export function TradeChart({ chartData }: TradeChartProps) {
  const chartContainersRef = useRef<Map<string, HTMLDivElement>>(new Map())
  const chartsRef = useRef<Map<string, IChartApi>>(new Map())

  useEffect(() => {
    // Cleanup 플래그
    let isCleaningUp = false
    
    // cleanup 함수에서 사용할 ref 값 복사
    const chartsMap = chartsRef.current

    // chart_name별로 지표 그룹핑
    const indicatorsByChartName = new Map<string, Array<{
      key: string
      values: number[]
      config: ChartSeriesConfig
    }>>()
    
    // 포인트 타입 지표는 별도로 관리 (항상 main 차트에만)
    const pointIndicators: Array<{
      key: string
      values: number[]
      config: ChartSeriesConfig
    }> = []

    // 모든 지표를 chart_name별로 그룹핑
    Object.entries(chartData.indicators || {}).forEach(([indicatorKey, values]) => {
      const config = chartData.indicator_chart_config?.[indicatorKey]
      if (!config) return

      // 포인트 타입은 항상 main 차트에만 그리기
      if (config.type === 'point') {
        pointIndicators.push({
          key: indicatorKey,
          values,
          config: {
            ...config,
            chart_name: 'main'  // 강제로 main으로 설정
          }
        })
        return
      }

      const chartName = config.chart_name || 'main'
      if (!indicatorsByChartName.has(chartName)) {
        indicatorsByChartName.set(chartName, [])
      }
      indicatorsByChartName.get(chartName)!.push({
        key: indicatorKey,
        values,
        config
      })
    })

    // 차트 생성 (chart_name별로)
    const chartNames = Array.from(indicatorsByChartName.keys())
    // main 차트는 항상 첫 번째
    if (!chartNames.includes('main')) {
      chartNames.unshift('main')
    } else {
      // main을 맨 앞으로 이동
      const mainIndex = chartNames.indexOf('main')
      chartNames.splice(mainIndex, 1)
      chartNames.unshift('main')
    }

    chartNames.forEach((chartName, index) => {
      const container = chartContainersRef.current.get(chartName)
      if (!container) return

      const chart = createChart(container, {
        width: container.clientWidth,
        height: chartName === 'main' ? 400 : 150,
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
        rightPriceScale: {
          borderColor: '#2B2B43',
        },
      })

      chartsRef.current.set(chartName, chart)

      // main 차트에만 캔들스틱 추가
      if (chartName === 'main') {
        const candlestickData: CandlestickData[] = chartData.bars.map(bar => ({
          time: bar.timestamp as Time,
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
        }))

        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#26a69a',
          downColor: '#ef5350',
          borderVisible: false,
          wickUpColor: '#26a69a',
          wickDownColor: '#ef5350',
          priceFormat: {
            type: 'custom',
            formatter: (price: number) => price.toFixed(4),
          },
        })
        candlestickSeries.setData(candlestickData)

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

        // 포인트 타입 지표 마커 추가
        pointIndicators.forEach(({ key, values, config }) => {
          const properties = config.properties || {}
          // 표시 여부 확인 (기본값: true)
          if (properties.visible === false) {
            return  // 표시하지 않음
          }
          
          const color = properties.color || '#2962FF'
          
          values.forEach((value, i) => {
            // 0은 그리지 않음
            if (value === 0 || value === null || value === undefined) return
            
            const bar = chartData.bars[i]
            if (!bar) return
            
            let shape: 'arrowUp' | 'arrowDown' = 'arrowUp'
            let position: 'belowBar' | 'aboveBar' = 'belowBar'
            
            if (value > 0) {
              // 양수: 윗쪽 화살표, low 값 아래에
              shape = 'arrowUp'
              position = 'belowBar'
            } else {
              // 음수: 아랫쪽 화살표, high 값 위에
              shape = 'arrowDown'
              position = 'aboveBar'
            }
            
            markers.push({
              time: bar.timestamp as Time,
              position: position,
              color: color,
              shape: shape,
              size: 1,
            })
          })
        })

        // 마커를 시간 순서대로 정렬
        markers.sort((a, b) => {
          const timeA = typeof a.time === 'number' ? a.time : (a.time as any).timestamp || 0
          const timeB = typeof b.time === 'number' ? b.time : (b.time as any).timestamp || 0
          return timeA - timeB
        })

        candlestickSeries.setMarkers(markers)

        // SL 라인 추가
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
          priceFormat: {
            type: 'custom',
            formatter: (price: number) => price.toFixed(4),
          },
        })
        slLineSeries.setData(slLineData)

        // TP1 라인 추가
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
          priceFormat: {
            type: 'custom',
            formatter: (price: number) => price.toFixed(4),
          },
        })
        tp1LineSeries.setData(tp1LineData)

        // BE 라인 추가
        if (tp1Leg) {
          const beLineData: LineData[] = chartData.bars
            .filter(bar => 
              bar.timestamp > tp1Leg.exit_timestamp && 
              bar.timestamp <= lastExitTimestamp
            )
            .map(bar => ({
              time: bar.timestamp as Time,
              value: chartData.trade_info.entry_price,
            }))

          if (beLineData.length > 0) {
            const beLineSeries = chart.addLineSeries({
              color: '#FFC107',
              lineWidth: 1,
              lineStyle: 2, // 점선
              title: 'BE',
              lastValueVisible: false,
              priceLineVisible: false,
              priceFormat: {
                type: 'custom',
                formatter: (price: number) => price.toFixed(4),
              },
            })
            beLineSeries.setData(beLineData)
          }
        }
      }

      // 지표 추가
      const indicators = indicatorsByChartName.get(chartName) || []
      indicators.forEach(({ key, values, config }) => {
        // 표시 여부 확인 (기본값: true)
        const properties = config.properties || {}
        if (properties.visible === false) {
          return  // 표시하지 않음
        }
        
        const data = values.map((value, i) => ({
          time: chartData.bars[i].timestamp as Time,
          value: value,
        }))

        const color = properties.color || '#2962FF'
        // lineWidth는 1-10 사이의 정수 (기본값: 1)
        const lineWidthValue = Math.max(1, Math.min(10, properties.lineWidth || 1))
        const lineStyle = properties.lineStyle !== undefined ? properties.lineStyle : 0  // 기본값: 실선

        if (config.type === 'line') {
          // Line 타입
          // lineWidth는 TradingView 타입 정의 이슈로 인해 타입 단언 필요
          // lineWidthValue는 1-10 사이의 정수로 보장됨
          const lineSeries = chart.addLineSeries({
            color: color,
            lineWidth: lineWidthValue,
            lineStyle: lineStyle,
            title: key,
            priceFormat: {
              type: 'custom',
              formatter: (price: number) => price.toFixed(4),
            },
          } as Parameters<typeof chart.addLineSeries>[0])
          lineSeries.setData(data as LineData[])
        } else if (config.type === 'column') {
          // Column 타입 (Histogram 사용)
          const histogramData: HistogramData[] = data.map(d => ({
            time: d.time,
            value: d.value,
            color: color,
          }))
          const histogramSeries = chart.addHistogramSeries({
            color: color,
            title: key,
            priceFormat: {
              type: 'custom',
              formatter: (price: number) => price.toFixed(4),
            },
          })
          histogramSeries.setData(histogramData)
        }
      })

      // 차트 fitting
      chart.timeScale().fitContent()
    })

    // 타임스케일 동기화 (main 차트를 기준으로)
    const mainChart = chartsRef.current.get('main')
    if (mainChart) {
      mainChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if (isCleaningUp || !timeRange) return

        chartsRef.current.forEach((chart, chartName) => {
          if (chartName === 'main') return
          try {
            chart.timeScale().setVisibleRange(timeRange)
          } catch (error) {
            console.debug('Chart sync error:', error)
          }
        })
      })
    }

    // 리사이즈 핸들러
    const handleResize = () => {
      chartsRef.current.forEach((chart, chartName) => {
        const container = chartContainersRef.current.get(chartName)
        if (container) {
          chart.applyOptions({
            width: container.clientWidth
          })
        }
      })
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      isCleaningUp = true
      window.removeEventListener('resize', handleResize)
      // useEffect 내부에서 복사한 ref 값 사용
      chartsMap.forEach(chart => chart.remove())
      chartsMap.clear()
    }
  }, [chartData])

  // chart_name별로 컨테이너 생성
  const chartNames = new Set<string>(['main'])
  if (chartData.indicator_chart_config) {
    Object.values(chartData.indicator_chart_config).forEach(config => {
      if (config?.chart_name) {
        chartNames.add(config.chart_name)
      }
    })
  }

  return (
    <div className="space-y-4">
      {Array.from(chartNames).map(chartName => (
        <div
          key={chartName}
          ref={(el) => {
            if (el) {
              chartContainersRef.current.set(chartName, el)
            } else {
              chartContainersRef.current.delete(chartName)
            }
          }}
          className="w-full"
        />
      ))}
    </div>
  )
}
