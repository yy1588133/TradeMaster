import { useEffect, useRef, useCallback } from 'react'
import { message } from 'antd'

interface UseAutoSaveOptions {
  key: string
  delay?: number
  onSave?: (data: any) => Promise<void> | void
  onRestore?: (data: any) => void
  enabled?: boolean
}

export const useAutoSave = <T = any>({
  key,
  delay = 2000,
  onSave,
  onRestore,
  enabled = true
}: UseAutoSaveOptions) => {
  const timeoutRef = useRef<NodeJS.Timeout>()
  const previousDataRef = useRef<string>()

  // 保存数据到localStorage
  const saveToLocal = useCallback((data: T) => {
    if (!enabled) return
    
    try {
      const serializedData = JSON.stringify(data)
      localStorage.setItem(`autosave_${key}`, serializedData)
      localStorage.setItem(`autosave_${key}_timestamp`, Date.now().toString())
    } catch (error) {
      console.warn('Auto-save to localStorage failed:', error)
    }
  }, [key, enabled])

  // 从localStorage恢复数据
  const restoreFromLocal = useCallback((): T | null => {
    if (!enabled) return null
    
    try {
      const savedData = localStorage.getItem(`autosave_${key}`)
      const timestamp = localStorage.getItem(`autosave_${key}_timestamp`)
      
      if (savedData && timestamp) {
        const age = Date.now() - parseInt(timestamp)
        // 只恢复24小时内的数据
        if (age < 24 * 60 * 60 * 1000) {
          return JSON.parse(savedData)
        }
      }
    } catch (error) {
      console.warn('Auto-restore from localStorage failed:', error)
    }
    
    return null
  }, [key, enabled])

  // 清除保存的数据
  const clearSaved = useCallback(() => {
    localStorage.removeItem(`autosave_${key}`)
    localStorage.removeItem(`autosave_${key}_timestamp`)
  }, [key])

  // 自动保存函数
  const autoSave = useCallback((data: T) => {
    if (!enabled || !data) return

    // 清除之前的定时器
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // 检查数据是否发生变化
    const currentDataStr = JSON.stringify(data)
    if (previousDataRef.current === currentDataStr) {
      return
    }
    previousDataRef.current = currentDataStr

    // 设置新的定时器
    timeoutRef.current = setTimeout(async () => {
      try {
        // 保存到localStorage
        saveToLocal(data)
        
        // 如果提供了自定义保存函数，则调用
        if (onSave) {
          await onSave(data)
        }
      } catch (error) {
        console.error('Auto-save failed:', error)
      }
    }, delay)
  }, [enabled, delay, onSave, saveToLocal])

  // 立即保存
  const saveNow = useCallback(async (data: T) => {
    if (!enabled) return

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    try {
      saveToLocal(data)
      if (onSave) {
        await onSave(data)
      }
      message.success('保存成功')
    } catch (error) {
      console.error('Save failed:', error)
      message.error('保存失败')
    }
  }, [enabled, onSave, saveToLocal])

  // 检查是否有保存的数据
  const hasSavedData = useCallback((): boolean => {
    if (!enabled) return false
    return !!localStorage.getItem(`autosave_${key}`)
  }, [key, enabled])

  // 恢复数据
  const restore = useCallback(() => {
    const savedData = restoreFromLocal()
    if (savedData && onRestore) {
      onRestore(savedData)
      message.info('已恢复之前保存的数据')
    }
    return savedData
  }, [restoreFromLocal, onRestore])

  // 获取保存时间戳
  const getSaveTimestamp = useCallback((): number | null => {
    const timestamp = localStorage.getItem(`autosave_${key}_timestamp`)
    return timestamp ? parseInt(timestamp) : null
  }, [key])

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return {
    autoSave,
    saveNow,
    restore,
    clearSaved,
    hasSavedData,
    getSaveTimestamp
  }
}

export default useAutoSave