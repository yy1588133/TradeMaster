import React from 'react'
import { Line } from '@ant-design/plots'
import { Card, Empty, Spin } from 'antd'
import type { LineConfig } from '@ant-design/plots'

import { CHART_COLORS } from '@/constants'

export interface LineChartProps {
  data: any[]
  title?: string
  height?: number
  loading?: boolean
  xField: string
  yField: string
  seriesField?: string
  smooth?: boolean
  color?: string | string[]
  showSlider?: boolean
  showArea?: boolean
  showTooltip?: boolean
  showLegend?: boolean
  yAxisFormatter?: (value: number) => string
  xAxisFormatter?: (value: any) => string
  config?: Partial<LineConfig>
  style?: React.CSSProperties
  bodyStyle?: React.CSSProperties
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  title,
  height = 300,
  loading = false,
  xField,
  yField,
  seriesField,
  smooth = true,
  color,
  showSlider = false,
  showArea = false,
  showTooltip = true,
  showLegend = true,
  yAxisFormatter,
  xAxisFormatter,
  config = {},
  style,
  bodyStyle,
}) => {
  const chartConfig: LineConfig = {
    data,
    xField,
    yField,
    seriesField,
    smooth,
    height,
    color: color || (seriesField ? CHART_COLORS : CHART_COLORS[0]),
    point: {
      size: 3,
      shape: 'circle',
    },
    legend: showLegend ? {
      position: 'top-right',
    } : false,
    tooltip: showTooltip ? {
      shared: true,
      showCrosshairs: true,
      crosshairs: {
        type: 'xy',
        line: {
          style: {
            stroke: '#565656',
            lineDash: [4, 4],
          },
        },
      },
    } : false,
    xAxis: {
      type: 'timeCat' as any,
      tickCount: 5,
      label: xAxisFormatter ? {
        formatter: xAxisFormatter,
      } : undefined,
    },
    yAxis: {
      label: yAxisFormatter ? {
        formatter: yAxisFormatter,
      } : undefined,
      grid: {
        line: {
          style: {
            stroke: '#f0f0f0',
            lineWidth: 1,
          },
        },
      },
    },
    slider: showSlider ? {
      start: 0,
      end: 1,
    } : undefined,
    area: showArea ? {
      style: {
        fillOpacity: 0.3,
      },
    } : undefined,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    ...config,
  }

  const content = () => {
    if (loading) {
      return (
        <div style={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}>
          <Spin size="large" />
        </div>
      )
    }

    if (!data || data.length === 0) {
      return (
        <div style={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}>
          <Empty description="暂无数据" />
        </div>
      )
    }

    return <Line {...chartConfig} />
  }

  if (title) {
    return (
      <Card title={title} style={style} bodyStyle={bodyStyle}>
        {content()}
      </Card>
    )
  }

  return (
    <div style={style}>
      {content()}
    </div>
  )
}

export default LineChart