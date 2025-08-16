import React from 'react'
import { Column } from '@ant-design/plots'
import { Card, Empty, Spin } from 'antd'
import type { ColumnConfig } from '@ant-design/plots'

import { CHART_COLORS } from '@/constants'

export interface BarChartProps {
  data: any[]
  title?: string
  height?: number
  loading?: boolean
  xField: string
  yField: string
  seriesField?: string
  color?: string | string[] | ((datum: any) => string)
  showTooltip?: boolean
  showLegend?: boolean
  yAxisFormatter?: (value: number) => string
  xAxisFormatter?: (value: any) => string
  config?: Partial<ColumnConfig>
  style?: React.CSSProperties
  bodyStyle?: React.CSSProperties
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  title,
  height = 300,
  loading = false,
  xField,
  yField,
  seriesField,
  color,
  showTooltip = true,
  showLegend = true,
  yAxisFormatter,
  xAxisFormatter,
  config = {},
  style,
  bodyStyle,
}) => {
  const chartConfig: ColumnConfig = {
    data,
    xField,
    yField,
    seriesField,
    height,
    color: color || (seriesField ? CHART_COLORS : CHART_COLORS[0]),
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
    legend: showLegend && seriesField ? {
      position: 'top-right',
    } : false,
    tooltip: showTooltip ? {
      shared: true,
    } : false,
    xAxis: {
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
    animation: {
      appear: {
        animation: 'grow-in-y',
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

    return <Column {...chartConfig} />
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

export default BarChart