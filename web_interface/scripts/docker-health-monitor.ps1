<#
.SYNOPSIS
    Docker容器健康监控和cgroup问题预防脚本
    
.DESCRIPTION
    定期检查Docker容器健康状态，预防和处理cgroup清理问题。
    可以作为定时任务运行或手动执行。
    
.PARAMETER MonitorDuration
    监控持续时间（分钟），默认持续监控
    
.PARAMETER CheckInterval  
    检查间隔（秒），默认30秒
    
.PARAMETER AutoFix
    自动修复发现的问题
    
.EXAMPLE
    .\docker-health-monitor.ps1 -AutoFix
    启动监控并自动修复问题
    
.EXAMPLE
    .\docker-health-monitor.ps1 -MonitorDuration 60 -CheckInterval 10
    监控60分钟，每10秒检查一次

.NOTES
    Author: TradeMaster Development Team
    Version: 1.0
    LastModified: 2025-08-25
#>

[CmdletBinding()]
param(
    [int]$MonitorDuration = 0,  # 0表示持续监控
    [int]$CheckInterval = 30,    # 检查间隔（秒）
    [switch]$AutoFix            # 是否自动修复问题
)

$ErrorActionPreference = "Stop"

# 全局配置
$Global:Config = @{
    ProjectContainers = @("trademaster-backend", "trademaster-frontend", "trademaster-postgresql", "trademaster-redis")
    LogFile = "logs\docker-health.log"
    MaxLogSize = 10MB
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 控制台输出
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry -ForegroundColor White }
    }
    
    # 文件日志
    try {
        # 创建日志目录
        $logDir = Split-Path $Global:Config.LogFile -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        
        # 检查日志文件大小
        if ((Test-Path $Global:Config.LogFile) -and ((Get-Item $Global:Config.LogFile).Length -gt $Global:Config.MaxLogSize)) {
            # 备份并重建日志文件
            $backupLog = $Global:Config.LogFile -replace '\.log$', "_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
            Move-Item $Global:Config.LogFile $backupLog
        }
        
        $logEntry | Add-Content -Path $Global:Config.LogFile -Encoding UTF8
    } catch {
        Write-Warning "无法写入日志文件: $($_.Exception.Message)"
    }
}

function Test-DockerDaemonHealth {
    <#
    .SYNOPSIS
    检查Docker daemon健康状态
    #>
    
    try {
        $dockerInfo = & docker info --format "{{.ServerVersion}}" 2>$null
        if (-not $dockerInfo) {
            Write-Log "Docker daemon不响应" "ERROR"
            return $false
        }
        
        Write-Log "Docker daemon正常运行，版本: $dockerInfo" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "Docker daemon检查失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-ContainerHealth {
    <#
    .SYNOPSIS
    检查项目容器健康状态
    #>
    
    $healthyCount = 0
    $totalContainers = $Global:Config.ProjectContainers.Count
    
    foreach ($containerName in $Global:Config.ProjectContainers) {
        try {
            $containerInfo = & docker inspect $containerName --format "{{.State.Status}}|{{.State.Health.Status}}|{{.State.ExitCode}}" 2>$null
            
            if (-not $containerInfo) {
                Write-Log "容器不存在: $containerName" "WARNING"
                continue
            }
            
            $status, $healthStatus, $exitCode = $containerInfo -split '\|'
            
            switch ($status) {
                "running" {
                    if ($healthStatus -eq "healthy" -or $healthStatus -eq "<no value>") {
                        Write-Log "容器健康: $containerName (状态: $status)" "SUCCESS"
                        $healthyCount++
                    } elseif ($healthStatus -eq "unhealthy") {
                        Write-Log "容器不健康: $containerName (健康状态: $healthStatus)" "ERROR"
                        
                        if ($AutoFix) {
                            Write-Log "尝试重启不健康容器: $containerName" "INFO"
                            Restart-Container $containerName
                        }
                    } else {
                        Write-Log "容器健康检查中: $containerName (健康状态: $healthStatus)" "INFO"
                        $healthyCount++
                    }
                }
                "exited" {
                    Write-Log "容器已退出: $containerName (退出代码: $exitCode)" "ERROR"
                    
                    if ($AutoFix) {
                        Write-Log "尝试重启已退出容器: $containerName" "INFO"
                        Restart-Container $containerName
                    }
                }
                default {
                    Write-Log "容器状态异常: $containerName (状态: $status)" "WARNING"
                }
            }
            
        } catch {
            Write-Log "检查容器失败: $containerName - $($_.Exception.Message)" "ERROR"
        }
    }
    
    $healthPercent = [math]::Round(($healthyCount / $totalContainers) * 100)
    Write-Log "容器健康概览: $healthyCount/$totalContainers ($healthPercent%)" "INFO"
    
    return $healthyCount -eq $totalContainers
}

function Restart-Container {
    <#
    .SYNOPSIS
    重启容器
    #>
    param([string]$ContainerName)
    
    try {
        Write-Log "停止容器: $ContainerName" "INFO"
        & docker stop $ContainerName 2>$null | Out-Null
        
        Write-Log "移除容器: $ContainerName" "INFO"  
        & docker rm -f $ContainerName 2>$null | Out-Null
        
        # 清理相关资源
        Clear-ContainerResources $ContainerName
        
        Write-Log "重新启动容器服务..." "INFO"
        & docker compose up -d 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "容器重启成功: $ContainerName" "SUCCESS"
        } else {
            Write-Log "容器重启失败: $ContainerName" "ERROR"
        }
        
    } catch {
        Write-Log "重启容器失败: $ContainerName - $($_.Exception.Message)" "ERROR"
    }
}

function Clear-ContainerResources {
    <#
    .SYNOPSIS
    清理容器相关资源，防止cgroup问题
    #>
    param([string]$ContainerName)
    
    try {
        Write-Log "清理容器资源: $ContainerName" "INFO"
        
        # 等待容器完全停止
        Start-Sleep -Seconds 2
        
        # 系统级清理
        & docker system prune -f 2>$null | Out-Null
        
        Write-Log "容器资源清理完成: $ContainerName" "SUCCESS"
        
    } catch {
        Write-Log "清理容器资源失败: $ContainerName - $($_.Exception.Message)" "WARNING"
    }
}

function Test-CgroupIssues {
    <#
    .SYNOPSIS
    检查潜在的cgroup问题
    #>
    
    try {
        # 检查Docker日志中的cgroup错误
        $dockerLogs = & docker system events --since 1m --format "{{.Status}}|{{.Type}}|{{.Action}}" 2>$null
        
        if ($dockerLogs) {
            foreach ($logLine in $dockerLogs) {
                if ($logLine -match "cgroup|containerd.*failed") {
                    Write-Log "检测到潜在cgroup问题: $logLine" "WARNING"
                    
                    if ($AutoFix) {
                        Write-Log "执行预防性资源清理" "INFO"
                        & docker system prune -f 2>$null | Out-Null
                    }
                }
            }
        }
        
        return $true
        
    } catch {
        Write-Log "cgroup问题检查失败: $($_.Exception.Message)" "WARNING"
        return $false
    }
}

function Show-HealthSummary {
    <#
    .SYNOPSIS
    显示健康状态摘要
    #>
    
    Write-Host "`n==================== Docker健康监控摘要 ====================" -ForegroundColor Cyan
    Write-Host "监控时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
    Write-Host "检查间隔: $CheckInterval 秒" -ForegroundColor White
    Write-Host "自动修复: $(if ($AutoFix) { '启用' } else { '禁用' })" -ForegroundColor White
    
    # 显示容器状态
    Write-Host "`n容器状态:" -ForegroundColor Yellow
    foreach ($containerName in $Global:Config.ProjectContainers) {
        $status = & docker inspect $containerName --format "{{.State.Status}}" 2>$null
        if ($status) {
            $color = if ($status -eq "running") { "Green" } else { "Red" }
            Write-Host "  $containerName : $status" -ForegroundColor $color
        } else {
            Write-Host "  $containerName : 不存在" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n日志位置: $($Global:Config.LogFile)" -ForegroundColor Gray
    Write-Host "========================================================`n" -ForegroundColor Cyan
}

# 主监控循环
function Start-Monitoring {
    Write-Log "开始Docker容器健康监控" "INFO"
    Write-Log "监控配置 - 间隔: ${CheckInterval}秒, 持续时间: $(if ($MonitorDuration -eq 0) { '持续监控' } else { "${MonitorDuration}分钟" }), 自动修复: $(if ($AutoFix) { '启用' } else { '禁用' })" "INFO"
    
    $startTime = Get-Date
    $checkCount = 0
    
    do {
        $checkCount++
        Write-Log "执行第 $checkCount 次健康检查..." "INFO"
        
        # 检查Docker daemon
        if (-not (Test-DockerDaemonHealth)) {
            Write-Log "Docker daemon异常，跳过容器检查" "WARNING"
        } else {
            # 检查容器健康状态
            Test-ContainerHealth | Out-Null
            
            # 检查cgroup问题
            Test-CgroupIssues | Out-Null
        }
        
        # 显示摘要（每10次检查显示一次）
        if ($checkCount % 10 -eq 0) {
            Show-HealthSummary
        }
        
        # 检查是否达到监控时长
        if ($MonitorDuration -gt 0) {
            $elapsed = (Get-Date) - $startTime
            if ($elapsed.TotalMinutes -ge $MonitorDuration) {
                Write-Log "达到监控时长限制，退出监控" "INFO"
                break
            }
        }
        
        # 等待下次检查
        Start-Sleep -Seconds $CheckInterval
        
    } while ($true)
    
    Write-Log "Docker容器健康监控结束" "INFO"
}

# 程序入口
try {
    Write-Host "🔍 Docker容器健康监控器启动" -ForegroundColor Cyan
    Write-Host "版本: 1.0 | 开发: TradeMaster Team" -ForegroundColor Gray
    Write-Host ""
    
    Start-Monitoring
    
} catch {
    Write-Log "监控程序异常退出: $($_.Exception.Message)" "ERROR"
    exit 1
}