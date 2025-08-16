import React from 'react'
import { Pie } from '@ant-design/plots'
import { Card, Empty, Spin } from 'antd'
import type { PieConfig } from '@ant-design/plots'

import { CHART_COLORS } from '@/constants'

export interface PieChartProps {
  data: any[]
  title?: string
  height?: number
  loading?: boolean
  angleField: string
  colorField: string
  radius?: number
  innerRadius?: number
  color?: string[]
  showTooltip?: boolean
  showLegend?: boolean
  showLabel?: boolean
  labelType?: 'inner' | 'outer' | 'spider'
  valueFormatter?: (value: number) => string
  config?: Partial<PieConfig>
  style?: React.CSSProperties
  bodyStyle?: React.CSSProperties
}

const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  height = 300,
  loading = false,
  angleField,
  colorField,
  radius = 0.8,
  innerRadius = 0,
  color = CHART_COLORS,
  showTooltip = true,
  showLegend = true,
  showLabel = true,
  labelType = 'outer',
  valueFormatter,
  config = {},
  style,
  bodyStyle,
}) => {
  const chartConfig: PieConfig = {
    data,
    angleField,
    colorField,
    height,
    radius,
    innerRadius,
    color,
    legend: showLegend ? {
      position: 'bottom',
    } : false,
    tooltip: showTooltip ? {
      formatter: (datum) => {
        return {
          name: datum[colorField],
          value: valueFormatter ? valueFormatter(datum[angleField]) : datum[angleField],
        }
      },
    } : false,
    label: showLabel ? {
      type: labelType,
      content: '{name}\n{percentage}',
      style: {
        fontSize: 12,
        textAlign: 'center',
      },
    } : false,
    interactions: [
      {
        type: 'element-active',
      },
      {
        type: 'pie-statistic-active',
      },
    ],
    animation: {
      appear: {
        animation: 'grow-in-x',
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

    return <Pie {...chartConfig} />
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

export default PieChart