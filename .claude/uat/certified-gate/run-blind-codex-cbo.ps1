# Task-local CBO certified-blind Codex probe launcher.
# Based on D:\e2e-usability\run-blind-codex.ps1. The task-local recovery fixes
# observed audit false alarms and closes independently found provenance bypasses
# while preserving the shared actor isolation and heartbeat behavior.
# Blindness by construction + audit: stripped auth-only CODEX_HOME rebuilt per
# run, fresh exec thread, prompt logged verbatim, post-run agent-originated
# transcript audit -> blindness-certificate.txt. A FAIL certificate means the
# run's findings are DISCARDED.
param(
    [Alias('TargetOrigin')]
    [Parameter(Mandatory = $true)][string]$TargetUrl,
    [string]$PersonaFile = '',
    [string]$Goal = '',
    [string]$State = '',
    [string]$Rubric = '',
    [string]$Arm = '',
    [string]$AuthFile = '',
    [string]$ExistingMatterId = '',
    [string]$RunLabel = 'blind',
    [string]$Model = 'gpt-5.6-sol',
    [string]$Effort = 'max',
    [ValidateSet('read-only', 'workspace-write')][string]$Sandbox = 'workspace-write',
    [string[]]$ExtraDenyTerms = @(),
    [ValidateRange(0, 86400)][int]$HeartbeatSoakSeconds = 0
)
$ErrorActionPreference = 'Stop'
$sharedHarnessRoot = 'D:\e2e-usability'

$script:LaneLockModulePath = 'D:\services\lane-locks\LaneLocks.psm1'
$script:LaneHeartbeatModulePath = Join-Path $sharedHarnessRoot 'BlindLeaseHeartbeat.psm1'
$script:LaneLockScope = 'blind-run'
$script:LaneLockTtlSeconds = 120
$script:LaneHeartbeatSeconds = 30
$script:LaneLockHeld = $false
$script:LaneHeartbeatHandle = $null
$script:LaneHeartbeatStartupProof = $null
$script:ActorStartedAt = $null
$script:ActorEndedAt = $null
$script:HeartbeatSoakPassed = $false
$runDir = $null

function Start-BlindRunHeartbeat {
    $script:LaneHeartbeatHandle = Start-LaneLeaseHeartbeat `
        -LaneLockModulePath $script:LaneLockModulePath `
        -Scope $script:LaneLockScope `
        -TtlSeconds $script:LaneLockTtlSeconds `
        -HeartbeatSeconds $script:LaneHeartbeatSeconds `
        -InitialLease $laneLease
}

function Set-BlindRunStage {
    param([Parameter(Mandatory = $true)][ValidateSet('setup', 'blind-run', 'audit', 'triage', 'verdict')][string]$Stage)

    Set-LaneLeaseHeartbeatStage -Handle $script:LaneHeartbeatHandle -Stage $Stage
    Write-Output "lane stage -> $Stage"
}

function Stop-BlindRunHeartbeat {
    if ($script:LaneHeartbeatHandle) {
        Stop-LaneLeaseHeartbeat -Handle $script:LaneHeartbeatHandle
    }
}

Import-Module $script:LaneLockModulePath -Force -DisableNameChecking
Import-Module $script:LaneHeartbeatModulePath -Force -DisableNameChecking
$blockedBy = $null
$laneLease = Acquire-LaneLock `
    -Scope $script:LaneLockScope `
    -Holder 'factr-certified-blind' `
    -Purpose "certified blind launcher: $RunLabel" `
    -TtlSeconds $script:LaneLockTtlSeconds `
    -RetrySeconds 0 `
    -Stage 'setup' `
    -BlockedBy ([ref]$blockedBy)
if (-not $laneLease) {
    $incumbentReport = if ($blockedBy) { $blockedBy | ConvertTo-Json -Compress } else { 'null' }
    throw "blind-run lane lock is held; BlockedBy=$incumbentReport"
}
$script:LaneLockHeld = $true

try {
Start-BlindRunHeartbeat

function Test-AgentOriginatedRecord {
    param([object]$Record)

    if ($null -eq $Record -or $null -eq $Record.payload) { return $false }
    $outerType = [string]$Record.type
    $payloadType = [string]$Record.payload.type
    if ($payloadType -eq 'user_message') { return $false }
    if ($outerType -eq 'response_item') {
        if ($payloadType -eq 'message') {
            return ([string]$Record.payload.role -eq 'assistant')
        }
        return $true
    }
    if ($outerType -eq 'event_msg') {
        return $payloadType -notin @('task_started', 'token_count', 'user_message')
    }
    return $false
}

function Get-TranscriptTextLeaves {
    param([object]$Value)

    if ($null -eq $Value) { return }
    if ($Value -is [string]) {
        Write-Output $Value
        return
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        foreach ($property in $Value.PSObject.Properties) {
            Get-TranscriptTextLeaves $property.Value
        }
        return
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        foreach ($item in $Value) {
            Get-TranscriptTextLeaves $item
        }
    }
}

function Hide-AllowedAuditPath {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Token
    )

    $forms = @($Path, $Path.Replace('\', '\\')) | Sort-Object Length -Descending -Unique
    foreach ($form in $forms) {
        $pattern = [regex]::Escape($form) + '(?=$|[\\/"''\s,}\]])'
        $Text = [regex]::Replace(
            $Text,
            $pattern,
            $Token,
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
    }
    return $Text
}

function Get-DisallowedBlindToolReason {
    param(
        [object]$Record,
        [Parameter(Mandatory = $true)][string]$ValidatorPath,
        [Parameter(Mandatory = $true)][string]$NodeCommand
    )

    if ([string]$Record.payload.type -ne 'custom_tool_call') { return $null }
    if ([string]$Record.payload.name -ne 'exec') {
        return 'custom tool call is not the audited executor'
    }
    $inputText = [string]$Record.payload.input
    if (-not $inputText) { return 'custom executor call has no inspectable input' }
    $validatorOutput = @($inputText | & $NodeCommand $ValidatorPath 2>&1)
    if ($LASTEXITCODE -ne 0) {
        return 'AST validator failed closed before producing a verdict'
    }
    try {
        $verdict = (($validatorOutput | ForEach-Object { [string]$_ }) -join "`n") | ConvertFrom-Json
    } catch {
        return 'AST validator produced no parseable verdict'
    }
    if ([bool]$verdict.allowed) { return $null }
    $reason = [string]$verdict.reason
    if (-not $reason) { $reason = 'source is outside the restricted executor grammar' }
    return "AST allowlist rejected executor: $reason"
}

function Invoke-CertifiedStructuredJudge {
    param(
        [Parameter(Mandatory = $true)][string]$Codex,
        [Parameter(Mandatory = $true)][string]$BlindHome,
        [Parameter(Mandatory = $true)][string]$Scratch,
        [Parameter(Mandatory = $true)][string]$PromptPath,
        [Parameter(Mandatory = $true)][string]$SchemaPath,
        [Parameter(Mandatory = $true)][string]$ResultPath,
        [Parameter(Mandatory = $true)][string]$LogPath,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][string]$Effort,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $priorHome = [Environment]::GetEnvironmentVariable('CODEX_HOME', 'Process')
    $judgeExit = -1
    $env:CODEX_HOME = $BlindHome
    $judgeArgs = @(
        'exec', '--ephemeral', '--cd', $Scratch, '--skip-git-repo-check',
        '--ignore-rules', '--strict-config',
        '--disable', 'apps', '--disable', 'memories', '--disable', 'plugins',
        '-m', $Model,
        '-c', "model_reasoning_effort=`"$Effort`"",
        '-c', 'approval_policy="never"',
        '-c', 'default_permissions=:read-only',
        '--output-schema', $SchemaPath,
        '--output-last-message', $ResultPath,
        '-'
    )
    $ErrorActionPreference = 'Continue'
    try {
        Get-Content -LiteralPath $PromptPath -Raw | & $Codex @judgeArgs *> $LogPath
        $judgeExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = 'Stop'
        if ($null -eq $priorHome) {
            Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue
        } else {
            $env:CODEX_HOME = $priorHome
        }
        Get-ChildItem -LiteralPath $BlindHome -Force | Where-Object Name -ne 'auth.json' |
            Remove-Item -Recurse -Force -Confirm:$false
    }
    if ($judgeExit -ne 0 -or -not (Test-Path -LiteralPath $ResultPath)) {
        throw "$Label failed with exit $judgeExit."
    }
}

if ($RunLabel -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') {
    throw 'RunLabel contains unsupported characters.'
}
if (-not $State) { $State = [string]$env:E2E_STATE }
if (-not $ExistingMatterId) { $ExistingMatterId = [string]$env:E2E_EXISTING_MATTER }
if (-not $Rubric) { $Rubric = [string]$env:E2E_RUBRIC }
if (-not $Arm) {
    if ($env:E2E_ARM) {
        $Arm = [string]$env:E2E_ARM
    } elseif ([string]$env:E2E_MOBILE -match '^(1|true|yes|on)$') {
        $Arm = 'mobile'
    } else {
        $Arm = 'desktop'
    }
}
$Arm = $Arm.Trim().ToLowerInvariant()
if ($Arm -notin @('desktop', 'mobile')) { throw "Unknown arm '$Arm'; use desktop or mobile." }
$isT2 = [bool]$State
if ($ExistingMatterId -and -not $isT2) {
    throw 'ExistingMatterId requires State so the verify-only state contract is explicit.'
}
if ($isT2) {
    if (-not $Rubric) { throw 'Rubric is required when State is selected.' }
    $Rubric = $Rubric.Trim().ToLowerInvariant()
    if ($Rubric -notin @('parity', 'task', 'ux')) {
        throw "Unknown rubric '$Rubric'; use parity, task, or ux."
    }
    if (-not $AuthFile) { $AuthFile = [string]$env:E2E_AUTH }
    if (-not $AuthFile) { $AuthFile = Join-Path $sharedHarnessRoot 'auth-state.json' }
    $AuthFile = (Resolve-Path -LiteralPath $AuthFile).Path
} else {
    if (-not $PersonaFile -or -not $Goal) {
        throw 'PersonaFile and Goal are required when State is not selected.'
    }
    $PersonaFile = (Resolve-Path -LiteralPath $PersonaFile).Path
    if ($Rubric) { throw 'Rubric requires a State so the shared T2 prompt contract can be rendered.' }
}

$blindHome = 'D:\services\blind-codex-home'
$toolCallAstValidator = Join-Path $PSScriptRoot 'audit-js\validate-tool-call.mjs'
if (-not (Test-Path -LiteralPath $toolCallAstValidator)) {
    throw "Certified tool-call AST validator is missing: $toolCallAstValidator"
}
$transcriptAuditor = Join-Path $PSScriptRoot 'audit-js\audit-transcript.mjs'
if (-not (Test-Path -LiteralPath $transcriptAuditor)) {
    throw "Certified transcript auditor is missing: $transcriptAuditor"
}
$acornPackagePath = Join-Path $sharedHarnessRoot 'audit-js\node_modules\acorn\package.json'
if (-not (Test-Path -LiteralPath $acornPackagePath)) {
    throw "Pinned Acorn audit dependency is missing from $sharedHarnessRoot\audit-js."
}
$acornVersion = [string]((Get-Content -Raw -LiteralPath $acornPackagePath | ConvertFrom-Json).version)
if ($acornVersion -ne '8.17.0') {
    throw "Pinned Acorn audit dependency must be 8.17.0; found $acornVersion."
}
$toolCallAstValidatorHash = (Get-FileHash -LiteralPath $toolCallAstValidator -Algorithm SHA256).Hash
$transcriptAuditorHash = (Get-FileHash -LiteralPath $transcriptAuditor -Algorithm SHA256).Hash
$launcherHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
$sharedBaseLauncherHash = (Get-FileHash -LiteralPath (Join-Path $sharedHarnessRoot 'run-blind-codex.ps1') -Algorithm SHA256).Hash
$sharedCertifiedProbeHash = (Get-FileHash -LiteralPath (Join-Path $sharedHarnessRoot 'certified_probe.py') -Algorithm SHA256).Hash
$sharedHeartbeatHash = (Get-FileHash -LiteralPath $script:LaneHeartbeatModulePath -Algorithm SHA256).Hash
$sharedLaneLockHash = (Get-FileHash -LiteralPath $script:LaneLockModulePath -Algorithm SHA256).Hash
$nodeCommand = (Get-Command node -CommandType Application -ErrorAction Stop).Source
$browserStatePath = $null
$blindRunMutex = [System.Threading.Mutex]::new($false, 'Global\CodexCertifiedBlindHome')
$mutexAcquired = $false
try {
    $mutexAcquired = $blindRunMutex.WaitOne(0)
} catch [System.Threading.AbandonedMutexException] {
    $mutexAcquired = $true
}
if (-not $mutexAcquired) {
    $blindRunMutex.Dispose()
    throw 'Another certified blind run owns the shared auth-only home; retry after it finishes.'
}

try {
# --- run layout -------------------------------------------------------------
$stamp = Get-Date -Format 'yyyyMMdd-HHmmssfff'
$nonce = [Guid]::NewGuid().ToString('N').Substring(0, 8)
$runId = "$stamp-$nonce-$RunLabel"
$runDir = "D:\e2e-usability\blind-runs\$runId"
$scratch = Join-Path $runDir 'scratch'
New-Item -ItemType Directory -Force -Path $scratch | Out-Null

# --- prompt and state: consume the shared T2 contracts ----------------------
$browserToolRoot = $null
$playwrightMcpEntry = $null
$browserViewport = $null
$browserUserAgent = $null
if ($isT2) {
    $adapter = Join-Path $sharedHarnessRoot 'certified_probe.py'
    $prepareArgs = @(
        $adapter, 'prepare',
        '--run-dir', $runDir,
        '--scratch', $scratch,
        '--run-id', $runId,
        '--target-origin', $TargetUrl,
        '--state', $State,
        '--rubric', $Rubric,
        '--arm', $Arm,
        '--auth', $AuthFile
    )
    if ($ExistingMatterId) {
        $prepareArgs += @('--existing-matter', $ExistingMatterId)
    }
    & python @prepareArgs 2>&1 | Tee-Object -FilePath (Join-Path $runDir 'prepare.log')
    if ($LASTEXITCODE -ne 0) { throw "Certified T2 preparation failed with exit $LASTEXITCODE." }
    $prepareResult = Get-Content (Join-Path $runDir 'prepare-result.json') -Raw | ConvertFrom-Json
    $browserToolRoot = [string]$prepareResult.playwright_tool_root
    $playwrightMcpEntry = [string]$prepareResult.playwright_mcp_entry
    $browserViewport = $prepareResult.viewport
    $browserUserAgent = [string]$prepareResult.user_agent
    if (-not (Test-Path -LiteralPath $browserToolRoot)) {
        throw "Pinned Playwright tool root not found: $browserToolRoot"
    }
    if (-not (Test-Path -LiteralPath $playwrightMcpEntry)) {
        throw "Pinned Playwright MCP entry not found: $playwrightMcpEntry"
    }
    $prompt = Get-Content (Join-Path $runDir 'actor-prompt.txt') -Raw
    $browserStatePath = Join-Path $scratch 'browser-state.json'
} else {
    $persona = Get-Content -LiteralPath $PersonaFile -Raw
    $prompt = @"
$persona

Your goal: $Goal
Target: $TargetUrl
"@
    if ($Sandbox -eq 'workspace-write') {
        $browserToolResultPath = Join-Path $runDir 'browser-tool.json'
        & python (Join-Path $sharedHarnessRoot 'certified_probe.py') browser-tool `
            --scratch $scratch --arm $Arm --output $browserToolResultPath
        if ($LASTEXITCODE -ne 0) { throw "Pinned browser-tool preparation failed with exit $LASTEXITCODE." }
        $browserToolResult = Get-Content $browserToolResultPath -Raw | ConvertFrom-Json
        $browserToolRoot = [string]$browserToolResult.playwright_tool_root
        $playwrightMcpEntry = [string]$browserToolResult.playwright_mcp_entry
        $browserViewport = $browserToolResult.viewport
        $browserUserAgent = [string]$browserToolResult.user_agent
    }
}
Set-Content (Join-Path $runDir 'prompt.txt') $prompt -Encoding utf8

# --- stripped home: auth.json ONLY, rebuilt fresh every run -----------------
$sourceAuth = Join-Path $env:USERPROFILE '.codex\auth.json'
if (-not (Test-Path -LiteralPath $sourceAuth)) { throw "Codex auth source not found: $sourceAuth" }
if (Test-Path -LiteralPath $blindHome) {
    Remove-Item -LiteralPath $blindHome -Recurse -Force -Confirm:$false
}
New-Item -ItemType Directory -Force -Path $blindHome | Out-Null
Copy-Item -LiteralPath $sourceAuth -Destination (Join-Path $blindHome 'auth.json')
$homeManifest = (Get-ChildItem -LiteralPath $blindHome -Recurse -File | ForEach-Object Name) -join ', '
if ($homeManifest -ne 'auth.json') { throw "stripped home not clean: $homeManifest" }

# --- fresh exec thread with a browser-only MCP and bounded shell profile -----
$codex = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" |
    Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object FullName
if (-not $codex) { throw 'Codex executable not found.' }
$priorCodexHome = [Environment]::GetEnvironmentVariable('CODEX_HOME', 'Process')
$priorPlaywrightBrowsers = [Environment]::GetEnvironmentVariable('PLAYWRIGHT_BROWSERS_PATH', 'Process')
$targetUri = [Uri]$TargetUrl
$targetHost = $targetUri.DnsSafeHost
$targetOrigin = $targetUri.GetLeftPart([UriPartial]::Authority)
$permissionProfile = if ($Sandbox -eq 'workspace-write') { 'blind-browser' } else { ':read-only' }
$codexArgs = @(
    'exec', '--cd', $scratch, '--skip-git-repo-check',
    '--ignore-rules', '--strict-config',
    '--disable', 'apps', '--disable', 'memories', '--disable', 'plugins',
    '-m', $Model,
    '-c', "model_reasoning_effort=`"$Effort`"",
    '-c', 'approval_policy="never"',
    '-c', 'features.code_mode.enabled=false',
    '-c', "features.code_mode.excluded_tool_namespaces=[ 'functions', 'web', 'shell', 'shell_command', 'filesystem', 'container', 'apply_patch', 'view_image' ]",
    '-c', 'web_search="disabled"',
    '-c', 'tools.web_search=false',
    '-c', 'shell_environment_policy.inherit="core"',
    '-c', 'shell_environment_policy.set.PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers'
)
if ($Sandbox -eq 'workspace-write') {
    # Codex 0.144 uses managed permission profiles on this host. Shell writes
    # stay inside scratch and shell networking stays off. The separate browser
    # MCP receives scratch-local auth/output paths plus an advisory request
    # allowlist for the target origin; Playwright documents that redirects are
    # outside that filter and that it is not a security boundary.
    $codexArgs += @(
        '-c', 'default_permissions=blind-browser'
    )
} else {
    $codexArgs += @('-c', 'default_permissions=:read-only')
}
if ($playwrightMcpEntry) {
    $browserArtifacts = Join-Path $scratch 'browser-artifacts'
    New-Item -ItemType Directory -Force -Path $browserArtifacts | Out-Null
    $viewportText = "$([int]$browserViewport.width)x$([int]$browserViewport.height)"
    $mcpArgs = @(
        $playwrightMcpEntry,
        '--headless',
        '--isolated',
        '--viewport-size', $viewportText,
        '--output-dir', $browserArtifacts,
        '--allowed-origins', $targetOrigin
    )
    if ($Arm -eq 'mobile') {
        $mcpArgs += '--mobile'
        if ($browserUserAgent) { $mcpArgs += @('--user-agent', $browserUserAgent) }
    }
    if ($browserStatePath) { $mcpArgs += @('--storage-state', $browserStatePath) }
    foreach ($mcpArg in $mcpArgs) {
        if ([string]$mcpArg -match "'") { throw "Playwright MCP argument contains an unsupported quote." }
    }
    $mcpArgsToml = '[ ' + (($mcpArgs | ForEach-Object { "'$_'" }) -join ', ') + ' ]'
    $filesystemToml = "{ ':minimal' = 'read', ':workspace_roots' = { '.' = 'write' }, '$browserToolRoot' = 'read', 'D:\playwright-browsers' = 'read' }"
    $codexArgs += @(
        '-c', "permissions.blind-browser.filesystem=$filesystemToml",
        '-c', 'mcp_servers.playwright.command=node',
        '-c', "mcp_servers.playwright.args=$mcpArgsToml",
        '-c', "mcp_servers.playwright.cwd='$scratch'",
        '-c', 'mcp_servers.playwright.required=true',
        '-c', 'mcp_servers.playwright.default_tools_approval_mode=approve',
        '-c', "mcp_servers.playwright.disabled_tools=[ 'browser_drop', 'browser_install', 'browser_file_upload', 'browser_run_code_unsafe' ]",
        '-c', 'mcp_servers.playwright.startup_timeout_sec=60',
        '-c', 'mcp_servers.playwright.tool_timeout_sec=120',
        '-c', 'mcp_servers.playwright.env.PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers'
    )
}
$codexArgs += @(
    '--output-last-message', (Join-Path $runDir 'debrief.txt'),
    '-'
)
$networkSummary = if ($playwrightMcpEntry) {
    "Playwright MCP request filter $targetOrigin (advisory; redirects unbounded); shell disabled"
} else { 'disabled' }
$script:LaneHeartbeatStartupProof = Wait-LaneLeaseHeartbeatStartup `
    -Handle $script:LaneHeartbeatHandle `
    -MinimumTicks 2 `
    -TimeoutSeconds 105
Write-Output (
    'lane heartbeat startup self-check: PASS ' +
    "($($script:LaneHeartbeatStartupProof.renewalTicks) renewals, " +
    "$($script:LaneHeartbeatStartupProof.firstHeartbeatAt) -> " +
    "$($script:LaneHeartbeatStartupProof.lastHeartbeatAt))"
)
Set-BlindRunStage -Stage 'blind-run'
if ($HeartbeatSoakSeconds -gt 0) {
    Write-Output "launching heartbeat soak run=$runId sleep-actor=${HeartbeatSoakSeconds}s"
} else {
    Write-Output "launching certified Codex run=$runId permissions=$permissionProfile network=$networkSummary arm=$Arm"
}
# Prompt goes via stdin ('-'): PS 5.1 argv quoting mangles multiline text.
# EAP drops to Continue around the native call because native stderr warnings
# become ErrorRecords; the native exit code is the actual gate.
$ErrorActionPreference = 'Continue'
try {
    $env:CODEX_HOME = $blindHome
    $env:PLAYWRIGHT_BROWSERS_PATH = 'D:\playwright-browsers'
    if ($browserStatePath) {
        Copy-Item -LiteralPath $AuthFile -Destination $browserStatePath
    }
    $script:ActorStartedAt = [datetime]::UtcNow.ToString('o')
    if ($HeartbeatSoakSeconds -gt 0) {
        & powershell.exe -NoProfile -NonInteractive -Command "Start-Sleep -Seconds $HeartbeatSoakSeconds" `
            *> (Join-Path $runDir 'run.log')
    } else {
        Get-Content (Join-Path $runDir 'prompt.txt') -Raw |
            & $codex @codexArgs *> (Join-Path $runDir 'run.log')
    }
    $execExit = $LASTEXITCODE
    $script:ActorEndedAt = [datetime]::UtcNow.ToString('o')
} finally {
    $ErrorActionPreference = 'Stop'
    if ($browserStatePath -and (Test-Path -LiteralPath $browserStatePath)) {
        Remove-Item -LiteralPath $browserStatePath -Force -Confirm:$false
    }
    if ($null -eq $priorCodexHome) {
        Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue
    } else {
        $env:CODEX_HOME = $priorCodexHome
    }
    if ($null -eq $priorPlaywrightBrowsers) {
        Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue
    } else {
        $env:PLAYWRIGHT_BROWSERS_PATH = $priorPlaywrightBrowsers
    }
}
if ($null -eq $execExit) { $execExit = 1 }

if ($HeartbeatSoakSeconds -gt 0) {
    if ($execExit -ne 0) { throw "Heartbeat soak actor failed with exit $execExit." }
    Assert-LaneHeartbeatWorkerHealthy -Handle $script:LaneHeartbeatHandle
    $soakLease = Test-LaneLock -Scope $script:LaneLockScope
    if (-not $soakLease.held -or [int]$soakLease.lease.pid -ne $PID) {
        throw 'Heartbeat soak ended without the live launcher-owned blind-run lease.'
    }
    $minimumActorRenewals = [Math]::Max(
        1,
        [int][Math]::Floor($HeartbeatSoakSeconds / $script:LaneHeartbeatSeconds) - 1
    )
    $actualActorRenewals = [int]$script:LaneHeartbeatHandle.State.ticks -
        [int]$script:LaneHeartbeatStartupProof.renewalTicks
    if ($actualActorRenewals -lt $minimumActorRenewals) {
        throw "Heartbeat soak recorded $actualActorRenewals actor-window renewal(s); expected at least $minimumActorRenewals."
    }
    Set-BlindRunStage -Stage 'verdict'
    $script:HeartbeatSoakPassed = $true
    Write-Output "heartbeat soak: PASS ($actualActorRenewals renewal(s) during the blocking actor)"
    return
}

Set-BlindRunStage -Stage 'audit'
# --- blindness audit over agent-originated transcript records only ---------
$transcripts = Get-ChildItem (Join-Path $blindHome 'sessions') -Recurse -Filter '*.jsonl' -ErrorAction SilentlyContinue
$transcriptCopies = @()
$evidence = @()
$auditorStats = $null
if (-not $transcripts) {
    $evidence += 'NO TRANSCRIPT FOUND - cannot certify'
} else {
    $transcripts | ForEach-Object {
        $copyPath = Join-Path $runDir ('transcript-' + $_.Name)
        Copy-Item -LiteralPath $_.FullName -Destination $copyPath
        $transcriptCopies += Get-Item -LiteralPath $copyPath
    }
    # The task-local auditor validates every agent executor with the restricted
    # AST grammar, then correlates each allowed Playwright call with its MCP
    # result and executor output. Only those correlated browser-output records
    # are treated as target-origin content. Agent reasoning, messages, tool
    # arguments, discovery output, and all unbound records retain the complete
    # host-path and internal-vocabulary deny scan.
    $auditArgs = @('--scratch', $scratch, '--target-url', $TargetUrl)
    if ($browserToolRoot) { $auditArgs += @('--browser-root', $browserToolRoot) }
    foreach ($term in $ExtraDenyTerms) { $auditArgs += @('--extra-deny', $term) }
    foreach ($transcript in $transcriptCopies) { $auditArgs += @('--transcript', $transcript.FullName) }
    $auditOutput = @(& $nodeCommand $transcriptAuditor @auditArgs 2>&1)
    if ($LASTEXITCODE -ne 0) {
        $evidence += 'TASK-LOCAL TRANSCRIPT AUDITOR FAILED CLOSED'
        $evidence += ($auditOutput | ForEach-Object { [string]$_ })
    } else {
        try {
            $auditVerdict = (($auditOutput | ForEach-Object { [string]$_ }) -join "`n") | ConvertFrom-Json
            $auditorStats = $auditVerdict.stats
            if (-not [bool]$auditVerdict.ok) {
                $evidence += @($auditVerdict.evidence | ForEach-Object { [string]$_ })
            }
        } catch {
            $evidence += 'TASK-LOCAL TRANSCRIPT AUDITOR PRODUCED NO PARSEABLE VERDICT'
        }
    }
}

$transcriptManifestHash = 'MISSING'
if ($transcriptCopies.Count -gt 0) {
    $transcriptManifest = ($transcriptCopies | Sort-Object Name | ForEach-Object {
        "$($_.Name):$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
    }) -join "`n"
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $manifestBytes = [System.Text.Encoding]::UTF8.GetBytes($transcriptManifest)
        $transcriptManifestHash = [BitConverter]::ToString($sha256.ComputeHash($manifestBytes)).Replace('-', '')
    } finally {
        $sha256.Dispose()
    }
}

# Leave the shared home in its minimal auth-only shape after transcript copy.
Get-ChildItem -LiteralPath $blindHome -Force | Where-Object Name -ne 'auth.json' |
    Remove-Item -Recurse -Force -Confirm:$false
$postRunHomeManifest = (Get-ChildItem -LiteralPath $blindHome -Recurse -File | ForEach-Object Name) -join ', '
if ($postRunHomeManifest -ne 'auth.json') {
    $evidence += "HOME CLEANUP FAILED: $postRunHomeManifest"
}
$verdict = if ($evidence.Count -eq 0 -and $execExit -eq 0) { 'PASS' } else { 'FAIL' }

# --- certificate ------------------------------------------------------------
$cert = @(
    "BLINDNESS CERTIFICATE: $verdict",
    "run: $runId | exec exit: $execExit",
    "model: $Model @ $Effort | permissions: $permissionProfile | network: $networkSummary",
    'read scoping is not enforced on this host - detection tier; ACL tier pending elevated bundle',
    "home manifest at launch: $homeManifest (fresh thread, no AGENTS.md, no sessions)",
    "home manifest after audit: $postRunHomeManifest",
    "prompt: prompt.txt (sha256 $((Get-FileHash (Join-Path $runDir 'prompt.txt')).Hash))",
    "transcripts: $($transcriptCopies.Count) | manifest sha256 $transcriptManifestHash",
    'audit scope: agent-originated records only; user/developer prompt echoes skipped',
    "launcher provenance: task-local sha256 $launcherHash | shared base sha256 $sharedBaseLauncherHash",
    "shared dependencies: certified_probe.py $sharedCertifiedProbeHash | heartbeat $sharedHeartbeatHash | lane lock $sharedLaneLockHash",
    "executor audit: Acorn $acornVersion restricted AST | validator sha256 $toolCallAstValidatorHash | transcript auditor sha256 $transcriptAuditorHash",
    "audit provenance: $($auditorStats.validatedPlaywrightCalls) correlated Playwright calls | $($auditorStats.exemptBrowserOutputRecords) target-origin browser-output records",
    'audit path allowances: run scratch, exact pinned Playwright MCP root, pinned browser runtime, and correlated public target output only',
    "evidence ($($evidence.Count)):"
) + $evidence
Set-Content (Join-Path $runDir 'blindness-certificate.txt') ($cert -join "`n") -Encoding utf8
Write-Output "certificate: $verdict -> $runDir\blindness-certificate.txt"
if ($verdict -ne 'PASS') { throw 'Blindness certificate FAIL; findings discarded.' }

Set-BlindRunStage -Stage 'triage'
# --- independent rubric judge, semantic de-duplication, and publication -----
if ($isT2) {
    $actorDebriefPath = Join-Path $runDir 'actor-debrief.txt'
    Copy-Item -LiteralPath (Join-Path $runDir 'debrief.txt') -Destination $actorDebriefPath
    $rubricPromptPath = Join-Path $runDir 'rubric-judge-prompt.txt'
    $rubricSchemaPath = Join-Path $runDir 'rubric-judge-schema.json'
    $rubricResultPath = Join-Path $runDir 'rubric-judgment.json'
    & python (Join-Path $sharedHarnessRoot 'certified_probe.py') rubric-prompt `
        --run-dir $runDir --prompt-output $rubricPromptPath --schema-output $rubricSchemaPath
    if ($LASTEXITCODE -ne 0) { throw "Rubric-judge framing failed with exit $LASTEXITCODE." }
    Invoke-CertifiedStructuredJudge `
        -Codex $codex -BlindHome $blindHome -Scratch $scratch `
        -PromptPath $rubricPromptPath -SchemaPath $rubricSchemaPath `
        -ResultPath $rubricResultPath -LogPath (Join-Path $runDir 'rubric-judge.log') `
        -Model $Model -Effort $Effort -Label 'Independent rubric judgment'
    & python (Join-Path $sharedHarnessRoot 'certified_probe.py') apply-judgment `
        --run-dir $runDir --judgment $rubricResultPath
    if ($LASTEXITCODE -ne 0) { throw "Rubric judgment application failed with exit $LASTEXITCODE." }

    $dedupePromptPath = Join-Path $runDir 'semantic-dedupe-prompt.txt'
    $dedupeSchemaPath = Join-Path $runDir 'semantic-dedupe-schema.json'
    $dedupeResultPath = Join-Path $runDir 'semantic-dedupe.json'
    & python (Join-Path $sharedHarnessRoot 'certified_probe.py') dedupe-prompt `
        --run-dir $runDir --prompt-output $dedupePromptPath --schema-output $dedupeSchemaPath
    if ($LASTEXITCODE -ne 0) { throw "Semantic de-duplication framing failed with exit $LASTEXITCODE." }

    Invoke-CertifiedStructuredJudge `
        -Codex $codex -BlindHome $blindHome -Scratch $scratch `
        -PromptPath $dedupePromptPath -SchemaPath $dedupeSchemaPath `
        -ResultPath $dedupeResultPath -LogPath (Join-Path $runDir 'semantic-dedupe.log') `
        -Model $Model -Effort $Effort -Label 'Semantic de-duplication'

    & python (Join-Path $sharedHarnessRoot 'certified_probe.py') finalize `
        --run-dir $runDir --semantic-dedupe $dedupeResultPath
    if ($LASTEXITCODE -ne 0) { throw "Certified T2 finalize/triage failed with exit $LASTEXITCODE." }
    Write-Output "t2 result -> $runDir\t2-result.json"
}
Set-BlindRunStage -Stage 'verdict'
} finally {
    if ($browserStatePath -and (Test-Path -LiteralPath $browserStatePath)) {
        Remove-Item -LiteralPath $browserStatePath -Force -Confirm:$false
    }
    if (Test-Path -LiteralPath $blindHome) {
        Get-ChildItem -LiteralPath $blindHome -Force | Where-Object Name -ne 'auth.json' |
            Remove-Item -Recurse -Force -Confirm:$false
    }
    if ($mutexAcquired) {
        $blindRunMutex.ReleaseMutex()
    }
    $blindRunMutex.Dispose()
}
} finally {
    $heartbeatCleanupError = $null
    try {
        Stop-BlindRunHeartbeat
        if ($script:LaneHeartbeatHandle -and $runDir -and (Test-Path -LiteralPath $runDir)) {
            $heartbeatMode = if ($HeartbeatSoakSeconds -gt 0) { 'soak' } else { 'certified' }
            $heartbeatMetadata = @{
                runId                 = $runId
                mode                  = $heartbeatMode
                actorStartedAt        = $script:ActorStartedAt
                actorEndedAt          = $script:ActorEndedAt
                requestedSoakSeconds  = $HeartbeatSoakSeconds
                startupSelfCheck      = $script:LaneHeartbeatStartupProof
            }
            $heartbeatSummary = Save-LaneLeaseHeartbeatEvidence `
                -Handle $script:LaneHeartbeatHandle `
                -RunDir $runDir `
                -Metadata $heartbeatMetadata

            if ($HeartbeatSoakSeconds -gt 0) {
                $durationPass = $heartbeatSummary.actorWindow -and
                    [double]$heartbeatSummary.actorWindow.durationSeconds -ge ($HeartbeatSoakSeconds - 1)
                $continuityPass = $heartbeatSummary.actorWindow -and
                    [bool]$heartbeatSummary.actorWindow.continuityPass
                $soakPass = $script:HeartbeatSoakPassed -and $durationPass -and $continuityPass -and
                    -not $heartbeatSummary.failure
                $soakResult = [ordered]@{
                    status                 = if ($soakPass) { 'PASS' } else { 'FAIL' }
                    requestedBlockSeconds  = $HeartbeatSoakSeconds
                    actorWindow            = $heartbeatSummary.actorWindow
                    totalRenewalCount      = $heartbeatSummary.renewalCount
                    firstHeartbeatAt       = $heartbeatSummary.firstHeartbeatAt
                    lastHeartbeatAt        = $heartbeatSummary.lastHeartbeatAt
                    startupSelfCheck       = $script:LaneHeartbeatStartupProof
                    failure                = $heartbeatSummary.failure
                    heartbeatJournal       = 'lane-heartbeats.jsonl'
                    heartbeatSummary       = 'lane-heartbeat-summary.json'
                    certificateIssued      = $false
                    note                   = 'Diagnostic soak only; this run is not a blindness certification.'
                }
                $soakJson = $soakResult | ConvertTo-Json -Depth 10
                [System.IO.File]::WriteAllText(
                    (Join-Path $runDir 'heartbeat-soak-result.json'),
                    $soakJson + [Environment]::NewLine,
                    [System.Text.UTF8Encoding]::new($false)
                )
                if (-not $soakPass) {
                    $heartbeatCleanupError = 'Heartbeat soak continuity summary failed.'
                }
            } elseif ($heartbeatSummary.failure) {
                $heartbeatCleanupError = "Heartbeat worker reported a terminal failure: $($heartbeatSummary.failure)"
            }
        }
    } catch {
        $heartbeatCleanupError = $_.Exception.Message
    } finally {
        if ($script:LaneHeartbeatHandle) {
            Remove-LaneLeaseHeartbeatTemp -Handle $script:LaneHeartbeatHandle
        }
        if ($script:LaneLockHeld) {
            $released = Release-LaneLock -Scope $script:LaneLockScope
            $script:LaneLockHeld = $false
            if (-not $released) {
                Write-Warning 'PID guard refused to release blind-run; the lease is no longer owned by this launcher.'
            }
        }
    }
    if ($heartbeatCleanupError) {
        throw $heartbeatCleanupError
    }
}
