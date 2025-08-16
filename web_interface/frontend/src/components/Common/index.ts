export { default as ConfirmDialog } from './ConfirmDialog'
export { default as SearchBox, AdvancedSearchBox } from './SearchBox'

export type { ConfirmDialogOptions } from './ConfirmDialog'
export type { SearchBoxProps, AdvancedSearchBoxProps } from './SearchBox'

// Re-export existing components
export { default as LoadingSpinner } from '../Loading/LoadingSpinner'
export { default as PageLoader } from '../Loading/PageLoader'
export { default as ErrorBoundary } from '../Error/ErrorBoundary'
export { default as NotificationProvider } from '../Notification/NotificationProvider'