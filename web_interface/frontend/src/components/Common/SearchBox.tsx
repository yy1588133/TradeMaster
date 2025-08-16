import React, { useState, useCallback } from 'react'
import { Input, Select, Space, Button } from 'antd'
import { SearchOutlined, ClearOutlined } from '@ant-design/icons'
import { debounce } from 'lodash-es'

const { Search } = Input
const { Option } = Select

export interface SearchBoxProps {
  placeholder?: string
  allowClear?: boolean
  loading?: boolean
  onSearch?: (value: string) => void
  onClear?: () => void
  style?: React.CSSProperties
  size?: 'small' | 'middle' | 'large'
  debounceMs?: number
  showSearchButton?: boolean
  enterButton?: boolean | React.ReactNode
}

export interface AdvancedSearchBoxProps extends SearchBoxProps {
  filters?: Array<{
    key: string
    label: string
    options: Array<{ label: string; value: any }>
    placeholder?: string
    allowClear?: boolean
  }>
  onFiltersChange?: (filters: Record<string, any>) => void
  initialFilters?: Record<string, any>
}

const SearchBox: React.FC<SearchBoxProps> = ({
  placeholder = '请输入搜索关键词',
  allowClear = true,
  loading = false,
  onSearch,
  onClear,
  style,
  size = 'middle',
  debounceMs = 300,
  showSearchButton = false,
  enterButton = false,
}) => {
  const [searchValue, setSearchValue] = useState('')

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((value: string) => {
      onSearch?.(value)
    }, debounceMs),
    [onSearch, debounceMs]
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchValue(value)
    
    if (debounceMs > 0) {
      debouncedSearch(value)
    }
  }

  const handleSearch = (value: string) => {
    if (debounceMs === 0) {
      onSearch?.(value)
    }
  }

  const handleClear = () => {
    setSearchValue('')
    onClear?.()
    onSearch?.('')
  }

  return (
    <Search
      placeholder={placeholder}
      allowClear={allowClear}
      loading={loading}
      value={searchValue}
      onChange={handleChange}
      onSearch={handleSearch}
      onClear={handleClear}
      style={style}
      size={size}
      enterButton={enterButton}
    />
  )
}

export const AdvancedSearchBox: React.FC<AdvancedSearchBoxProps> = ({
  filters = [],
  onFiltersChange,
  initialFilters = {},
  ...searchProps
}) => {
  const [filterValues, setFilterValues] = useState<Record<string, any>>(initialFilters)

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...filterValues, [key]: value }
    setFilterValues(newFilters)
    onFiltersChange?.(newFilters)
  }

  const handleClearFilters = () => {
    setFilterValues({})
    onFiltersChange?.({})
  }

  const hasActiveFilters = Object.values(filterValues).some(value => 
    value !== undefined && value !== null && value !== ''
  )

  return (
    <Space.Compact style={{ width: '100%', ...searchProps.style }}>
      <SearchBox {...searchProps} style={{ flex: 1 }} />
      
      {filters.map(filter => (
        <Select
          key={filter.key}
          placeholder={filter.placeholder || `选择${filter.label}`}
          allowClear={filter.allowClear !== false}
          value={filterValues[filter.key]}
          onChange={(value) => handleFilterChange(filter.key, value)}
          style={{ minWidth: 120 }}
          size={searchProps.size}
        >
          {filter.options.map(option => (
            <Option key={option.value} value={option.value}>
              {option.label}
            </Option>
          ))}
        </Select>
      ))}
      
      {hasActiveFilters && (
        <Button
          icon={<ClearOutlined />}
          onClick={handleClearFilters}
          size={searchProps.size}
          title="清除筛选"
        />
      )}
    </Space.Compact>
  )
}

export default SearchBox