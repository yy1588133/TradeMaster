#!/usr/bin/env node

/**
 * TradeMaster Frontend Build Test Script (Node.js版本)
 * 此脚本用于测试前端构建流程并验证输出
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

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
 * 获取目录大小
 */
function getDirSize(dirPath) {
  try {
    const result = execSync(`du -sh "${dirPath}"`, { encoding: 'utf8' })
    return result.split('\t')[0]
  } catch (error) {
    return 'Unknown'
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

    // 检查package.json
    if (!exists(path.join(frontendDir, 'package.json'))) {
      log.error('package.json文件不存在')
      process.exit(1)
    }
    log.success('找到package.json')

    // 检查dist目录
    if (!exists(distDir)) {
      log.error('构建失败：dist目录不存在')
      log.error('请先运行 npm run build 或 pnpm build')
      process.exit(1)
    }
    log.success('找到dist目录')

    // 检查必需文件
    const requiredFiles = ['index.html', 'assets']
    let missingFiles = []

    for (const file of requiredFiles) {
      const filePath = path.join(distDir, file)
      if (exists(filePath)) {
        log.success(`找到必需文件/目录: ${file}`)
      } else {
        log.error(`缺少必需文件/目录: ${file}`)
        missingFiles.push(file)
      }
    }

    if (missingFiles.length > 0) {
      log.error(`构建验证失败，缺少文件: ${missingFiles.join(', ')}`)
      process.exit(1)
    }

    // 检查assets目录内容
    const assetsDir = path.join(distDir, 'assets')
    if (exists(assetsDir)) {
      const allFiles = getAllFiles(assetsDir)
      const jsFiles = allFiles.filter(file => file.endsWith('.js'))
      const cssFiles = allFiles.filter(file => file.endsWith('.css'))
      const imageFiles = allFiles.filter(file => /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(file))
      const fontFiles = allFiles.filter(file => /\.(woff|woff2|ttf|eot)$/i.test(file))

      log.info('构建产物统计:')
      log.info(`  JavaScript文件: ${jsFiles.length}`)
      log.info(`  CSS文件: ${cssFiles.length}`)
      log.info(`  图片文件: ${imageFiles.length}`)
      log.info(`  字体文件: ${fontFiles.length}`)

      if (jsFiles.length === 0) {
        log.error('未找到JavaScript文件')
        process.exit(1)
      }

      if (cssFiles.length === 0) {
        log.warning('未找到CSS文件（可能正常，如果所有样式都内联了）')
      }

      // 显示最大的几个文件
      const allFilesWithSize = allFiles.map(file => ({
        path: file,
        size: fs.statSync(file).size,
        relativePath: path.relative(distDir, file)
      })).sort((a, b) => b.size - a.size)

      log.info('最大的5个文件:')
      allFilesWithSize.slice(0, 5).forEach(file => {
        log.info(`  ${file.relativePath} (${getFileSize(file.path)})`)
      })
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

      // 检查是否有基本的HTML结构
      if (htmlContent.includes('<div id="root"') || htmlContent.includes('<div id="app"')) {
        log.success('HTML文件包含React根元素')
      } else {
        log.warning('HTML文件可能缺少React根元素')
      }
    }

    // 计算总大小
    const totalSize = getDirSize(distDir)
    log.info(`构建产物总大小: ${totalSize}`)

    // 检查构建产物清单
    log.info('构建产物清单:')
    const allFiles = getAllFiles(distDir)
    allFiles.sort().forEach(file => {
      const relativePath = path.relative(distDir, file)
      const size = getFileSize(file)
      console.log(`  ${relativePath} (${size})`)
    })

    // 性能检查
    log.info('性能检查:')
    const jsFiles = allFiles.filter(file => file.endsWith('.js'))
    const cssFiles = allFiles.filter(file => file.endsWith('.css'))

    // 检查是否有过大的文件
    const largeFiles = allFiles.filter(file => {
      const stats = fs.statSync(file)
      return stats.size > 1024 * 1024 // 1MB
    })

    if (largeFiles.length > 0) {
      log.warning(`发现较大文件 (>1MB):`)
      largeFiles.forEach(file => {
        const relativePath = path.relative(distDir, file)
        const size = getFileSize(file)
        log.warning(`  ${relativePath} (${size})`)
      })
    }

    // 检查是否有source map文件
    const sourceMaps = allFiles.filter(file => file.endsWith('.map'))
    if (sourceMaps.length > 0) {
      log.info(`找到 ${sourceMaps.length} 个source map文件`)
    }

    log.success('====================')
    log.success('前端构建验证完成！')
    log.success('====================')
    log.info(`构建产物位置: ${distDir}`)
    log.info(`总大小: ${totalSize}`)
    log.info(`文件总数: ${allFiles.length}`)
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