# Starts cloudflared tunnel in background and outputs the public URL
$ErrorActionPreference = "Continue"

$cloudflared = Join-Path $PSScriptRoot "cloudflared.exe"
$log = Join-Path $env:TEMP "rrg_tunnel.log"

Remove-Item $log -ErrorAction SilentlyContinue
Stop-Process -Name "cloudflared" -ErrorAction SilentlyContinue

Write-Host "Starting Cloudflare quick tunnel for http://127.0.0.1:8501..."
$proc = Start-Process -FilePath $cloudflared -ArgumentList "tunnel", "--url", "http://127.0.0.1:8501", "--no-autoupdate" -RedirectStandardError $log -PassThru

$link = $null
for ($i = 0; $i -lt 40 -and -not $link; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $log) {
        $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
        if ($m) {
            $link = $m.Matches[0].Value
        }
    }
}

if ($link) {
    Write-Host "LIVE_SHARE_URL=$link"
    Set-Clipboard -Value $link -ErrorAction SilentlyContinue
} else {
    Write-Host "ERROR: Failed to obtain tunnel URL within 40 seconds."
    if (Test-Path $log) {
        Get-Content $log -Tail 30
    }
}
