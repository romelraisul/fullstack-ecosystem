# Quick system + stack diagnostics
$ErrorActionPreference = 'Stop'

function Write-Json($obj) {
    $obj | ConvertTo-Json -Depth 6
}

# 1) System specs
$os = Get-CimInstance -ClassName Win32_OperatingSystem
$cpu = Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1
$cs = Get-CimInstance -ClassName Win32_ComputerSystem
$uptimeDays = [Math]::Round(((Get-Date) - $os.LastBootUpTime).TotalDays, 2)
$memGB = [Math]::Round(($cs.TotalPhysicalMemory / 1GB), 2)
$sys = [pscustomobject]@{
    computer    = $env:COMPUTERNAME
    os          = $os.Caption
    os_version  = $os.Version
    uptime_days = $uptimeDays
    cpu_name    = $cpu.Name
    cpu_cores   = $cpu.NumberOfCores
    cpu_threads = $cpu.NumberOfLogicalProcessors
    mem_gb      = $memGB
}

# 2) Docker resources (if available)
$dockerInfo = $null
try {
    $dockerInfo = docker info --format '{{json .}}' | ConvertFrom-Json
}
catch {}

$docker = $null
if ($dockerInfo) {
    $docker = [pscustomobject]@{
        server_version = $dockerInfo.ServerVersion
        cgroup_driver  = $dockerInfo.CgroupDriver
        cpus           = $dockerInfo.NCPU
        mem_total_gb   = if ($dockerInfo.MemTotal) { [Math]::Round($dockerInfo.MemTotal / 1GB, 2) } else { $null }
        running        = $dockerInfo.ContainersRunning
        images         = $dockerInfo.Images
    }
}

# 3) Local services latency
function Test-Latency($url) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $resp = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 5
        $sw.Stop()
        return [pscustomobject]@{ url = $url; status = $resp.StatusCode; ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2) }
    }
    catch {
        return [pscustomobject]@{ url = $url; status = 'ERR'; ms = $null; error = $_.Exception.Message }
    }
}
$apiHealth = Test-Latency 'http://localhost:8010/health'
$gateway = Test-Latency 'http://localhost:5125/'

# 4) Disk throughput
$disk = $null
try {
    $temp = [System.IO.Path]::GetTempPath()
    $file = Join-Path $temp "diag_$(Get-Random).bin"
    $sizeMB = 256
    $bytes = New-Object byte[] ($sizeMB * 1MB)
    (New-Object System.Random).NextBytes($bytes)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    [System.IO.File]::WriteAllBytes($file, $bytes)
    $sw.Stop()
    $writeMBps = [Math]::Round(($sizeMB / $sw.Elapsed.TotalSeconds), 2)

    $sw.Restart()
    $data = [System.IO.File]::ReadAllBytes($file)
    $sw.Stop()
    $readMBps = [Math]::Round(($sizeMB / $sw.Elapsed.TotalSeconds), 2)
    Remove-Item -Force $file -ErrorAction SilentlyContinue
    $disk = [pscustomobject]@{ size_mb = $sizeMB; write_MBps = $writeMBps; read_MBps = $readMBps }
}
catch {}

# 5) Network latency + bandwidth (quick)
$net = $null
try {
    $p1 = Test-Connection -ComputerName 1.1.1.1 -Count 4 -ErrorAction Stop
    $p2 = Test-Connection -ComputerName 8.8.8.8 -Count 4 -ErrorAction Stop
    $avg1 = [Math]::Round(($p1 | Measure-Object -Property ResponseTime -Average).Average, 2)
    $avg2 = [Math]::Round(($p2 | Measure-Object -Property ResponseTime -Average).Average, 2)

    $downloadUrl = 'https://speed.cloudflare.com/__down?bytes=10000000'
    $wc = New-Object System.Net.WebClient
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $null = $wc.DownloadData($downloadUrl)
    $sw.Stop()
    $mbps = [Math]::Round(((10 / $sw.Elapsed.TotalSeconds) * 8), 2) # 10 MB -> MBytes/sec * 8 -> Mbps

    $net = [pscustomobject]@{
        ping_avg_ms_1_1_1_1 = $avg1
        ping_avg_ms_8_8_8_8 = $avg2
        est_download_mbps   = $mbps
    }
}
catch {}

# Aggregate
$result = [pscustomobject]@{
    system   = $sys
    docker   = $docker
    services = [pscustomobject]@{ api = $apiHealth; gateway = $gateway }
    disk     = $disk
    network  = $net
}

Write-Json $result
