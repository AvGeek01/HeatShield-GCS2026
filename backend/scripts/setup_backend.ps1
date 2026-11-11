param(
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$script:BackendRoot = Join-Path $script:RepoRoot "backend"
$script:Results = New-Object System.Collections.Generic.List[object]
$script:StepNames = @(
    "1. Python version and virtual environment",
    "2. Install backend requirements",
    "2a. Verify backend imports",
    "2b. Write backend requirements lock",
    "3. Create and configure backend environment file",
    "4. Verify backend environment file is git-ignored",
    "5a. Verify Docker daemon",
    "5b. Validate Docker Compose configuration",
    "5c. Start database and wait for healthy status",
    "6a. Apply Alembic migration",
    "6b. Verify PostGIS, schema tables, and spatial indexes",
    "6c. Reverse Alembic migration",
    "6d. Reapply Alembic migration",
    "7. Run repository tests",
    "8. Write setup summary"
)
$script:PackageVersions = "(not installed)"
$script:PythonVersion = "(not detected)"
$script:TestCounts = "total=0, passed=0, failed=0"
$script:GeneratedPassword = $null
$script:FailureMessage = $null
$script:VenvPython = Join-Path $script:RepoRoot ".venv\Scripts\python.exe"
$script:VenvScripts = Join-Path $script:RepoRoot ".venv\Scripts"

function Protect-Text {
    param([string]$Text)

    if ($null -eq $Text) {
        return ""
    }

    $safeText = $Text
    if (-not [string]::IsNullOrEmpty($script:GeneratedPassword)) {
        $safeText = $safeText.Replace($script:GeneratedPassword, "[REDACTED]")
    }
    $safeText = [regex]::Replace(
        $safeText,
        '(?i)(https?://)[^:/@\s]+:[^@\s]+@',
        '$1[REDACTED]@'
    )
    $safeText = [regex]::Replace(
        $safeText,
        '(?i)(https?://)[^/@\s]+@',
        '$1[REDACTED]@'
    )
    return $safeText
}

function Get-DotEnvValues {
    param([string]$Path)

    $values = @{}
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if ($value.Length -ge 2 -and
                (($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $values[$key] = $value
        }
    }
    return $values
}

function Invoke-NativeCommand {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$Description,
        [switch]$StreamOutput
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($StreamOutput) {
            $outputLines = New-Object System.Collections.Generic.List[string]
            & $FilePath @Arguments 2>&1 | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) {
                    $line = $_.ToString()
                }
                else {
                    $line = "$_"
                }
                $outputLines.Add($line)
                Write-Host (Protect-Text $line)
            }
            $exitCode = $LASTEXITCODE
            $text = $outputLines -join [Environment]::NewLine
        }
        else {
            $output = @(& $FilePath @Arguments 2>&1)
            $exitCode = $LASTEXITCODE
            $text = ($output | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) {
                    $_.ToString()
                }
                else {
                    "$_"
                }
            }) -join [Environment]::NewLine
        }
    }
    catch {
        $exceptionText = $_.ToString()
        if ([string]::IsNullOrWhiteSpace($exceptionText)) {
            $exceptionText = $_.Exception.GetType().FullName
        }
        throw ("Could not run {0} {1}. PowerShell error: {2}" -f $FilePath, ($Arguments -join " "), $exceptionText)
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($null -eq $exitCode) {
        $exitCode = 0
    }
    if ($exitCode -ne 0) {
        if ([string]::IsNullOrWhiteSpace($text)) {
            $text = "(the command produced no captured output)"
        }
        throw ("{0} exited with code {1}. Output:{2}{3}" -f $Description, $exitCode, [Environment]::NewLine, $text)
    }
    if (-not [string]::IsNullOrWhiteSpace($text)) {
        Write-Verbose (Protect-Text $text)
    }
    return $text
}

function Add-StepResult {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Detail
    )

    $script:Results.Add([pscustomobject]@{
        Name = $Name
        Status = $Status
        Detail = Protect-Text $Detail
    }) | Out-Null
}

function Invoke-SetupStep {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    try {
        Write-Host "RUNNING: $Name"
        $actionOutput = @(& $Action)
        $detail = ($actionOutput | ForEach-Object { "$_" }) -join "; "
        Add-StepResult -Name $Name -Status "PASS" -Detail $detail
        if ([string]::IsNullOrWhiteSpace($detail)) {
            Write-Host "PASS: $Name"
        }
        else {
            Write-Host ("PASS: {0} - {1}" -f $Name, (Protect-Text $detail))
        }
    }
    catch {
        $exactError = $_.ToString()
        if ([string]::IsNullOrWhiteSpace($exactError)) {
            $exactError = $_.Exception.GetType().FullName
        }
        $exactError = Protect-Text $exactError
        $plainMessage = "The step could not be completed."
        Add-StepResult -Name $Name -Status "FAIL" -Detail ("{0} Exact error: {1}" -f $plainMessage, $exactError)
        $script:FailureMessage = "FAIL: $Name. $plainMessage Exact error: $exactError"
        Write-Host $script:FailureMessage
        throw "Setup stopped after the first failed step."
    }
}

function New-DevelopmentPassword {
    $characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes = New-Object byte[] 24
    $random.GetBytes($bytes)
    $builder = New-Object System.Text.StringBuilder
    foreach ($byte in $bytes) {
        [void]$builder.Append($characters[[int]$byte % $characters.Length])
    }
    $random.Dispose()
    return $builder.ToString()
}

function Set-ComposeDatabasePassword {
    param(
        [string]$DatabaseUser,
        [string]$DatabaseName,
        [string]$Password
    )

    if ($DatabaseUser -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
        throw "POSTGRES_USER must be a plain PostgreSQL identifier before the local database password can be synchronized."
    }
    if ([string]::IsNullOrWhiteSpace($DatabaseName) -or $DatabaseName.Contains('"')) {
        throw "POSTGRES_DB is not a supported database name for local credential synchronization."
    }

    $dockerCommand = Get-Command "docker" -ErrorAction SilentlyContinue
    if ($null -eq $dockerCommand) {
        throw "The docker command was not found while synchronizing the local database password."
    }

    $escapedPassword = $Password.Replace("'", "''")
    $sql = 'ALTER ROLE "' + $DatabaseUser + '" WITH PASSWORD ''' + $escapedPassword + ''';'
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $dockerCommand.Source
    $startInfo.Arguments = 'compose exec -T db psql -X -v ON_ERROR_STOP=1 -U "' + $DatabaseUser + '" -d "' + $DatabaseName + '"'
    $startInfo.WorkingDirectory = $script:BackendRoot
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "Could not start docker compose exec to synchronize the local database password."
        }
        $process.StandardInput.WriteLine($sql)
        $process.StandardInput.Close()
        $standardOutput = $process.StandardOutput.ReadToEnd()
        $standardError = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        if ($process.ExitCode -ne 0) {
            $diagnostic = ($standardOutput + [Environment]::NewLine + $standardError).Trim()
            if ([string]::IsNullOrWhiteSpace($diagnostic)) {
                $diagnostic = "(psql returned no diagnostic output)"
            }
            throw ("Local database password synchronization failed with exit code {0}. Output: {1}" -f $process.ExitCode, (Protect-Text $diagnostic))
        }
    }
    finally {
        $process.Dispose()
    }
}

function Test-PasswordPlaceholder {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $true
    }
    return $Value -match '(?i)^(replace[-_ ]with.*|change[-_ ]?me|your[-_ ]?password|placeholder|dummy|<.*>|\$\{.*\}|\$.*)$'
}

function Get-SetupSummary {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("HeatShield backend setup summary")
    $lines.Add(("Generated: {0}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")))
    $lines.Add(("Repository: {0}" -f $script:RepoRoot))
    $lines.Add(("Python: {0}" -f $script:PythonVersion))
    $lines.Add("")
    $lines.Add("Steps:")

    foreach ($stepName in $script:StepNames) {
        $result = $script:Results | Where-Object { $_.Name -eq $stepName } | Select-Object -First 1
        if ($null -eq $result) {
            $status = "NOT RUN"
            $detail = "Setup stopped before this step."
            if ($SkipDocker -and $stepName -match '^(5|6)') {
                $status = "SKIP"
                $detail = "Docker verification was skipped by -SkipDocker."
            }
        }
        else {
            $status = $result.Status
            $detail = $result.Detail
        }
        $lines.Add(("{0}: {1} - {2}" -f $status, $stepName, (Protect-Text $detail)))
    }

    $lines.Add("")
    $lines.Add("Package versions:")
    $lines.Add((Protect-Text $script:PackageVersions))
    $lines.Add("")
    $lines.Add(("Tests: {0}" -f $script:TestCounts))
    if (-not [string]::IsNullOrWhiteSpace($script:FailureMessage)) {
        $lines.Add("")
        $lines.Add(("Failure: {0}" -f (Protect-Text $script:FailureMessage)))
    }
    return ($lines -join [Environment]::NewLine)
}

if ($SkipDocker) {
    foreach ($stepName in $script:StepNames) {
        if ($stepName -match '^(5|6)') {
            Add-StepResult -Name $stepName -Status "SKIP" -Detail "Docker verification was skipped by -SkipDocker."
        }
    }
}

try {
    Invoke-SetupStep -Name $script:StepNames[0] -Action {
        $pyCommand = Get-Command "py" -ErrorAction SilentlyContinue
        if ($null -eq $pyCommand) {
            throw "The Python launcher 'py' was not found on PATH."
        }
        $versionOutput = Invoke-NativeCommand -FilePath $pyCommand.Source -Arguments @("-3", "--version") -Description "py -3 --version"
        if ($versionOutput -notmatch 'Python\s+\d+\.\d+') {
            throw "The Python launcher did not report a recognizable Python version. Output: $versionOutput"
        }
        $script:PythonVersion = $versionOutput.Trim()

        $venvPath = Join-Path $script:RepoRoot ".venv"
        Push-Location $script:RepoRoot
        try {
            if (-not (Test-Path -LiteralPath $venvPath)) {
                $null = Invoke-NativeCommand -FilePath $pyCommand.Source -Arguments @("-3", "-m", "venv", ".venv") -Description "py -3 -m venv .venv"
            }
        }
        finally {
            Pop-Location
        }
        if (-not (Test-Path -LiteralPath $script:VenvPython)) {
            throw "The virtual environment was not created; expected $script:VenvPython."
        }

        $activatePath = Join-Path $script:VenvScripts "Activate.ps1"
        if (-not (Test-Path -LiteralPath $activatePath)) {
            throw "The virtual environment activation script is missing: $activatePath"
        }
        . $activatePath
        $env:VIRTUAL_ENV = Join-Path $script:RepoRoot ".venv"
        $env:Path = "$script:VenvScripts;$env:Path"
        return $script:PythonVersion
    }

    Invoke-SetupStep -Name $script:StepNames[1] -Action {
        $requirementsPath = Join-Path $script:BackendRoot "requirements.txt"
        $null = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments @("-m", "pip", "install", "-r", $requirementsPath) -Description "pip install -r backend\requirements.txt"
        return "Installed backend\requirements.txt using the repository .venv."
    }

    Invoke-SetupStep -Name $script:StepNames[2] -Action {
        $importOutput = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments @(
            "-c",
            "import fastapi, geoalchemy2, sqlalchemy, alembic; print('imports ok')"
        ) -Description "backend import verification"
        if ($importOutput -notmatch 'imports ok') {
            throw "The import verification command completed without the expected 'imports ok' output. Output: $importOutput"
        }
        return $importOutput.Trim()
    }

    Invoke-SetupStep -Name $script:StepNames[3] -Action {
        $freezeOutput = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments @("-m", "pip", "freeze") -Description "pip freeze"
        $script:PackageVersions = $freezeOutput.Trim()
        $lockPath = Join-Path $script:BackendRoot "requirements.lock.txt"
        $lockLines = @()
        if (-not [string]::IsNullOrWhiteSpace($freezeOutput)) {
            $lockLines = $freezeOutput -split "\r?\n"
        }
        [System.IO.File]::WriteAllLines($lockPath, $lockLines, ([System.Text.UTF8Encoding]::new($false)))
        return "Wrote backend\requirements.lock.txt."
    }

    Invoke-SetupStep -Name $script:StepNames[4] -Action {
        $examplePath = Join-Path $script:BackendRoot ".env.example"
        $envPath = Join-Path $script:BackendRoot ".env"
        if (-not (Test-Path -LiteralPath $examplePath -PathType Leaf)) {
            throw "The environment template is missing: $examplePath"
        }
        if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
            Copy-Item -LiteralPath $examplePath -Destination $envPath
        }

        $envLines = [System.IO.File]::ReadAllLines($envPath)
        $hadMalformedGeneratedLine = $false
        $cleanEnvLines = New-Object System.Collections.Generic.List[string]
        foreach ($line in $envLines) {
            if ($line -match '^\$[A-Za-z0-9]{20,40}$') {
                $hadMalformedGeneratedLine = $true
                continue
            }
            $cleanEnvLines.Add($line)
        }
        $envLines = $cleanEnvLines.ToArray()
        $existingKeys = @{}
        foreach ($line in $envLines) {
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
                $existingKeys[$Matches[1]] = $true
            }
        }
        foreach ($exampleLine in [System.IO.File]::ReadAllLines($examplePath)) {
            if ($exampleLine -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
                $exampleKey = $Matches[1]
                if (-not $existingKeys.ContainsKey($exampleKey)) {
                    $envLines += $exampleLine
                    $existingKeys[$exampleKey] = $true
                }
            }
        }

        $passwordLine = -1
        $currentPassword = $null
        $databaseUrlLine = -1
        $databaseUrl = $null
        for ($index = 0; $index -lt $envLines.Length; $index++) {
            if ($envLines[$index] -match '^\s*POSTGRES_PASSWORD\s*=\s*(.*)\s*$') {
                $passwordLine = $index
                $currentPassword = $Matches[1].Trim().Trim('"').Trim("'")
            }
            if ($envLines[$index] -match '^\s*DATABASE_URL\s*=\s*(.*)\s*$') {
                $databaseUrlLine = $index
                $databaseUrl = $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
        $script:GeneratedPassword = $currentPassword
        if ($passwordLine -lt 0 -or
            (Test-PasswordPlaceholder $currentPassword) -or
            $currentPassword.StartsWith('$') -or
            $hadMalformedGeneratedLine) {
            $script:GeneratedPassword = New-DevelopmentPassword
            if ($passwordLine -lt 0) {
                $envLines += "POSTGRES_PASSWORD=$($script:GeneratedPassword)"
                $passwordLine = $envLines.Length - 1
            }
            else {
                $envLines[$passwordLine] = "POSTGRES_PASSWORD=$($script:GeneratedPassword)"
            }
            if ($databaseUrlLine -ge 0 -and -not [string]::IsNullOrWhiteSpace($databaseUrl)) {
                $urlMatch = [regex]::Match(
                    $databaseUrl,
                    '^(?<prefix>[^:]+://[^:/@\s]+:)(?<password>[^@\s]*)@(?<suffix>.+)$'
                )
                if (-not $urlMatch.Success) {
                    throw "DATABASE_URL does not contain a replaceable username/password pair; no password was written to it."
                }
                $updatedUrl = $urlMatch.Groups["prefix"].Value + $script:GeneratedPassword + "@" + $urlMatch.Groups["suffix"].Value
                $envLines[$databaseUrlLine] = "DATABASE_URL=$updatedUrl"
            }
            [System.IO.File]::WriteAllLines($envPath, $envLines, ([System.Text.UTF8Encoding]::new($false)))
        }
        else {
            # Keep newly merged template keys in the existing env file as well.
            [System.IO.File]::WriteAllLines($envPath, $envLines, ([System.Text.UTF8Encoding]::new($false)))
        }

        $envValues = Get-DotEnvValues -Path $envPath
        $requiredKeys = @("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "API_PORT", "DATABASE_URL", "CORS_ORIGINS")
        foreach ($key in $requiredKeys) {
            if (-not $envValues.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($envValues[$key])) {
                throw "Required environment variable '$key' is missing or empty in backend\.env."
            }
        }
        if (Test-PasswordPlaceholder $envValues["POSTGRES_PASSWORD"]) {
            throw "POSTGRES_PASSWORD is still empty or a placeholder in backend\.env."
        }
        $script:GeneratedPassword = $envValues["POSTGRES_PASSWORD"]
        $databaseUrlMatch = [regex]::Match(
            $envValues["DATABASE_URL"],
            '^(?<scheme>postgresql(?:\+psycopg)?://)(?<user>[^:/@\s]+):(?<password>[^@\s]*)@(?<host>[^:/\s]+):(?<port>\d+)/(?<database>[^?\s]+)'
        )
        if (-not $databaseUrlMatch.Success -or
            $databaseUrlMatch.Groups["user"].Value -ne $envValues["POSTGRES_USER"] -or
            $databaseUrlMatch.Groups["password"].Value -ne $envValues["POSTGRES_PASSWORD"] -or
            $databaseUrlMatch.Groups["host"].Value -ne $envValues["POSTGRES_HOST"] -or
            $databaseUrlMatch.Groups["port"].Value -ne $envValues["POSTGRES_PORT"] -or
            $databaseUrlMatch.Groups["database"].Value -ne $envValues["POSTGRES_DB"]) {
            throw "DATABASE_URL must match the POSTGRES user, password, host, port, and database settings in backend\.env."
        }
        foreach ($key in $requiredKeys) {
            Set-Item -Path ("Env:" + $key) -Value $envValues[$key]
        }
        return "backend\.env is present and configured; its password was not displayed."
    }

    Invoke-SetupStep -Name $script:StepNames[5] -Action {
        Push-Location $script:RepoRoot
        try {
            $ignoreOutput = Invoke-NativeCommand -FilePath "git" -Arguments @("check-ignore", "-v", "backend/.env") -Description "git check-ignore -v backend/.env"
            if ([string]::IsNullOrWhiteSpace($ignoreOutput)) {
                throw "Git did not report an ignore rule for backend/.env."
            }
        }
        finally {
            Pop-Location
        }
        return "Git confirms backend/.env is ignored."
    }

    if (-not $SkipDocker) {
        Invoke-SetupStep -Name $script:StepNames[6] -Action {
            $dockerOutput = Invoke-NativeCommand -FilePath "docker" -Arguments @("info") -Description "docker info"
            if ($dockerOutput -notmatch '(?m)^Server:') {
                throw "docker info completed but did not include a Server section."
            }
            return "docker info includes a Server section."
        }

        Invoke-SetupStep -Name $script:StepNames[7] -Action {
            Push-Location $script:BackendRoot
            try {
                $null = Invoke-NativeCommand -FilePath "docker" -Arguments @("compose", "config") -Description "docker compose config"
            }
            finally {
                Pop-Location
            }
            return "docker compose config resolved successfully."
        }

        Invoke-SetupStep -Name $script:StepNames[8] -Action {
            Push-Location $script:BackendRoot
            try {
                $null = Invoke-NativeCommand -FilePath "docker" -Arguments @("compose", "up", "-d", "db") -Description "docker compose up -d db"
                $psOutput = Invoke-NativeCommand -FilePath "docker" -Arguments @("compose", "ps") -Description "docker compose ps"
                Write-Host (Protect-Text $psOutput)
                $containerId = (Invoke-NativeCommand -FilePath "docker" -Arguments @("compose", "ps", "-q", "db") -Description "docker compose ps -q db").Trim()
                if ([string]::IsNullOrWhiteSpace($containerId)) {
                    throw "Docker Compose did not return a container ID for service db."
                }

                $deadline = (Get-Date).AddSeconds(90)
                $healthStatus = ""
                do {
                    $inspectOutput = Invoke-NativeCommand -FilePath "docker" -Arguments @(
                        "inspect",
                        "--format",
                        "{{.State.Health.Status}}",
                        $containerId
                    ) -Description "docker inspect database health"
                    $healthStatus = $inspectOutput.Trim()
                    if ($healthStatus -eq "healthy") {
                        break
                    }
                    if ($healthStatus -eq "unhealthy") {
                        throw "The db container reported unhealthy before the 90-second deadline."
                    }
                    Start-Sleep -Seconds 3
                } while ((Get-Date) -lt $deadline)
                if ($healthStatus -ne "healthy") {
                    throw "The db service did not become healthy within 90 seconds; last health status was '$healthStatus'."
                }
            }
            finally {
                Pop-Location
            }
            return "The db service is healthy."
        }

        Invoke-SetupStep -Name $script:StepNames[9] -Action {
            Push-Location $script:BackendRoot
            $previousPgConnectTimeout = $env:PGCONNECT_TIMEOUT
            $previousPgOptions = $env:PGOPTIONS
            $previousDatabaseUrl = $env:DATABASE_URL
            try {
                $localDatabaseUrl = [regex]::Match(
                    $env:DATABASE_URL,
                    '^(?<prefix>postgresql(?:\+psycopg)?://[^:/@\s]+:[^@\s]*@)(?<host>[^:/\s]+)(?<suffix>:\d+/.+)$'
                )
                if (-not $localDatabaseUrl.Success) {
                    throw "DATABASE_URL is not a supported PostgreSQL URL for a local Alembic run."
                }
                $env:DATABASE_URL = $localDatabaseUrl.Groups["prefix"].Value + "127.0.0.1" + $localDatabaseUrl.Groups["suffix"].Value
                $env:PGCONNECT_TIMEOUT = "10"
                $env:PGOPTIONS = "-c lock_timeout=10000 -c statement_timeout=60000"
                Write-Host "Checking PostgreSQL connection (10-second timeout)..."
                $preflightArguments = @(
                    "-c",
                    "import os; from sqlalchemy import create_engine, text; url=os.environ['DATABASE_URL']; url=url.replace('postgresql://','postgresql+psycopg://',1) if url.startswith('postgresql://') else url; engine=create_engine(url, connect_args={'connect_timeout': 10}); connection=engine.connect(); print('database connection ok:', connection.execute(text('SELECT 1')).scalar()); connection.close(); engine.dispose()"
                )
                try {
                    $preflight = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments $preflightArguments -Description "PostgreSQL connection preflight" -StreamOutput
                }
                catch {
                    if ($_.Exception.Message -notmatch '(?i)password authentication failed') {
                        throw
                    }
                    Write-Host "PostgreSQL rejected the configured password. Updating the local database role through the db container without displaying the password..."
                    Set-ComposeDatabasePassword -DatabaseUser $env:POSTGRES_USER -DatabaseName $env:POSTGRES_DB -Password $env:POSTGRES_PASSWORD
                    Write-Host "Retrying PostgreSQL connection..."
                    $preflight = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments $preflightArguments -Description "PostgreSQL connection preflight after local credential synchronization" -StreamOutput
                }
                if ($preflight -notmatch 'database connection ok:\s*1') {
                    throw "PostgreSQL connection preflight did not confirm SELECT 1."
                }
                Write-Host "Running Alembic with a 10-second lock timeout and 60-second statement timeout..."
                $null = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments @("-m", "alembic", "upgrade", "head") -Description "python -m alembic upgrade head" -StreamOutput
            }
            finally {
                $env:PGCONNECT_TIMEOUT = $previousPgConnectTimeout
                $env:PGOPTIONS = $previousPgOptions
                $env:DATABASE_URL = $previousDatabaseUrl
                Pop-Location
            }
            return "PostgreSQL preflight and alembic upgrade head succeeded from backend\."
        }

        Invoke-SetupStep -Name $script:StepNames[10] -Action {
            $dbUser = $env:POSTGRES_USER
            $dbName = $env:POSTGRES_DB
            Push-Location $script:BackendRoot
            try {
                $postgisOutput = Invoke-NativeCommand -FilePath "docker" -Arguments @(
                    "compose", "exec", "-T", "db", "psql", "-U", $dbUser, "-d", $dbName, "-c", "SELECT postgis_version();"
                ) -Description "PostGIS version query"
                $null = Invoke-NativeCommand -FilePath "docker" -Arguments @(
                    "compose", "exec", "-T", "db", "psql", "-U", $dbUser, "-d", $dbName, "-c", "\dt"
                ) -Description "psql \dt"
                $null = Invoke-NativeCommand -FilePath "docker" -Arguments @(
                    "compose", "exec", "-T", "db", "psql", "-U", $dbUser, "-d", $dbName, "-c", "\di"
                ) -Description "psql \di"
                $tablesOutput = Invoke-NativeCommand -FilePath "docker" -Arguments @(
                    "compose", "exec", "-T", "db", "psql", "-U", $dbUser, "-d", $dbName, "-At", "-c",
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
                ) -Description "public table verification query"
                $tableNames = @($tablesOutput -split "\r?\n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
                $expectedTables = @("nodes", "readings", "resources", "grid_cells", "interventions", "pilot_surveys")
                $missingTables = @($expectedTables | Where-Object { $tableNames -notcontains $_ })
                if ($missingTables.Count -gt 0) {
                    throw ("Expected schema table(s) are missing: {0}" -f ($missingTables -join ", "))
                }
                $gistOutput = Invoke-NativeCommand -FilePath "docker" -Arguments @(
                    "compose", "exec", "-T", "db", "psql", "-U", $dbUser, "-d", $dbName, "-At", "-c",
                    "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexdef ILIKE '%USING gist%';"
                ) -Description "spatial GIST index verification query"
                $gistIndexes = @($gistOutput -split "\r?\n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
                if ($gistIndexes.Count -lt 4) {
                    throw ("Expected at least four spatial GIST indexes; found {0}." -f $gistIndexes.Count)
                }
                if ($postgisOutput -notmatch '(?i)postgis') {
                    throw "The PostGIS version query did not return a PostGIS version."
                }
                Write-Host (Protect-Text $postgisOutput.Trim())
            }
            finally {
                Pop-Location
            }
            return ("Verified tables: {0}; GIST indexes: {1}." -f ($expectedTables -join ", "), ($gistIndexes -join ", "))
        }

        Invoke-SetupStep -Name $script:StepNames[11] -Action {
            Push-Location $script:BackendRoot
            $previousPgConnectTimeout = $env:PGCONNECT_TIMEOUT
            $previousPgOptions = $env:PGOPTIONS
            $previousDatabaseUrl = $env:DATABASE_URL
            try {
                $localDatabaseUrl = [regex]::Match(
                    $env:DATABASE_URL,
                    '^(?<prefix>postgresql(?:\+psycopg)?://[^:/@\s]+:[^@\s]*@)(?<host>[^:/\s]+)(?<suffix>:\d+/.+)$'
                )
                if (-not $localDatabaseUrl.Success) {
                    throw "DATABASE_URL is not a supported PostgreSQL URL for a local Alembic downgrade."
                }
                $env:DATABASE_URL = $localDatabaseUrl.Groups["prefix"].Value + "127.0.0.1" + $localDatabaseUrl.Groups["suffix"].Value
                $env:PGCONNECT_TIMEOUT = "10"
                $env:PGOPTIONS = "-c lock_timeout=10000 -c statement_timeout=60000"
                Write-Host "Running Alembic downgrade with a 10-second lock timeout and 60-second statement timeout..."
                $null = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments @("-m", "alembic", "downgrade", "base") -Description "python -m alembic downgrade base" -StreamOutput
            }
            finally {
                $env:PGCONNECT_TIMEOUT = $previousPgConnectTimeout
                $env:PGOPTIONS = $previousPgOptions
                $env:DATABASE_URL = $previousDatabaseUrl
                Pop-Location
            }
            return "alembic downgrade base succeeded."
        }

        Invoke-SetupStep -Name $script:StepNames[12] -Action {
            Push-Location $script:BackendRoot
            $previousPgConnectTimeout = $env:PGCONNECT_TIMEOUT
            $previousPgOptions = $env:PGOPTIONS
            $previousDatabaseUrl = $env:DATABASE_URL
            try {
                $localDatabaseUrl = [regex]::Match(
                    $env:DATABASE_URL,
                    '^(?<prefix>postgresql(?:\+psycopg)?://[^:/@\s]+:[^@\s]*@)(?<host>[^:/\s]+)(?<suffix>:\d+/.+)$'
                )
                if (-not $localDatabaseUrl.Success) {
                    throw "DATABASE_URL is not a supported PostgreSQL URL for a local Alembic upgrade."
                }
                $env:DATABASE_URL = $localDatabaseUrl.Groups["prefix"].Value + "127.0.0.1" + $localDatabaseUrl.Groups["suffix"].Value
                $env:PGCONNECT_TIMEOUT = "10"
                $env:PGOPTIONS = "-c lock_timeout=10000 -c statement_timeout=60000"
                Write-Host "Running Alembic upgrade with a 10-second lock timeout and 60-second statement timeout..."
                $null = Invoke-NativeCommand -FilePath $script:VenvPython -Arguments @("-m", "alembic", "upgrade", "head") -Description "python -m alembic upgrade head" -StreamOutput
            }
            finally {
                $env:PGCONNECT_TIMEOUT = $previousPgConnectTimeout
                $env:PGOPTIONS = $previousPgOptions
                $env:DATABASE_URL = $previousDatabaseUrl
                Pop-Location
            }
            return "alembic upgrade head succeeded after downgrade."
        }
    }

    Invoke-SetupStep -Name $script:StepNames[13] -Action {
        Push-Location $script:RepoRoot
        try {
            $pytestLines = @(& $script:VenvPython -m pytest 2>&1)
            $pytestExitCode = $LASTEXITCODE
            $pytestOutput = ($pytestLines | ForEach-Object { "$_" }) -join [Environment]::NewLine
        }
        finally {
            Pop-Location
        }
        Write-Host (Protect-Text $pytestOutput)
        $matches = [regex]::Matches($pytestOutput, '(?i)(?<count>\d+)\s+(?<kind>passed|failed|errors?|skipped|xfailed|xpassed)')
        $counts = @{ passed = 0; failed = 0; error = 0; skipped = 0; xfailed = 0; xpassed = 0 }
        $total = 0
        foreach ($match in $matches) {
            $count = [int]$match.Groups["count"].Value
            $kind = $match.Groups["kind"].Value.ToLowerInvariant()
            if ($kind -eq "errors") {
                $kind = "error"
            }
            $counts[$kind] += $count
            $total += $count
        }
        $failedCount = $counts["failed"] + $counts["error"]
        $script:TestCounts = "total=$total, passed=$($counts['passed']), failed=$failedCount"
        if ($total -eq 0) {
            throw ("Pytest reported no collected test results. Exact output: {0}" -f $pytestOutput)
        }
        if ($pytestExitCode -ne 0) {
            throw ("pytest exited with code {0}. Exact output: {1}" -f $pytestExitCode, $pytestOutput)
        }
        return $script:TestCounts
    }
}
catch {
    if ([string]::IsNullOrWhiteSpace($script:FailureMessage)) {
        $script:FailureMessage = Protect-Text $_.Exception.Message
    }
}

foreach ($stepName in $script:StepNames) {
    if ($stepName -eq $script:StepNames[14]) {
        continue
    }
    $existing = $script:Results | Where-Object { $_.Name -eq $stepName } | Select-Object -First 1
    if ($null -eq $existing) {
        if ($SkipDocker -and $stepName -match '^(5|6)') {
            Add-StepResult -Name $stepName -Status "SKIP" -Detail "Docker verification was skipped by -SkipDocker."
        }
        else {
            Add-StepResult -Name $stepName -Status "NOT RUN" -Detail "Setup stopped before this step."
        }
    }
}

if ($null -eq ($script:Results | Where-Object { $_.Name -eq $script:StepNames[14] } | Select-Object -First 1)) {
    Add-StepResult -Name $script:StepNames[14] -Status "PASS" -Detail "Summary report written to private\K_setup_report.txt."
}

$summary = Get-SetupSummary
$privateDirectory = Join-Path $script:RepoRoot "private"
$reportPath = Join-Path $privateDirectory "K_setup_report.txt"
try {
    if (-not (Test-Path -LiteralPath $privateDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $privateDirectory -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($reportPath, $summary, ([System.Text.UTF8Encoding]::new($false)))
}
catch {
    $reportError = Protect-Text $_.Exception.Message
    $script:FailureMessage = "FAIL: Writing setup summary. The setup report could not be saved. Exact error: $reportError"
    $reportResult = $script:Results | Where-Object { $_.Name -eq $script:StepNames[14] } | Select-Object -First 1
    if ($null -ne $reportResult) {
        $script:Results.Remove($reportResult)
    }
    Add-StepResult -Name $script:StepNames[14] -Status "FAIL" -Detail $script:FailureMessage
    $summary = Get-SetupSummary
}

Write-Host ""
Write-Host $summary
Write-Host ""

if (-not [string]::IsNullOrWhiteSpace($script:FailureMessage)) {
    exit 1
}
