#!/bin/bash
# GCP 배포 스크립트
# 사용법: ./deploy.sh [gcp-project-id] [vm-instance-name] [zone]

set -e

PROJECT_ID=${1:-"your-project-id"}
VM_NAME=${2:-"upbit-bot"}
ZONE=${3:-"asia-northeast3-a"}

echo "🚀 Upbit Quant Bot 배포 시작..."
echo "Project: $PROJECT_ID"
echo "VM: $VM_NAME"
echo "Zone: $ZONE"

# GCP 프로젝트 설정
echo "📋 GCP 프로젝트 설정..."
gcloud config set project "$PROJECT_ID"

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드..."
cd "$(dirname "$0")/.."
docker build -f deploy/Dockerfile -t gcr.io/$PROJECT_ID/upbit-quant-bot:latest .

# GCR에 푸시
echo "📤 GCR에 이미지 푸시..."
gcloud auth configure-docker --quiet
docker push gcr.io/$PROJECT_ID/upbit-quant-bot:latest

# VM에 배포
echo "🚀 VM에 배포..."
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
    # 기존 컨테이너 중지 및 제거
    docker stop upbit-quant-bot 2>/dev/null || true
    docker rm upbit-quant-bot 2>/dev/null || true
    
    # 새 이미지 풀
    gcloud auth configure-docker --quiet
    docker pull gcr.io/$PROJECT_ID/upbit-quant-bot:latest
    
    # 컨테이너 실행
    docker run -d \
        --name upbit-quant-bot \
        --restart unless-stopped \
        -e UPBIT_ACCESS_KEY=\"\$UPBIT_ACCESS_KEY\" \
        -e UPBIT_SECRET_KEY=\"\$UPBIT_SECRET_KEY\" \
        -e TELEGRAM_TOKEN=\"\$TELEGRAM_TOKEN\" \
        -e TELEGRAM_CHAT_ID=\"\$TELEGRAM_CHAT_ID\" \
        -e TELEGRAM_ENABLED=\"\${TELEGRAM_ENABLED:-true}\" \
        -e TRADING_TICKERS=\"\${TRADING_TICKERS:-KRW-BTC,KRW-ETH,KRW-XRP,KRW-TRX}\" \
        -e TRADING_MAX_SLOTS=\"\${TRADING_MAX_SLOTS:-4}\" \
        -e BOT_DAILY_RESET_HOUR=\"\${BOT_DAILY_RESET_HOUR:-9}\" \
        -e BOT_DAILY_RESET_MINUTE=\"\${BOT_DAILY_RESET_MINUTE:-0}\" \
        -v /home/\$(whoami)/upbit-bot/logs:/app/logs \
        gcr.io/$PROJECT_ID/upbit-quant-bot:latest
    
    echo '✅ 배포 완료!'
    echo '📊 로그 확인: docker logs -f upbit-quant-bot'
"

echo "✅ 배포 완료!"
echo ""
echo "📊 로그 확인:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='docker logs -f upbit-quant-bot'"
echo ""
echo "🛑 중지:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='docker stop upbit-quant-bot'"
