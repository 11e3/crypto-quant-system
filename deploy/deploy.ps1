# GCP 배포 스크립트 (PowerShell)
# 사용법: .\deploy.ps1 -ProjectId "your-project-id" -VmName "upbit-bot" -Zone "asia-northeast3-a"

param(
    [string]$ProjectId = "your-project-id",
    [string]$VmName = "upbit-bot",
    [string]$Zone = "asia-northeast3-a"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Upbit Quant Bot 배포 시작..." -ForegroundColor Green
Write-Host "Project: $ProjectId"
Write-Host "VM: $VmName"
Write-Host "Zone: $Zone"

# GCP 프로젝트 설정
Write-Host "`n📋 GCP 프로젝트 설정..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Docker 이미지 빌드
Write-Host "`n🔨 Docker 이미지 빌드..." -ForegroundColor Yellow
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

docker build -f deploy/Dockerfile -t "gcr.io/$ProjectId/upbit-quant-bot:latest" .

# GCR에 푸시
Write-Host "`n📤 GCR에 이미지 푸시..." -ForegroundColor Yellow
gcloud auth configure-docker --quiet
docker push "gcr.io/$ProjectId/upbit-quant-bot:latest"

# VM에 배포
Write-Host "`n🚀 VM에 배포..." -ForegroundColor Yellow
$deployCommand = @"
# 기존 컨테이너 중지 및 제거
docker stop upbit-quant-bot 2>/dev/null || true
docker rm upbit-quant-bot 2>/dev/null || true

# 새 이미지 풀
gcloud auth configure-docker --quiet
docker pull gcr.io/$ProjectId/upbit-quant-bot:latest

# 컨테이너 실행
docker run -d \
    --name upbit-quant-bot \
    --restart unless-stopped \
    -e UPBIT_ACCESS_KEY="`$UPBIT_ACCESS_KEY" \
    -e UPBIT_SECRET_KEY="`$UPBIT_SECRET_KEY" \
    -e TELEGRAM_TOKEN="`$TELEGRAM_TOKEN" \
    -e TELEGRAM_CHAT_ID="`$TELEGRAM_CHAT_ID" \
    -e TELEGRAM_ENABLED="`${TELEGRAM_ENABLED:-true}" \
    -e TRADING_TICKERS="`${TRADING_TICKERS:-KRW-BTC,KRW-ETH,KRW-XRP,KRW-TRX}" \
    -e TRADING_MAX_SLOTS="`${TRADING_MAX_SLOTS:-4}" \
    -e BOT_DAILY_RESET_HOUR="`${BOT_DAILY_RESET_HOUR:-9}" \
    -e BOT_DAILY_RESET_MINUTE="`${BOT_DAILY_RESET_MINUTE:-0}" \
    -v /home/`$(whoami)/upbit-bot/logs:/app/logs \
    gcr.io/$ProjectId/upbit-quant-bot:latest

echo '✅ 배포 완료!'
echo '📊 로그 확인: docker logs -f upbit-quant-bot'
"@

gcloud compute ssh $VmName --zone=$Zone --command=$deployCommand

Write-Host "`n✅ 배포 완료!" -ForegroundColor Green
Write-Host "`n📊 로그 확인:" -ForegroundColor Cyan
Write-Host "  gcloud compute ssh $VmName --zone=$Zone --command='docker logs -f upbit-quant-bot'"
Write-Host "`n🛑 중지:" -ForegroundColor Cyan
Write-Host "  gcloud compute ssh $VmName --zone=$Zone --command='docker stop upbit-quant-bot'"
