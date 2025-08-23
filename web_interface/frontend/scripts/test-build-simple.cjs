#!/usr/bin/env node

/**
 * TradeMaster Frontend Build Test Script (简化版)
 * 验证构建产物是否正确生成
 */

const fs = require('fs')
const path = require('path')

// 颜色定义
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
}

// 日志函数
const log = {
  info: (msg) => console.log(`${colors.blue}[INFO]${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}[SUCCESS]${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}[WARNING]${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}[ERROR]${colors.reset} ${msg}`)
}

// 项目路径
const frontendDir = process.cwd()
const distDir = path.join(frontendDir, 'dist')

/**
 * 检查文件或目录是否存在
 */
function exists(filePath) {
  try {
    return fs.existsSync(filePath)
  } catch (error) {
    return false
  }
}

/**
 * 获取文件大小
 */
function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath)
    const size = stats.size
    if (size < 1024) return `${size}B`
    if (size < 1024 * 1024) return `${Math.round(size / 1024)}KB`
    return `${Math.round(size / (1024 * 1024))}MB`
  } catch (error) {
    return 'Unknown'
  }
}

/**
 * 递归获取所有文件
 */
function getAllFiles(dirPath, arrayOfFiles = []) {
  if (!fs.existsSync(dirPath)) return arrayOfFiles
  
  const files = fs.readdirSync(dirPath)
  
  files.forEach(file => {
    const fullPath = path.join(dirPath, file)
    if (fs.statSync(fullPath).isDirectory()) {
      arrayOfFiles = getAllFiles(fullPath, arrayOfFiles)
    } else {
      arrayOfFiles.push(fullPath)
    }
  })
  
  return arrayOfFiles
}

/**
 * 主测试函数
 */
async function testBuild() {
  try {
    log.info('开始前端构建验证...')
    log.info(`前端目录: ${frontendDir}`)

    // 检查dist目录
    if (!exists(distDir)) {
      log.error('构建失败：dist目录不存在')
      log.error('请先运行构建命令')
      process.exit(1)
    }
    log.success('找到dist目录')

    // 检查必需文件
    const requiredFiles = ['index.html']
    const requiredDirs = ['css', 'js']
    
    // 检查文件
    for (const file of requiredFiles) {
      const filePath = path.join(distDir, file)
      if (exists(filePath)) {
        log.success(`找到必需文件: ${file}`)
      } else {
        log.error(`缺少必需文件: ${file}`)
        process.exit(1)
      }
    }
    
    // 检查目录
    for (const dir of requiredDirs) {
      const dirPath = path.join(distDir, dir)
      if (exists(dirPath)) {
        log.success(`找到必需目录: ${dir}`)
      } else {
        log.error(`缺少必需目录: ${dir}`)
        process.exit(1)
      }
    }

    // 收集所有文件
    let allFiles = []
    const cssDir = path.join(distDir, 'css')
    const jsDir = path.join(distDir, 'js')
    
    if (exists(cssDir)) {
      allFiles = allFiles.concat(getAllFiles(cssDir))
    }
    if (exists(jsDir)) {
      allFiles = allFiles.concat(getAllFiles(jsDir))
    }

    const jsFiles = allFiles.filter(file => file.endsWith('.js'))
    const cssFiles = allFiles.filter(file => file.endsWith('.css'))

    log.info('构建产物统计:')
    log.info(`  JavaScript文件: ${jsFiles.length}`)
    log.info(`  CSS文件: ${cssFiles.length}`)
    log.info(`  总文件数: ${allFiles.length}`)

    if (jsFiles.length === 0) {
      log.error('未找到JavaScript文件')
      process.exit(1)
    }

    if (cssFiles.length === 0) {
      log.warning('未找到CSS文件（可能样式都内联了）')
    }

    // 验证HTML文件
    log.info('验证HTML文件...')
    const indexPath = path.join(distDir, 'index.html')
    if (exists(indexPath)) {
      const htmlContent = fs.readFileSync(indexPath, 'utf8')
      
      if (htmlContent.includes('<script')) {
        log.success('HTML文件包含JavaScript引用')
      } else {
        log.warning('HTML文件可能缺少JavaScript引用')
      }

      if (htmlContent.includes('stylesheet') || htmlContent.includes('<style')) {
        log.success('HTML文件包含CSS引用')
      } else {
        log.warning('HTML文件可能缺少CSS引用')
      }

      if (htmlContent.includes('<div id="root"') || htmlContent.includes('<div id="app"')) {
        log.success('HTML文件包含React根元素')
      } else {
        log.warning('HTML文件可能缺少React根元素')
      }
    }

    // 显示构建产物清单
    log.info('构建产物清单:')
    const distFiles = getAllFiles(distDir)
    distFiles.sort().forEach(file => {
      const relativePath = path.relative(distDir, file)
      const size = getFileSize(file)
      console.log(`  ${relativePath} (${size})`)
    })

    log.success('====================')
    log.success('前端构建验证完成！')
    log.success('====================')
    log.info(`构建产物位置: ${distDir}`)
    log.info(`文件总数: ${distFiles.length}`)
    log.success('构建通过验证，可以用于生产部署！')

  } catch (error) {
    log.error(`构建验证失败: ${error.message}`)
    console.error(error)
    process.exit(1)
  }
}

// 运行测试
if (require.main === module) {
  testBuild()
}

module.exports = { testBuild }