# tc-hook-kit Windows setup (replaces install.sh)
# Run this in your own terminal (NOT under the sandbox), because it writes to your user profile.
param(
    [string]$Port = 8765,
    [string]$HostAddr = "127.0.0.1",
    [switch]$NoStartReceive
)

$ErrorActionPreference = "Stop"

# PS 5.1's Set-Content -Encoding utf8 adds a BOM, which Python's json.loads and
# Node's JSON.parse both reject. Write UTF-8 WITHOUT BOM instead.
function Write-Utf8NoBom([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

# --- Paths -------------------------------------------------------------
$Repo   = Split-Path -Parent $MyInvocation.MyCommand.Path          # repo dir (this script's folder)
$Bridge = Join-Path $Repo "bridge.js"
$Bridge = $Bridge -replace '/', '\'

$CfgDir      = Join-Path $HOME ".tc-hook-kit"
$CfgFile     = Join-Path $CfgDir "config.json"
$BridgeCfg   = Join-Path $CfgDir "bridge.json"
$HooksPath   = Join-Path $HOME ".trae-cn\hooks.json"
$RuntimeCfg  = Join-Path $Repo "bridge.runtime.json"

$ServerUrl = "http://${HostAddr}:${Port}"

Write-Host "repo bridge : $Bridge"
Write-Host "server url  : $ServerUrl"

# --- Generate shared secret -------------------------------------------
$Secret = $null
if (Test-Path $CfgFile) {
    try { $Secret = (Get-Content $CfgFile -Raw | ConvertFrom-Json).hook_secret } catch {}
}
if (-not $Secret) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $Secret = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
}

# --- config.json (server reads this) ----------------------------------
New-Item -ItemType Directory -Force -Path $CfgDir | Out-Null
$cfg = @{
    server_url = $ServerUrl
    hook_secret = $Secret
    data_dir = Join-Path $CfgDir "data"
}
Write-Utf8NoBom $CfgFile ($cfg | ConvertTo-Json)

# --- bridge.json (bridge.js reads server_url + hook_secret) -----------
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BridgeCfg) | Out-Null
$bcfg = @{
    server_url = $ServerUrl
    hook_secret = $Secret
    error_log_path = (Join-Path $CfgDir "bridge-errors.log")
}
Write-Utf8NoBom $BridgeCfg ($bcfg | ConvertTo-Json)
# also drop a copy next to bridge.js (bridge.js checks bridge.runtime.json too)
Write-Utf8NoBom $RuntimeCfg ($bcfg | ConvertTo-Json)

# --- Register Trae CN hooks (~/.trae-cn/hooks.json) -------------------
if (Test-Path $HooksPath) { Copy-Item $HooksPath "$HooksPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)" -Force }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $HooksPath) | Out-Null

$NodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $NodeExe) { $NodeExe = "node" }
$cmd = "`"$NodeExe`" `"$Bridge`""
$hookEntry = @{ matcher = ""; hooks = @(@{ type = "command"; command = $cmd; timeout = 10 }) }

$hooks = @{ version = 1; hooks = @{} }
if (Test-Path $HooksPath) {
    try { $hooks = Get-Content $HooksPath -Raw | ConvertFrom-Json } catch {}
}
if (-not $hooks.version) { $hooks.version = 1 }
if (-not $hooks.hooks)    { $hooks.hooks = @{} }

$events = @("SessionStart","UserPromptSubmit","PreToolUse","PostToolUse","Stop","Notification")
foreach ($ev in $events) {
    if (-not $hooks.hooks.$ev) { $hooks.hooks.$ev = @() }
    $entryList = @($hooks.hooks.$ev)
    # avoid duplicates: if any sub-entry already runs this command, skip
    $already = $false
    foreach ($entry in $entryList) {
        foreach ($h in @($entry.hooks)) {
            if ($h.command -eq $cmd) { $already = $true }
        }
    }
    if (-not $already) {
        $hooks.hooks.$ev = $entryList + @($hookEntry)
    }
}
# write JSON without needing an array wrapper
$hooksOut = [ordered]@{ version = 1; hooks = @{} }
$hooksOut.version = 1
foreach ($ev in $events) {
    $hooksOut.hooks[$ev] = @($hooks.hooks.$ev)
}
Write-Utf8NoBom $HooksPath ($hooksOut | ConvertTo-Json -Depth 8)

Write-Host ""
Write-Host "OK. Files written:" -ForegroundColor Green
Write-Host "  config   : $CfgFile"
Write-Host "  bridge   : $BridgeCfg"
Write-Host "  hooks    : $HooksPath (backed up if existed)"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1) Start the receiver (leave this running):"
Write-Host "       python `"$($Bridge.Replace('\','/'))\server.py`" --host $HostAddr --port $Port  -- or  --host 0.0.0.0 for LAN"
Write-Host "  2) In Trae CN -> Settings -> Hooks: confirm the 6 events point to:"
Write-Host "       $cmd"
Write-Host "     and set them to auto-run."
Write-Host "  3) After a task: get the count with"
Write-Host "       curl.exe http://127.0.0.1:$Port/stats"
Write-Host "       curl.exe http://127.0.0.1:$Port/stats?session_id=<fragment>"
