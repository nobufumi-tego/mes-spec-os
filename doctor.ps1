# doctor.ps1 - mes-spec-os 環境診断スクリプト
# 使い方: リポジトリのルートで .\doctor.ps1 を実行
# Windows PowerShell 5.1 / PowerShell 7 の両方で動作します

$ErrorActionPreference = 'SilentlyContinue'
$ok = 0
$ng = 0

function Check($label, $condition, $fixHint) {
    if ($condition) {
        Write-Host ("  [OK] " + $label) -ForegroundColor Green
        $script:ok++
    }
    else {
        Write-Host ("  [NG] " + $label) -ForegroundColor Red
        if ($fixHint) { Write-Host ("       → " + $fixHint) -ForegroundColor Yellow }
        $script:ng++
    }
}

Write-Host ""
Write-Host "=== mes-spec-os 環境診断 ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. 実行場所の確認 ---
Write-Host "[1] 実行場所" -ForegroundColor Cyan
Check "リポジトリのルートで実行している（CLAUDE.md が見える）" (Test-Path ".\CLAUDE.md") "cd で mes-spec-os フォルダに移動してから再実行してください"

# --- 2. 必要ツール ---
Write-Host ""
Write-Host "[2] 必要ツール" -ForegroundColor Cyan
Check "Git" (Get-Command git) "winget install Git.Git"
Check "Node.js" (Get-Command node) "winget install OpenJS.NodeJS.LTS"
Check "Claude Code (claude)" (Get-Command claude) "npm install -g @anthropic-ai/claude-code"
Check "uv（Python 環境管理。ENAA Excel/PDF の読み取りに必要）" (Get-Command uv) "winget install astral-sh.uv"

# --- 3. ENAA 資料の配置 ---
Write-Host ""
Write-Host "[3] ENAA 資料（reference/ENAA/）" -ForegroundColor Cyan
$expected = @(
    "mes_g25-029-1.pdf",
    "mes_g25-029-2.xlsx",
    "mes_g25-029-3.pdf",
    "mes_g25-029-4.pdf",
    "mes_g25-029-5.pdf"
)
$missing = @()
foreach ($f in $expected) {
    if (Test-Path (Join-Path "reference\ENAA" $f)) {
        Write-Host ("  [OK] " + $f) -ForegroundColor Green
        $ok++
    }
    else {
        Write-Host ("  [NG] " + $f + " が見つかりません") -ForegroundColor Red
        $missing += $f
        $ng++
    }
}
if ($missing.Count -gt 0) {
    Write-Host "       → 取得手順は reference\ENAA\README.md を参照してください" -ForegroundColor Yellow
    # ブラウザ既定名のままのファイルがないか確認
    $unknown = Get-ChildItem "reference\ENAA" -File |
        Where-Object { ($_.Extension -in ".pdf", ".xlsx") -and ($expected -notcontains $_.Name) }
    if ($unknown) {
        Write-Host ""
        Write-Host "       期待名と違う PDF / Excel が見つかりました：" -ForegroundColor Yellow
        $unknown | ForEach-Object { Write-Host ("         - " + $_.Name) -ForegroundColor Yellow }
        Write-Host "       ダウンロードしたファイル名が「ダウンロード.pdf」等のままかもしれません。" -ForegroundColor Yellow
        Write-Host "       Claude を起動して「ENAA 資料を確認して」と話しかけると、中身から自動識別してリネームを提案します。" -ForegroundColor Yellow
    }
}

# --- 4. セキュリティ設定 ---
Write-Host ""
Write-Host "[4] セキュリティ（ローカル運用前提）" -ForegroundColor Cyan
$remotes = git remote 2>$null
Check "Git リモートが設定されていない（push 事故防止）" (-not $remotes) "git remote remove origin を実行してください（docs\インストール.md 手順 5 参照）"

# --- 結果 ---
Write-Host ""
Write-Host "=== 診断結果: OK $ok 件 / NG $ng 件 ===" -ForegroundColor Cyan
if ($ng -eq 0) {
    Write-Host "問題ありません。claude を起動して「こんにちは。」と話しかけてください。" -ForegroundColor Green
}
else {
    Write-Host "NG の項目を上の → の案内に従って解消してから、もう一度実行してください。" -ForegroundColor Yellow
    Write-Host "解決しない場合は docs\困ったとき.md を参照してください。" -ForegroundColor Yellow
}
Write-Host ""
