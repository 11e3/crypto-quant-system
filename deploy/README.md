# Legacy Docker 배포 가이드 (GCP 전용)

> **⚠️ DEPRECATED**: This directory contains legacy Docker configuration for GCP deployment.
>
> **🆕 NEW: Use root-level Docker setup instead!**
> - See [../README-DOCKER.md](../README-DOCKER.md) for the new production-grade setup
> - Supports Python 3.12.7 with automatic monkeypatch
> - Multi-service architecture (web-ui, trading-bot, data-collector)
> - Works on any platform (GCP, AWS, Azure, local)

---

## Why migrate to new setup?

| Feature | Legacy (this dir) | New (root) |
|---------|-------------------|------------|
| Python Version | 3.11 | 3.12.7 ✅ |
| Monkeypatch | No | Yes ✅ |
| Multi-service | No | Yes ✅ |
| Helper scripts | No | Yes ✅ |
| Documentation | Basic | Comprehensive ✅ |
| Platform support | GCP only | All platforms ✅ |

---

## Quick Migration Guide

### 1. Use new Docker setup from root directory

```bash
# From project root
cd /path/to/crypto-quant-system

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Start services (Windows)
docker-run.bat web       # Web UI only
docker-run.bat bot       # Trading bot

# Or Linux/Mac
./docker-run.sh web      # Web UI only
./docker-run.sh bot      # Trading bot
```

### 2. For GCP deployment with new setup

See [../README-DOCKER.md#production-deployment](../README-DOCKER.md#production-deployment) for:
- AWS EC2 / GCP Compute Engine setup
- Nginx reverse proxy
- SSL certificates (Let's Encrypt)
- Auto-start on boot (systemd)
- Monitoring and alerts

---

## Legacy GCP Deployment (Maintained for reference)

<details>
<summary>Click to expand legacy GCP instructions</summary>

실거래 봇을 GCP 서버에 도커로 배포하는 방법입니다.

### 사전 준비

#### 1. GCP 프로젝트 설정

```bash
# GCP 프로젝트 선택
gcloud config set project YOUR_PROJECT_ID

# Compute Engine API 활성화
gcloud services enable compute.googleapis.com
```

#### 2. VM 인스턴스 생성

```bash
# GCP VM 인스턴스 생성 (예시)
gcloud compute instances create upbit-bot \
    --zone=asia-northeast3-a \
    --machine-type=e2-small \
    --image-family=cos-stable \
    --image-project=cos-cloud \
    --boot-disk-size=20GB \
    --tags=http-server,https-server
```

또는 GCP Console에서:
- Machine type: `e2-small` (1 vCPU, 2GB RAM) 이상 권장
- OS: Container-Optimized OS 또는 Ubuntu
- Boot disk: 20GB 이상

#### 3. Docker 설치 (Ubuntu인 경우)

```bash
# SSH로 VM 접속
gcloud compute ssh upbit-bot --zone=asia-northeast3-a

# Docker 설치
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

### 배포 방법

#### 방법 1: Docker Compose 사용 (권장)

##### 1. 프로젝트 파일 업로드

```bash
# 로컬에서 GCP VM으로 파일 전송
gcloud compute scp --recurse \
    . \
    upbit-bot:~/upbit-quant-system/ \
    --zone=asia-northeast3-a \
    --exclude=".venv/*" --exclude=".git/*"
```

##### 2. 환경 변수 설정

```bash
# VM에 SSH 접속
gcloud compute ssh upbit-bot --zone=asia-northeast3-a

# .env 파일 생성
cd ~/upbit-quant-system
cat > .env << EOF
UPBIT_ACCESS_KEY=your-access-key
UPBIT_SECRET_KEY=your-secret-key
TELEGRAM_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
TELEGRAM_ENABLED=true
EOF

# 보안을 위해 권한 제한
chmod 600 .env
```

##### 3. Docker Compose로 실행

```bash
cd ~/upbit-quant-system

# Start trading bot only
docker-compose up -d trading-bot

# Or start web UI
docker-compose up -d web-ui

# 로그 확인
docker-compose logs -f trading-bot

# 상태 확인
docker-compose ps
```

### 환경 변수 설정

필수 환경 변수:
- `UPBIT_ACCESS_KEY`: Upbit API Access Key
- `UPBIT_SECRET_KEY`: Upbit API Secret Key

선택적 환경 변수:
- `TELEGRAM_TOKEN`: Telegram 봇 토큰
- `TELEGRAM_CHAT_ID`: Telegram 채팅 ID
- `TELEGRAM_ENABLED`: Telegram 알림 활성화 (default: true)
- `TRADING_TICKERS`: 거래할 종목 목록 (default: KRW-BTC,KRW-ETH,KRW-XRP)
- `TRADING_MAX_SLOTS`: 최대 보유 종목 수 (default: 3)
- `BOT_DAILY_RESET_HOUR`: 일일 리셋 시간 (default: 9)

전체 환경 변수 목록은 `../docker-compose.yml` 참조.

### 관리 명령어

```bash
# 로그 확인
docker-compose logs -f trading-bot

# 컨테이너 재시작
docker-compose restart trading-bot

# 컨테이너 중지
docker-compose stop trading-bot

# 컨테이너 삭제
docker-compose down

# 이미지 업데이트 후 재배포
docker-compose build --no-cache trading-bot
docker-compose up -d trading-bot
```

### 보안 권장사항

1. **환경 변수 관리**: `.env` 파일 대신 GCP Secret Manager 사용 권장
2. **방화벽 설정**: 필요한 포트만 열기
3. **IAM 권한**: 최소 권한 원칙 적용
4. **로그 모니터링**: Cloud Logging 연동 고려

### Secret Manager 사용 (고급)

```bash
# Secret 생성
echo -n "your-access-key" | gcloud secrets create upbit-access-key --data-file=-
echo -n "your-secret-key" | gcloud secrets create upbit-secret-key --data-file=-

# VM에 Secret Manager 접근 권한 부여
gcloud compute instances add-iam-policy-binding upbit-bot \
    --zone=asia-northeast3-a \
    --member=serviceAccount:YOUR_SERVICE_ACCOUNT \
    --role=roles/secretmanager.secretAccessor
```

### 모니터링

#### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f trading-bot

# 최근 100줄
docker-compose logs --tail=100 trading-bot
```

#### 헬스 체크

컨테이너는 자동으로 헬스 체크를 수행합니다. 상태 확인:

```bash
docker ps
docker inspect crypto-quant-trading-bot | grep Health
```

### 트러블슈팅

#### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker-compose logs trading-bot

# 환경 변수 확인
docker-compose config
```

#### API 연결 실패

- Upbit API 키가 올바른지 확인
- 네트워크 연결 확인
- 방화벽 설정 확인

#### 메모리 부족

VM의 메모리를 늘리거나 더 큰 인스턴스 타입 사용:

```bash
gcloud compute instances set-machine-type upbit-bot \
    --zone=asia-northeast3-a \
    --machine-type=e2-medium
```

### 자동 재시작 설정

`../docker-compose.yml`에 `restart: unless-stopped`가 설정되어 있어, VM이 재부팅되면 자동으로 컨테이너가 시작됩니다.

### 업데이트 방법

```bash
# 1. 새 코드 pull
cd ~/upbit-quant-system
git pull

# 2. 기존 컨테이너 중지
docker-compose down

# 3. 새 이미지 빌드
docker-compose build --no-cache

# 4. 새 컨테이너 시작
docker-compose up -d

# 5. 로그 확인
docker-compose logs -f trading-bot
```

</details>

---

## Recommended: Migrate to New Setup

The new root-level Docker setup provides:
- ✅ Python 3.12.7 support
- ✅ Automatic monkeypatch for third-party libraries
- ✅ Multi-service architecture (web-ui + trading-bot + data-collector)
- ✅ Helper scripts for easy deployment
- ✅ Comprehensive documentation
- ✅ Better security (non-root user, minimal image)
- ✅ Production-ready features (health checks, log rotation)

**Start here**: [../README-DOCKER.md](../README-DOCKER.md)
