$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backendRoot = Join-Path $repoRoot "backend"
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$envPath = Join-Path $backendRoot ".env"
$serverProcess = $null
$exitCode = 0

function Get-ConfigValue {
    param(
        [string]$Path,
        [string]$Name,
        [string]$DefaultValue
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $DefaultValue
    }
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        if ($line -match ('^\s*' + [regex]::Escape($Name) + '\s*=\s*(.*)\s*$')) {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $DefaultValue
}

function Get-ResponseStatusCode {
    param($ErrorRecord)

    try {
        if ($null -ne $ErrorRecord.Exception.Response -and $null -ne $ErrorRecord.Exception.Response.StatusCode) {
            return [int]$ErrorRecord.Exception.Response.StatusCode
        }
    }
    catch {
    }
    return "unavailable"
}

function Invoke-ApiCheck {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Uri,
        $Body
    )

    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Method Get -Uri $Uri -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        }
        else {
            $jsonBody = $Body | ConvertTo-Json -Depth 20
            $response = Invoke-RestMethod -Method Post -Uri $Uri -Body $jsonBody -ContentType "application/json" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        }
        Write-Host "PASS: $Name HTTP 200"
        return $response
    }
    catch {
        $statusCode = Get-ResponseStatusCode -ErrorRecord $_
        $message = $_.Exception.Message
        Write-Host "FAIL: $Name HTTP $statusCode - $message"
        throw "API check failed for $Name."
    }
}

try {
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw "The repository virtual environment was not found at $pythonPath. Run backend\scripts\setup_backend.ps1 first."
    }
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        throw "backend\.env was not found. Run backend\scripts\setup_backend.ps1 first."
    }
    $portText = Get-ConfigValue -Path $envPath -Name "API_PORT" -DefaultValue "8000"
    $port = 0
    if (-not [int]::TryParse($portText, [ref]$port) -or $port -lt 1 -or $port -gt 65535) {
        throw "API_PORT in backend\.env must be a valid TCP port."
    }

    $baseUrl = "http://127.0.0.1:$port"
    $serverProcess = Start-Process `
        -FilePath $pythonPath `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$port") `
        -WorkingDirectory $backendRoot `
        -WindowStyle Hidden `
        -PassThru

    $ready = $false
    $lastReadyError = ""
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($serverProcess.HasExited) {
            throw "Uvicorn exited before /docs became ready (process exit code $($serverProcess.ExitCode))."
        }
        try {
            $null = Invoke-RestMethod -Method Get -Uri "$baseUrl/docs" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            $ready = $true
            break
        }
        catch {
            $lastReadyError = $_.Exception.Message
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        throw "Uvicorn did not become ready at $baseUrl/docs within 60 seconds. Last request error: $lastReadyError"
    }
    Write-Host "PASS: Uvicorn ready at $baseUrl/docs"

    $riskUri = "$baseUrl/api/risk?lat=28.75&lon=77.1&activity=walking&duration_min=30&profile=general"
    $null = Invoke-ApiCheck -Name "/api/risk" -Method "GET" -Uri $riskUri

    $bbox = "77.04,28.70,77.14,28.78"
    $heatmapUri = "$baseUrl/api/heatmap?bbox=$bbox&ts=latest"
    $heatmap = Invoke-ApiCheck -Name "/api/heatmap" -Method "GET" -Uri $heatmapUri

    $routeBody = @{
        origin = @{ lat = 28.74; lon = 77.1 }
        dest = @{ lat = 28.76; lon = 77.12 }
        activity = "walking"
    }
    $null = Invoke-ApiCheck -Name "/api/route" -Method "POST" -Uri "$baseUrl/api/route" -Body $routeBody

    $resourcesUri = "$baseUrl/api/resources?type=water&lat=28.75&lon=77.1&radius_m=2000"
    $null = Invoke-ApiCheck -Name "/api/resources" -Method "GET" -Uri $resourcesUri

    $optimizeBody = @{
        budget_inr = 60000
        bbox = @(77.04, 28.70, 77.14, 28.78)
    }
    $null = Invoke-ApiCheck -Name "/api/optimize" -Method "POST" -Uri "$baseUrl/api/optimize" -Body $optimizeBody

    if ($null -eq $heatmap -or $null -eq $heatmap.features -or $heatmap.features.Count -lt 1) {
        throw "/api/heatmap returned no feature to use as a valid simulation target."
    }
    $simulateBody = @{
        interventions = @(
            @{
                cell_id = $heatmap.features[0].properties.cell_id
                type = "shade"
                units = 1
            }
        )
    }
    $null = Invoke-ApiCheck -Name "/api/simulate" -Method "POST" -Uri "$baseUrl/api/simulate" -Body $simulateBody

    $null = Invoke-ApiCheck -Name "/docs" -Method "GET" -Uri "$baseUrl/docs"
}
catch {
    $exitCode = 1
    Write-Host "FAIL: $($_.Exception.Message)"
}
finally {
    if ($null -ne $serverProcess) {
        try {
            if (-not $serverProcess.HasExited) {
                Stop-Process -Id $serverProcess.Id -Force -ErrorAction Stop
                Write-Host "Stopped Uvicorn process $($serverProcess.Id)."
            }
        }
        catch {
            if ($exitCode -eq 0) {
                $exitCode = 1
            }
            Write-Host "FAIL: Could not stop Uvicorn process $($serverProcess.Id): $($_.Exception.Message)"
        }
        $serverProcess.Dispose()
    }
}

if ($exitCode -ne 0) {
    exit $exitCode
}
