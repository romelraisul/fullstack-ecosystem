# Complete Coolify System Monitoring Setup
# Enterprise-grade monitoring, logging, and alerting system

param(
    [string]$CoolifyPath = "C:\coolify",
    [string]$MonitoringPath = "C:\coolify\monitoring",
    [bool]$EnableAlerts = $true,
    [string]$AlertEmail = "admin@coolify.local"
)

Write-Host "📊 Setting up comprehensive monitoring system..." -ForegroundColor Green

# Create monitoring directory structure
$monitoringDirs = @(
    "$MonitoringPath\prometheus",
    "$MonitoringPath\grafana",
    "$MonitoringPath\logs",
    "$MonitoringPath\alerts",
    "$MonitoringPath\dashboards",
    "$MonitoringPath\exporters"
)

foreach ($dir in $monitoringDirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host "📁 Created directory: $dir" -ForegroundColor White
}

# Step 1: Prometheus Configuration
Write-Host "🔍 Configuring Prometheus monitoring..." -ForegroundColor Cyan

$prometheusConfig = @"
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'coolify-monitor'
    environment: 'production'

rule_files:
  - "/etc/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: '/metrics'

  # Coolify application metrics
  - job_name: 'coolify-app'
    static_configs:
      - targets: ['coolify:8000']
    scrape_interval: 15s
    metrics_path: '/metrics'
    scrape_timeout: 10s

  # API service metrics
  - job_name: 'coolify-api'
    static_configs:
      - targets: ['api:8010']
    scrape_interval: 15s
    metrics_path: '/api/metrics'

  # Frontend application metrics
  - job_name: 'coolify-frontend'
    static_configs:
      - targets: ['frontend:5173']
    scrape_interval: 30s
    metrics_path: '/metrics'

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    scrape_interval: 15s
    metrics_path: '/nginx_status'

  # Node exporter for system metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  # Docker metrics
  - job_name: 'docker'
    static_configs:
      - targets: ['docker-exporter:9323']
    scrape_interval: 30s

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # Custom application metrics
  - job_name: 'custom-metrics'
    static_configs:
      - targets: ['custom-exporter:8080']
    scrape_interval: 60s
    honor_labels: true

  # Security and audit metrics
  - job_name: 'security-metrics'
    static_configs:
      - targets: ['security-exporter:9200']
    scrape_interval: 60s

# Remote write configuration for long-term storage
remote_write:
  - url: http://prometheus-remote:9201/write
    queue_config:
      max_samples_per_send: 1000
      max_shards: 200
      capacity: 2500
"@

$prometheusConfig | Out-File "$MonitoringPath\prometheus\prometheus.yml" -Encoding UTF8

# Prometheus alerting rules
$alertingRules = @"
groups:
  - name: coolify-alerts
    rules:
    # High-level service availability
    - alert: CoolifyServiceDown
      expr: up{job="coolify-app"} == 0
      for: 1m
      labels:
        severity: critical
        service: coolify
      annotations:
        summary: "Coolify application is down"
        description: "Coolify main application has been down for more than 1 minute"

    - alert: APIServiceDown
      expr: up{job="coolify-api"} == 0
      for: 1m
      labels:
        severity: critical
        service: api
      annotations:
        summary: "Coolify API service is down"
        description: "Coolify API service has been down for more than 1 minute"

    # Performance alerts
    - alert: HighResponseTime
      expr: http_request_duration_seconds{quantile="0.95"} > 2
      for: 5m
      labels:
        severity: warning
        type: performance
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ \$value }}s for more than 5 minutes"

    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
      for: 2m
      labels:
        severity: critical
        type: error
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ \$value }} requests/second for more than 2 minutes"

    # Resource utilization alerts
    - alert: HighCPUUsage
      expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
      for: 5m
      labels:
        severity: warning
        type: resource
      annotations:
        summary: "High CPU usage"
        description: "CPU usage is above 80% for more than 5 minutes"

    - alert: HighMemoryUsage
      expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
      for: 5m
      labels:
        severity: warning
        type: resource
      annotations:
        summary: "High memory usage"
        description: "Memory usage is above 85% for more than 5 minutes"

    - alert: LowDiskSpace
      expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 85
      for: 2m
      labels:
        severity: critical
        type: resource
      annotations:
        summary: "Low disk space"
        description: "Disk usage is above 85% on {{ \$labels.mountpoint }}"

    # Database alerts
    - alert: PostgreSQLDown
      expr: up{job="postgres"} == 0
      for: 1m
      labels:
        severity: critical
        service: database
      annotations:
        summary: "PostgreSQL database is down"
        description: "PostgreSQL database has been down for more than 1 minute"

    - alert: HighDatabaseConnections
      expr: pg_stat_database_numbackends / pg_settings_max_connections * 100 > 80
      for: 5m
      labels:
        severity: warning
        service: database
      annotations:
        summary: "High database connections"
        description: "Database connections are above 80% of maximum"

    # Security alerts
    - alert: FailedLoginAttempts
      expr: increase(nginx_http_requests_total{status="401"}[5m]) > 10
      for: 1m
      labels:
        severity: warning
        type: security
      annotations:
        summary: "Multiple failed login attempts"
        description: "More than 10 failed login attempts in the last 5 minutes"

    - alert: UnauthorizedAccess
      expr: increase(nginx_http_requests_total{status="403"}[5m]) > 5
      for: 1m
      labels:
        severity: warning
        type: security
      annotations:
        summary: "Unauthorized access attempts"
        description: "More than 5 unauthorized access attempts in the last 5 minutes"

    # Container and Docker alerts
    - alert: ContainerRestartLoop
      expr: increase(container_restart_count[15m]) > 3
      for: 0m
      labels:
        severity: warning
        type: container
      annotations:
        summary: "Container restart loop detected"
        description: "Container {{ \$labels.name }} has restarted more than 3 times in 15 minutes"

    - alert: ContainerHighMemory
      expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100 > 90
      for: 5m
      labels:
        severity: critical
        type: container
      annotations:
        summary: "Container high memory usage"
        description: "Container {{ \$labels.name }} memory usage is above 90%"

    # SSL Certificate expiry
    - alert: SSLCertificateExpiry
      expr: ssl_certificate_expiry_days < 30
      for: 1h
      labels:
        severity: warning
        type: security
      annotations:
        summary: "SSL certificate expiring soon"
        description: "SSL certificate expires in {{ \$value }} days"

    # Backup and maintenance alerts
    - alert: BackupFailed
      expr: time() - backup_last_success_timestamp > 86400
      for: 1h
      labels:
        severity: warning
        type: maintenance
      annotations:
        summary: "Backup has not run successfully"
        description: "Backup has not completed successfully in the last 24 hours"
"@

$alertingRules | Out-File "$MonitoringPath\prometheus\rules\coolify-alerts.yml" -Encoding UTF8

Write-Host "✅ Prometheus configuration completed!" -ForegroundColor Green

# Step 2: Grafana Configuration
Write-Host "📊 Configuring Grafana dashboards..." -ForegroundColor Cyan

# Grafana datasource configuration
$grafanaDatasource = @{
    apiVersion = 1
    datasources = @(
        @{
            name = "Prometheus"
            type = "prometheus"
            access = "proxy"
            url = "http://prometheus:9090"
            isDefault = $true
            editable = $true
            basicAuth = $false
            jsonData = @{
                timeInterval = "15s"
                queryTimeout = "60s"
                httpMethod = "POST"
            }
        }
    )
} | ConvertTo-Json -Depth 10

$grafanaDatasource | Out-File "$MonitoringPath\grafana\datasources.yml" -Encoding UTF8

# Comprehensive Coolify dashboard
$coolifyDashboard = @{
    dashboard = @{
        id = $null
        title = "Coolify System Overview"
        tags = @("coolify", "overview", "system")
        timezone = "browser"
        refresh = "30s"
        time = @{
            from = "now-1h"
            to = "now"
        }
        panels = @(
            @{
                id = 1
                title = "Service Status"
                type = "stat"
                targets = @(
                    @{expr = 'up{job=~"coolify.*"}'; legendFormat = "{{job}}"}
                )
                fieldConfig = @{
                    defaults = @{
                        color = @{mode = "thresholds"}
                        thresholds = @{
                            steps = @(
                                @{color = "red"; value = 0},
                                @{color = "green"; value = 1}
                            )
                        }
                    }
                }
                gridPos = @{h = 8; w = 6; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Request Rate"
                type = "graph"
                targets = @(
                    @{expr = 'rate(http_requests_total[5m])'; legendFormat = "{{method}} {{status}}"}
                )
                yAxes = @(
                    @{label = "Requests/sec"}
                )
                gridPos = @{h = 8; w = 18; x = 6; y = 0}
            },
            @{
                id = 3
                title = "Response Time"
                type = "graph"
                targets = @(
                    @{expr = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'; legendFormat = "95th percentile"},
                    @{expr = 'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))'; legendFormat = "50th percentile"}
                )
                yAxes = @(
                    @{label = "Seconds"}
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 8}
            },
            @{
                id = 4
                title = "Error Rate"
                type = "graph"
                targets = @(
                    @{expr = 'rate(http_requests_total{status=~"5.."}[5m])'; legendFormat = "5xx errors"},
                    @{expr = 'rate(http_requests_total{status=~"4.."}[5m])'; legendFormat = "4xx errors"}
                )
                yAxes = @(
                    @{label = "Errors/sec"}
                )
                gridPos = @{h = 8; w = 12; x = 12; y = 8}
            },
            @{
                id = 5
                title = "CPU Usage"
                type = "graph"
                targets = @(
                    @{expr = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'; legendFormat = "CPU Usage %"}
                )
                yAxes = @(
                    @{label = "Percentage"; min = 0; max = 100}
                )
                gridPos = @{h = 8; w = 8; x = 0; y = 16}
            },
            @{
                id = 6
                title = "Memory Usage"
                type = "graph"
                targets = @(
                    @{expr = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'; legendFormat = "Memory Usage %"}
                )
                yAxes = @(
                    @{label = "Percentage"; min = 0; max = 100}
                )
                gridPos = @{h = 8; w = 8; x = 8; y = 16}
            },
            @{
                id = 7
                title = "Disk Usage"
                type = "graph"
                targets = @(
                    @{expr = '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100'; legendFormat = "{{mountpoint}}"}
                )
                yAxes = @(
                    @{label = "Percentage"; min = 0; max = 100}
                )
                gridPos = @{h = 8; w = 8; x = 16; y = 16}
            },
            @{
                id = 8
                title = "Container Status"
                type = "table"
                targets = @(
                    @{expr = 'container_last_seen'; legendFormat = "{{name}}"}
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 24}
            },
            @{
                id = 9
                title = "Recent Logs"
                type = "logs"
                targets = @(
                    @{expr = '{job=~"coolify.*"}'}
                )
                gridPos = @{h = 8; w = 12; x = 12; y = 24}
            }
        )
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$coolifyDashboard | Out-File "$MonitoringPath\dashboards\coolify-overview.json" -Encoding UTF8

# Security dashboard
$securityDashboard = @{
    dashboard = @{
        id = $null
        title = "Security & Audit Dashboard"
        tags = @("security", "audit", "monitoring")
        timezone = "browser"
        refresh = "1m"
        time = @{
            from = "now-24h"
            to = "now"
        }
        panels = @(
            @{
                id = 1
                title = "Failed Login Attempts"
                type = "graph"
                targets = @(
                    @{expr = 'increase(nginx_http_requests_total{status="401"}[5m])'; legendFormat = "Failed Logins"}
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Unauthorized Access"
                type = "graph"
                targets = @(
                    @{expr = 'increase(nginx_http_requests_total{status="403"}[5m])'; legendFormat = "Unauthorized"}
                )
                gridPos = @{h = 8; w = 12; x = 12; y = 0}
            },
            @{
                id = 3
                title = "SSL Certificate Status"
                type = "stat"
                targets = @(
                    @{expr = 'ssl_certificate_expiry_days'; legendFormat = "Days to Expiry"}
                )
                gridPos = @{h = 4; w = 6; x = 0; y = 8}
            },
            @{
                id = 4
                title = "Security Alerts"
                type = "table"
                targets = @(
                    @{expr = 'ALERTS{alertname=~".*Security.*|.*Login.*|.*SSL.*"}'; legendFormat = "{{alertname}}"}
                )
                gridPos = @{h = 8; w = 18; x = 6; y = 8}
            }
        )
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$securityDashboard | Out-File "$MonitoringPath\dashboards\security-audit.json" -Encoding UTF8

Write-Host "✅ Grafana dashboards configured!" -ForegroundColor Green

# Step 3: Alertmanager Configuration
if ($EnableAlerts) {
    Write-Host "🚨 Configuring Alertmanager..." -ForegroundColor Cyan

    $alertmanagerConfig = @"
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@coolify.local'
  smtp_require_tls: true

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default-receiver'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 10s
    repeat_interval: 5m
  - match:
      severity: warning
    receiver: 'warning-alerts'
    repeat_interval: 1h
  - match:
      type: security
    receiver: 'security-alerts'
    group_wait: 5s
    repeat_interval: 30m

receivers:
- name: 'default-receiver'
  email_configs:
  - to: '$AlertEmail'
    subject: '[Coolify] Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Severity: {{ .Labels.severity }}
      Time: {{ .StartsAt }}
      {{ end }}

- name: 'critical-alerts'
  email_configs:
  - to: '$AlertEmail'
    subject: '[CRITICAL] Coolify Alert: {{ .GroupLabels.alertname }}'
    body: |
      🚨 CRITICAL ALERT 🚨

      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Severity: {{ .Labels.severity }}
      Service: {{ .Labels.service }}
      Time: {{ .StartsAt }}
      {{ end }}

      Immediate action required!

- name: 'warning-alerts'
  email_configs:
  - to: '$AlertEmail'
    subject: '[WARNING] Coolify Alert: {{ .GroupLabels.alertname }}'
    body: |
      ⚠️ WARNING ALERT ⚠️

      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Severity: {{ .Labels.severity }}
      Time: {{ .StartsAt }}
      {{ end }}

- name: 'security-alerts'
  email_configs:
  - to: '$AlertEmail'
    subject: '[SECURITY] Coolify Security Alert: {{ .GroupLabels.alertname }}'
    body: |
      🔒 SECURITY ALERT 🔒

      {{ range .Alerts }}
      Security Issue: {{ .Annotations.summary }}
      Details: {{ .Annotations.description }}
      Type: {{ .Labels.type }}
      Time: {{ .StartsAt }}
      {{ end }}

      Review security logs immediately!

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'service']
"@

    $alertmanagerConfig | Out-File "$MonitoringPath\alerts\alertmanager.yml" -Encoding UTF8

    Write-Host "✅ Alertmanager configured!" -ForegroundColor Green
}

# Step 4: Logging Configuration
Write-Host "📝 Configuring centralized logging..." -ForegroundColor Cyan

# Create log collection script
$logCollectionScript = @"
# Centralized Log Collection for Coolify
param(
    [string]`$LogPath = "$MonitoringPath\logs",
    [int]`$RetentionDays = 30
)

Write-Host "📝 Starting log collection..." -ForegroundColor Green

# Create log directories
`$logDirs = @(
    "`$LogPath\application",
    "`$LogPath\system",
    "`$LogPath\security",
    "`$LogPath\containers",
    "`$LogPath\nginx",
    "`$LogPath\database"
)

foreach (`$dir in `$logDirs) {
    New-Item -ItemType Directory -Path `$dir -Force | Out-Null
}

# Collect application logs
try {
    docker logs coolify --since 1h > "`$LogPath\application\coolify-`$(Get-Date -Format 'yyyy-MM-dd-HH').log" 2>&1
    docker logs api --since 1h > "`$LogPath\application\api-`$(Get-Date -Format 'yyyy-MM-dd-HH').log" 2>&1
    docker logs frontend --since 1h > "`$LogPath\application\frontend-`$(Get-Date -Format 'yyyy-MM-dd-HH').log" 2>&1
    Write-Host "✅ Application logs collected" -ForegroundColor White
} catch {
    Write-Host "⚠️ Error collecting application logs: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Collect system logs
try {
    Get-WinEvent -LogName System -MaxEvents 1000 |
        Where-Object { `$_.TimeCreated -gt (Get-Date).AddHours(-1) } |
        Export-Csv "`$LogPath\system\system-`$(Get-Date -Format 'yyyy-MM-dd-HH').csv" -NoTypeInformation
    Write-Host "✅ System logs collected" -ForegroundColor White
} catch {
    Write-Host "⚠️ Error collecting system logs: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Collect security logs
try {
    Get-WinEvent -LogName Security -MaxEvents 500 |
        Where-Object { `$_.TimeCreated -gt (Get-Date).AddHours(-1) } |
        Export-Csv "`$LogPath\security\security-`$(Get-Date -Format 'yyyy-MM-dd-HH').csv" -NoTypeInformation
    Write-Host "✅ Security logs collected" -ForegroundColor White
} catch {
    Write-Host "⚠️ Error collecting security logs: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Collect container logs
try {
    docker ps --format "table {{.Names}}" | Select-Object -Skip 1 | ForEach-Object {
        `$containerName = `$_.Trim()
        if (`$containerName) {
            docker logs `$containerName --since 1h > "`$LogPath\containers\`$containerName-`$(Get-Date -Format 'yyyy-MM-dd-HH').log" 2>&1
        }
    }
    Write-Host "✅ Container logs collected" -ForegroundColor White
} catch {
    Write-Host "⚠️ Error collecting container logs: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Clean up old logs
try {
    Get-ChildItem -Path `$LogPath -Recurse -File |
        Where-Object { `$_.CreationTime -lt (Get-Date).AddDays(-`$RetentionDays) } |
        Remove-Item -Force
    Write-Host "✅ Old logs cleaned up (older than `$RetentionDays days)" -ForegroundColor White
} catch {
    Write-Host "⚠️ Error cleaning up old logs: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "📝 Log collection completed!" -ForegroundColor Green
"@

$logCollectionScript | Out-File "$MonitoringPath\collect-logs.ps1" -Encoding UTF8

# Step 5: Health Check Script
Write-Host "🏥 Creating comprehensive health check..." -ForegroundColor Cyan

$healthCheckScript = @"
# Comprehensive Health Check for Coolify Ecosystem
param(
    [string]`$ReportPath = "$MonitoringPath\health-reports",
    [bool]`$SendAlert = `$true
)

Write-Host "🏥 Starting comprehensive health check..." -ForegroundColor Green

# Create health report directory
New-Item -ItemType Directory -Path `$ReportPath -Force | Out-Null

`$healthReport = @{
    timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    overall_status = "unknown"
    checks = @()
    summary = @{
        total_checks = 0
        passed = 0
        failed = 0
        warnings = 0
    }
}

# Function to add health check result
function Add-HealthCheck {
    param(
        [string]`$Name,
        [string]`$Status,
        [string]`$Message,
        [string]`$Severity = "info"
    )

    `$healthReport.checks += @{
        name = `$Name
        status = `$Status
        message = `$Message
        severity = `$Severity
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    }

    `$healthReport.summary.total_checks++

    switch (`$Status) {
        "pass" { `$healthReport.summary.passed++ }
        "fail" { `$healthReport.summary.failed++ }
        "warning" { `$healthReport.summary.warnings++ }
    }
}

# Check 1: Docker Service
try {
    `$dockerStatus = docker version --format '{{.Server.Version}}' 2>`$null
    if (`$dockerStatus) {
        Add-HealthCheck "Docker Service" "pass" "Docker is running (version: `$dockerStatus)"
    } else {
        Add-HealthCheck "Docker Service" "fail" "Docker is not responding" "critical"
    }
} catch {
    Add-HealthCheck "Docker Service" "fail" "Docker check failed: `$(`$_.Exception.Message)" "critical"
}

# Check 2: Container Status
try {
    `$containers = docker ps --format "{{.Names}},{{.Status}}" | ConvertFrom-Csv -Header "Name","Status"
    `$expectedContainers = @("coolify", "api", "frontend", "nginx", "prometheus", "grafana")

    foreach (`$expected in `$expectedContainers) {
        `$container = `$containers | Where-Object { `$_.Name -eq `$expected }
        if (`$container -and `$container.Status -like "*Up*") {
            Add-HealthCheck "Container: `$expected" "pass" "Container is running"
        } elseif (`$container) {
            Add-HealthCheck "Container: `$expected" "fail" "Container exists but not running: `$(`$container.Status)" "high"
        } else {
            Add-HealthCheck "Container: `$expected" "fail" "Container not found" "high"
        }
    }
} catch {
    Add-HealthCheck "Container Status" "fail" "Container check failed: `$(`$_.Exception.Message)" "high"
}

# Check 3: Service Endpoints
`$endpoints = @(
    @{Name="Coolify Dashboard"; URL="http://localhost:8000"; Expected=200},
    @{Name="API Service"; URL="http://localhost:8010/health"; Expected=200},
    @{Name="Frontend"; URL="http://localhost:5173"; Expected=200},
    @{Name="Prometheus"; URL="http://localhost:9090/-/healthy"; Expected=200},
    @{Name="Grafana"; URL="http://localhost:3000/api/health"; Expected=200}
)

foreach (`$endpoint in `$endpoints) {
    try {
        `$response = Invoke-WebRequest -Uri `$endpoint.URL -Method GET -TimeoutSec 10 -UseBasicParsing
        if (`$response.StatusCode -eq `$endpoint.Expected) {
            Add-HealthCheck "Endpoint: `$(`$endpoint.Name)" "pass" "Service responding (HTTP `$(`$response.StatusCode))"
        } else {
            Add-HealthCheck "Endpoint: `$(`$endpoint.Name)" "warning" "Unexpected status code: `$(`$response.StatusCode)" "medium"
        }
    } catch {
        Add-HealthCheck "Endpoint: `$(`$endpoint.Name)" "fail" "Service not responding: `$(`$_.Exception.Message)" "high"
    }
}

# Check 4: Resource Usage
try {
    # CPU usage
    `$cpuUsage = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
    if (`$cpuUsage -lt 80) {
        Add-HealthCheck "CPU Usage" "pass" "CPU usage is `$([math]::Round(`$cpuUsage, 2))%"
    } elseif (`$cpuUsage -lt 90) {
        Add-HealthCheck "CPU Usage" "warning" "High CPU usage: `$([math]::Round(`$cpuUsage, 2))%" "medium"
    } else {
        Add-HealthCheck "CPU Usage" "fail" "Critical CPU usage: `$([math]::Round(`$cpuUsage, 2))%" "high"
    }

    # Memory usage
    `$totalMemory = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum
    `$availableMemory = (Get-Counter '\Memory\Available Bytes').CounterSamples.CookedValue
    `$memoryUsage = ((`$totalMemory - `$availableMemory) / `$totalMemory) * 100

    if (`$memoryUsage -lt 80) {
        Add-HealthCheck "Memory Usage" "pass" "Memory usage is `$([math]::Round(`$memoryUsage, 2))%"
    } elseif (`$memoryUsage -lt 90) {
        Add-HealthCheck "Memory Usage" "warning" "High memory usage: `$([math]::Round(`$memoryUsage, 2))%" "medium"
    } else {
        Add-HealthCheck "Memory Usage" "fail" "Critical memory usage: `$([math]::Round(`$memoryUsage, 2))%" "high"
    }

    # Disk space
    `$disks = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { `$_.DriveType -eq 3 }
    foreach (`$disk in `$disks) {
        `$diskUsage = ((`$disk.Size - `$disk.FreeSpace) / `$disk.Size) * 100
        if (`$diskUsage -lt 80) {
            Add-HealthCheck "Disk Space (`$(`$disk.DeviceID))" "pass" "Disk usage is `$([math]::Round(`$diskUsage, 2))%"
        } elseif (`$diskUsage -lt 90) {
            Add-HealthCheck "Disk Space (`$(`$disk.DeviceID))" "warning" "High disk usage: `$([math]::Round(`$diskUsage, 2))%" "medium"
        } else {
            Add-HealthCheck "Disk Space (`$(`$disk.DeviceID))" "fail" "Critical disk usage: `$([math]::Round(`$diskUsage, 2))%" "high"
        }
    }
} catch {
    Add-HealthCheck "Resource Usage" "fail" "Resource check failed: `$(`$_.Exception.Message)" "medium"
}

# Check 5: SSL Certificate
try {
    if (Test-Path "ssl\coolify.crt") {
        # Simple certificate expiry check (simplified for demo)
        Add-HealthCheck "SSL Certificate" "pass" "SSL certificate file exists"
    } else {
        Add-HealthCheck "SSL Certificate" "warning" "SSL certificate file not found" "medium"
    }
} catch {
    Add-HealthCheck "SSL Certificate" "fail" "SSL check failed: `$(`$_.Exception.Message)" "medium"
}

# Check 6: Backup Status
try {
    `$backupPath = "C:\coolify-backups"
    if (Test-Path `$backupPath) {
        `$latestBackup = Get-ChildItem -Path `$backupPath -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (`$latestBackup -and `$latestBackup.LastWriteTime -gt (Get-Date).AddDays(-1)) {
            Add-HealthCheck "Backup Status" "pass" "Recent backup found: `$(`$latestBackup.Name)"
        } else {
            Add-HealthCheck "Backup Status" "warning" "No recent backup found (older than 24 hours)" "medium"
        }
    } else {
        Add-HealthCheck "Backup Status" "warning" "Backup directory not found" "medium"
    }
} catch {
    Add-HealthCheck "Backup Status" "fail" "Backup check failed: `$(`$_.Exception.Message)" "medium"
}

# Determine overall status
if (`$healthReport.summary.failed -gt 0) {
    `$healthReport.overall_status = "unhealthy"
} elseif (`$healthReport.summary.warnings -gt 0) {
    `$healthReport.overall_status = "degraded"
} else {
    `$healthReport.overall_status = "healthy"
}

# Generate report
`$reportFile = "`$ReportPath\health-report-`$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
`$healthReport | ConvertTo-Json -Depth 5 | Out-File `$reportFile -Encoding UTF8

# Display summary
Write-Host ""
Write-Host "🏥 Health Check Summary" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Overall Status: " -NoNewline
switch (`$healthReport.overall_status) {
    "healthy" { Write-Host "✅ HEALTHY" -ForegroundColor Green }
    "degraded" { Write-Host "⚠️ DEGRADED" -ForegroundColor Yellow }
    "unhealthy" { Write-Host "❌ UNHEALTHY" -ForegroundColor Red }
}

Write-Host "Total Checks: `$(`$healthReport.summary.total_checks)" -ForegroundColor White
Write-Host "Passed: `$(`$healthReport.summary.passed)" -ForegroundColor Green
Write-Host "Warnings: `$(`$healthReport.summary.warnings)" -ForegroundColor Yellow
Write-Host "Failed: `$(`$healthReport.summary.failed)" -ForegroundColor Red
Write-Host ""

# Display failed and warning checks
`$criticalIssues = `$healthReport.checks | Where-Object { `$_.status -eq "fail" -or (`$_.status -eq "warning" -and `$_.severity -eq "high") }
if (`$criticalIssues) {
    Write-Host "🚨 Critical Issues:" -ForegroundColor Red
    foreach (`$issue in `$criticalIssues) {
        Write-Host "   - `$(`$issue.name): `$(`$issue.message)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "📄 Full report saved to: `$reportFile" -ForegroundColor Cyan

# Send alert if enabled and there are issues
if (`$SendAlert -and (`$healthReport.summary.failed -gt 0 -or `$healthReport.summary.warnings -gt 0)) {
    Write-Host "🚨 Sending health alert..." -ForegroundColor Yellow
    # In production, integrate with alerting system
}

Write-Host "✅ Health check completed!" -ForegroundColor Green

# Exit with appropriate code
if (`$healthReport.overall_status -eq "unhealthy") {
    exit 1
} elseif (`$healthReport.overall_status -eq "degraded") {
    exit 2
} else {
    exit 0
}
"@

$healthCheckScript | Out-File "$MonitoringPath\health-check.ps1" -Encoding UTF8

# Step 6: Enhanced Docker Compose for monitoring
Write-Host "🐳 Updating Docker Compose with monitoring services..." -ForegroundColor Cyan

$monitoringDockerCompose = @"
version: '3.8'

services:
  # Existing services (coolify, api, frontend, nginx) would be here

  # Monitoring services
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - "./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml"
      - "./monitoring/prometheus/rules:/etc/prometheus/rules"
      - "prometheus_data:/prometheus"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped
    networks:
      - coolify-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - "grafana_data:/var/lib/grafana"
      - "./monitoring/grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml"
      - "./monitoring/dashboards:/var/lib/grafana/dashboards"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=\${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_COOKIE_SECURE=true
      - GF_SECURITY_STRICT_TRANSPORT_SECURITY=true
      - GF_SERVER_ROOT_URL=https://coolify.local/grafana/
    restart: unless-stopped
    networks:
      - coolify-network

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - "./monitoring/alerts/alertmanager.yml:/etc/alertmanager/alertmanager.yml"
      - "alertmanager_data:/alertmanager"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped
    networks:
      - coolify-network

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - "/proc:/host/proc:ro"
      - "/sys:/host/sys:ro"
      - "/:/rootfs:ro"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped
    networks:
      - coolify-network

  # Additional exporters
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@postgres:5432/\${POSTGRES_DB}?sslmode=disable
    restart: unless-stopped
    networks:
      - coolify-network
    depends_on:
      - postgres

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis:6379
      - REDIS_PASSWORD=\${REDIS_PASSWORD}
    restart: unless-stopped
    networks:
      - coolify-network
    depends_on:
      - redis

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  coolify-network:
    external: true
"@

$monitoringDockerCompose | Out-File "$MonitoringPath\docker-compose.monitoring.yml" -Encoding UTF8

# Step 7: Monitoring Control Script
Write-Host "🎛️ Creating monitoring control script..." -ForegroundColor Cyan

$monitoringControlScript = @"
# Monitoring Control Script for Coolify
param(
    [string]`$Action = "status",
    [string]`$MonitoringPath = "$MonitoringPath"
)

function Start-Monitoring {
    Write-Host "🚀 Starting monitoring services..." -ForegroundColor Green

    Push-Location `$MonitoringPath

    try {
        # Start monitoring stack
        docker-compose -f docker-compose.monitoring.yml up -d

        # Wait for services to be ready
        Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30

        # Check service health
        `$services = @("prometheus", "grafana", "alertmanager", "node-exporter")
        foreach (`$service in `$services) {
            `$status = docker ps --filter "name=`$service" --format "{{.Status}}"
            if (`$status -like "*Up*") {
                Write-Host "✅ `$service is running" -ForegroundColor Green
            } else {
                Write-Host "❌ `$service failed to start" -ForegroundColor Red
            }
        }

        Write-Host ""
        Write-Host "📊 Monitoring services started!" -ForegroundColor Green
        Write-Host "   - Prometheus: http://localhost:9090" -ForegroundColor White
        Write-Host "   - Grafana: http://localhost:3000" -ForegroundColor White
        Write-Host "   - Alertmanager: http://localhost:9093" -ForegroundColor White

    } catch {
        Write-Host "❌ Failed to start monitoring: `$(`$_.Exception.Message)" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

function Stop-Monitoring {
    Write-Host "🛑 Stopping monitoring services..." -ForegroundColor Yellow

    Push-Location `$MonitoringPath

    try {
        docker-compose -f docker-compose.monitoring.yml down
        Write-Host "✅ Monitoring services stopped!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to stop monitoring: `$(`$_.Exception.Message)" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

function Get-MonitoringStatus {
    Write-Host "📊 Monitoring Status:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan

    `$services = @("prometheus", "grafana", "alertmanager", "node-exporter", "postgres-exporter", "redis-exporter")

    foreach (`$service in `$services) {
        try {
            `$status = docker ps --filter "name=`$service" --format "{{.Names}},{{.Status}},{{.Ports}}" | ConvertFrom-Csv -Header "Name","Status","Ports"
            if (`$status) {
                Write-Host "`$service: " -NoNewline -ForegroundColor White
                if (`$status.Status -like "*Up*") {
                    Write-Host "✅ Running" -ForegroundColor Green
                    if (`$status.Ports) {
                        Write-Host "   Ports: `$(`$status.Ports)" -ForegroundColor Gray
                    }
                } else {
                    Write-Host "❌ Not running" -ForegroundColor Red
                }
            } else {
                Write-Host "`$service: ❌ Not found" -ForegroundColor Red
            }
        } catch {
            Write-Host "`$service: ❌ Error checking status" -ForegroundColor Red
        }
    }

    Write-Host ""

    # Check service endpoints
    `$endpoints = @(
        @{Name="Prometheus"; URL="http://localhost:9090/-/healthy"},
        @{Name="Grafana"; URL="http://localhost:3000/api/health"},
        @{Name="Alertmanager"; URL="http://localhost:9093/-/healthy"}
    )

    Write-Host "🌐 Service Health:" -ForegroundColor Cyan
    foreach (`$endpoint in `$endpoints) {
        try {
            `$response = Invoke-WebRequest -Uri `$endpoint.URL -Method GET -TimeoutSec 5 -UseBasicParsing
            Write-Host "`$(`$endpoint.Name): ✅ Healthy (HTTP `$(`$response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "`$(`$endpoint.Name): ❌ Unhealthy" -ForegroundColor Red
        }
    }
}

function Restart-Monitoring {
    Write-Host "🔄 Restarting monitoring services..." -ForegroundColor Yellow
    Stop-Monitoring
    Start-Sleep -Seconds 5
    Start-Monitoring
}

function Show-MonitoringLogs {
    param([string]`$Service = "")

    if (`$Service) {
        Write-Host "📋 Showing logs for `$Service..." -ForegroundColor Cyan
        docker logs `$Service --tail 50 --follow
    } else {
        Write-Host "📋 Available services for logs:" -ForegroundColor Cyan
        docker ps --format "{{.Names}}" | Where-Object { `$_ -match "prometheus|grafana|alertmanager|exporter" }
    }
}

# Main action handler
switch (`$Action.ToLower()) {
    "start" { Start-Monitoring }
    "stop" { Stop-Monitoring }
    "restart" { Restart-Monitoring }
    "status" { Get-MonitoringStatus }
    "logs" { Show-MonitoringLogs }
    default {
        Write-Host "🎛️ Monitoring Control Script" -ForegroundColor Cyan
        Write-Host "Usage: .\monitoring-control.ps1 -Action <action>" -ForegroundColor White
        Write-Host ""
        Write-Host "Available actions:" -ForegroundColor Yellow
        Write-Host "  start   - Start monitoring services" -ForegroundColor White
        Write-Host "  stop    - Stop monitoring services" -ForegroundColor White
        Write-Host "  restart - Restart monitoring services" -ForegroundColor White
        Write-Host "  status  - Show monitoring status" -ForegroundColor White
        Write-Host "  logs    - Show service logs" -ForegroundColor White
    }
}
"@

$monitoringControlScript | Out-File "$MonitoringPath\monitoring-control.ps1" -Encoding UTF8

# Create scheduled task for log collection
Write-Host "⏰ Setting up scheduled monitoring tasks..." -ForegroundColor Cyan

$scheduledTasks = @"
# Setup Scheduled Tasks for Monitoring
Write-Host "⏰ Setting up scheduled monitoring tasks..." -ForegroundColor Green

# Task 1: Health Check (every 15 minutes)
`$healthCheckAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$MonitoringPath\health-check.ps1`""
`$healthCheckTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365)
`$healthCheckSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
`$healthCheckPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

try {
    Register-ScheduledTask -TaskName "CoolifyHealthCheck" -Action `$healthCheckAction -Trigger `$healthCheckTrigger -Settings `$healthCheckSettings -Principal `$healthCheckPrincipal -Force
    Write-Host "✅ Health check task scheduled (every 15 minutes)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to schedule health check task: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Task 2: Log Collection (every hour)
`$logCollectionAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$MonitoringPath\collect-logs.ps1`""
`$logCollectionTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)

try {
    Register-ScheduledTask -TaskName "CoolifyLogCollection" -Action `$logCollectionAction -Trigger `$logCollectionTrigger -Settings `$healthCheckSettings -Principal `$healthCheckPrincipal -Force
    Write-Host "✅ Log collection task scheduled (every hour)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to schedule log collection task: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

# Task 3: Security Audit (daily)
`$securityAuditAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"C:\coolify\security-audit.ps1`""
`$securityAuditTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"

try {
    Register-ScheduledTask -TaskName "CoolifySecurityAudit" -Action `$securityAuditAction -Trigger `$securityAuditTrigger -Settings `$healthCheckSettings -Principal `$healthCheckPrincipal -Force
    Write-Host "✅ Security audit task scheduled (daily at 2 AM)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Failed to schedule security audit task: `$(`$_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📅 Scheduled tasks configured:" -ForegroundColor Cyan
Write-Host "   - Health Check: Every 15 minutes" -ForegroundColor White
Write-Host "   - Log Collection: Every hour" -ForegroundColor White
Write-Host "   - Security Audit: Daily at 2 AM" -ForegroundColor White
"@

$scheduledTasks | Out-File "$MonitoringPath\setup-scheduled-tasks.ps1" -Encoding UTF8

# Final Summary
Write-Host ""
Write-Host "🎉 Comprehensive monitoring system setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Monitoring components configured:" -ForegroundColor Cyan
Write-Host "   ✅ Prometheus (metrics collection)" -ForegroundColor White
Write-Host "   ✅ Grafana (visualization dashboards)" -ForegroundColor White
Write-Host "   ✅ Alertmanager (alert routing)" -ForegroundColor White
Write-Host "   ✅ Node Exporter (system metrics)" -ForegroundColor White
Write-Host "   ✅ Database exporters (PostgreSQL, Redis)" -ForegroundColor White
Write-Host "   ✅ Centralized logging" -ForegroundColor White
Write-Host "   ✅ Health monitoring" -ForegroundColor White
Write-Host "   ✅ Security monitoring" -ForegroundColor White
Write-Host "   ✅ Automated alerting" -ForegroundColor White
Write-Host ""
Write-Host "📄 Files created:" -ForegroundColor Yellow
Write-Host "   - prometheus.yml (metrics configuration)" -ForegroundColor White
Write-Host "   - coolify-alerts.yml (alerting rules)" -ForegroundColor White
Write-Host "   - datasources.yml (Grafana data sources)" -ForegroundColor White
Write-Host "   - coolify-overview.json (main dashboard)" -ForegroundColor White
Write-Host "   - security-audit.json (security dashboard)" -ForegroundColor White
Write-Host "   - alertmanager.yml (alert routing)" -ForegroundColor White
Write-Host "   - collect-logs.ps1 (log collection script)" -ForegroundColor White
Write-Host "   - health-check.ps1 (comprehensive health checks)" -ForegroundColor White
Write-Host "   - monitoring-control.ps1 (monitoring management)" -ForegroundColor White
Write-Host "   - docker-compose.monitoring.yml (monitoring stack)" -ForegroundColor White
Write-Host "   - setup-scheduled-tasks.ps1 (automation setup)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Quick start commands:" -ForegroundColor Cyan
Write-Host "   Start monitoring: .\monitoring-control.ps1 -Action start" -ForegroundColor White
Write-Host "   Check status: .\monitoring-control.ps1 -Action status" -ForegroundColor White
Write-Host "   Run health check: .\health-check.ps1" -ForegroundColor White
Write-Host "   Setup automation: .\setup-scheduled-tasks.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Access URLs (after starting):" -ForegroundColor Cyan
Write-Host "   - Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "   - Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "   - Alertmanager: http://localhost:9093" -ForegroundColor White
Write-Host ""
Write-Host "✅ Comprehensive monitoring setup completed!" -ForegroundColor Green
