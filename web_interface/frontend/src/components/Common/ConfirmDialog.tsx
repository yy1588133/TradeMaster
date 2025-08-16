import React from 'react'
import { Modal, Typography } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

export interface ConfirmDialogOptions {
  title?: string
  content?: React.ReactNode
  okText?: string
  cancelText?: string
  okType?: 'primary' | 'danger' | 'default'
  icon?: React.ReactNode
  maskClosable?: boolean
  centered?: boolean
  width?: number
  onOk?: () => void | Promise<void>
  onCancel?: () => void
}

export const showConfirmDialog = (options: ConfirmDialogOptions) => {
  const {
    title = '确认操作',
    content,
    okText = '确认',
    cancelText = '取消',
    okType = 'primary',
    icon = <ExclamationCircleOutlined />,
    maskClosable = false,
    centered = true,
    width = 416,
    onOk,
    onCancel,
  } = options

  return Modal.confirm({
    title,
    content,
    icon,
    okText,
    cancelText,
    okType,
    maskClosable,
    centered,
    width,
    onOk,
    onCancel,
  })
}

export const showDeleteConfirm = (
  itemName: string,
  onConfirm: () => void | Promise<void>,
  options?: Partial<ConfirmDialogOptions>
) => {
  return showConfirmDialog({
    title: '确认删除',
    content: (
      <div>
        <Text>确定要删除 </Text>
        <Text strong>"{itemName}"</Text>
        <Text> 吗？</Text>
        <br />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          此操作不可恢复，请谨慎操作。
        </Text>
      </div>
    ),
    okText: '删除',
    okType: 'danger',
    onOk: onConfirm,
    ...options,
  })
}

export const showBatchDeleteConfirm = (
  count: number,
  onConfirm: () => void | Promise<void>,
  options?: Partial<ConfirmDialogOptions>
) => {
  return showConfirmDialog({
    title: '确认批量删除',
    content: (
      <div>
        <Text>确定要删除选中的 </Text>
        <Text strong>{count}</Text>
        <Text> 个项目吗？</Text>
        <br />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          此操作不可恢复，请谨慎操作。
        </Text>
      </div>
    ),
    okText: '删除',
    okType: 'danger',
    onOk: onConfirm,
    ...options,
  })
}

export const showUnsavedChangesConfirm = (
  onConfirm: () => void | Promise<void>,
  options?: Partial<ConfirmDialogOptions>
) => {
  return showConfirmDialog({
    title: '未保存的更改',
    content: (
      <div>
        <Text>您有未保存的更改，确定要离开吗？</Text>
        <br />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          离开后将丢失所有未保存的更改。
        </Text>
      </div>
    ),
    okText: '离开',
    cancelText: '继续编辑',
    okType: 'danger',
    onOk: onConfirm,
    ...options,
  })
}

const ConfirmDialog = {
  show: showConfirmDialog,
  showDelete: showDeleteConfirm,
  showBatchDelete: showBatchDeleteConfirm,
  showUnsavedChanges: showUnsavedChangesConfirm,
}

export default ConfirmDialog