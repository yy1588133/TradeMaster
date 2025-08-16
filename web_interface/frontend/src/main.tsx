import React from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

import App from './App'
import { store } from './store'
import './styles/globals.less'

// Configure dayjs
dayjs.locale('zh-cn')

// Get root element
const container = document.getElementById('root')
if (!container) {
  throw new Error('Root element not found')
}

// Create root
const root = createRoot(container)

// Render app
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <BrowserRouter>
        <ConfigProvider
          locale={zhCN}
          theme={{
            token: {
              colorPrimary: '#1890ff',
              borderRadius: 6,
              wireframe: false,
            },
            components: {
              Layout: {
                headerBg: '#001529',
                siderBg: '#001529',
                triggerBg: '#002140',
              },
              Menu: {
                darkItemBg: '#001529',
                darkSubMenuItemBg: '#000c17',
                darkItemSelectedBg: '#1890ff',
              },
            },
          }}
        >
          <App />
        </ConfigProvider>
      </BrowserRouter>
    </Provider>
  </React.StrictMode>,
)