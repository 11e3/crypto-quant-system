# Docker 배포 가이드

실거래 봇을 GCP 서버에 도커로 배포하는 방법입니다.

## 사전 준비

### 1. GCP 프로젝트 설정

```bash
# GCP 프로젝트 선택
gcloud config set project YOUR_PROJECT_ID

# Compute Engine API 활성화
gcloud services enable compute.googleapis.com
```

### 2. VM 인스턴스 생성

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

### 3. Docker 설치 (Ubuntu인 경우)

```bash
# SSH로 VM 접속
gcloud compute ssh upbit-bot --zone=asia-northeast3-a

# Docker 설치
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

## 배포 방법

### 방법 1: Docker Compose 사용 (권장)

#### 1. 프로젝트 파일 업로드

```bash
# 로컬에서 GCP VM으로 파일 전송
gcloud compute scp --recurse \
    deploy/ \
    upbit-bot:~/upbit-quant-system/deploy/ \
    --zone=asia-northeast3-a

# 소스 코드 전송
gcloud compute scp --recurse \
    src/ \
    pyproject.toml \
    uv.lock \
    upbit-bot:~/upbit-quant-system/ \
    --zone=asia-northeast3-a
```

#### 2. 환경 변수 설정

```bash
# VM에 SSH 접속
gcloud compute ssh upbit-bot --zone=asia-northeast3-a

# .env 파일 생성
cd ~/upbit-quant-system/deploy
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

#### 3. Docker Compose로 실행

```bash
cd ~/upbit-quant-system/deploy
docker-compose up -d

# 로그 확인
docker-compose logs -f trading-bot

# 상태 확인
docker-compose ps
```

### 방법 2: Docker 이미지 직접 빌드 및 실행

#### 1. 이미지 빌드

```bash
# VM에 SSH 접속
gcloud compute ssh upbit-bot --zone=asia-northeast3-a

# 프로젝트 디렉토리로 이동
cd ~/upbit-quant-system

# Docker 이미지 빌드
docker build -f deploy/Dockerfile -t upbit-quant-bot:latest .
```

#### 2. 컨테이너 실행

```bash
docker run -d \
    --name upbit-quant-bot \
    --restart unless-stopped \
    -e UPBIT_ACCESS_KEY="your-access-key" \
    -e UPBIT_SECRET_KEY="your-secret-key" \
    -e TELEGRAM_TOKEN="your-telegram-token" \
    -e TELEGRAM_CHAT_ID="your-chat-id" \
    -v $(pwd)/deploy/logs:/app/logs \
    upbit-quant-bot:latest
```

### 방법 3: GCP Container Registry 사용

#### 1. 로컬에서 이미지 빌드 및 푸시

```bash
# 프로젝트 루트에서
docker build -f deploy/Dockerfile -t gcr.io/YOUR_PROJECT_ID/upbit-quant-bot:latest .

# GCR에 푸시
gcloud auth configure-docker
docker push gcr.io/YOUR_PROJECT_ID/upbit-quant-bot:latest
```

#### 2. GCP VM에서 이미지 실행

```bash
# VM에 SSH 접속
gcloud compute ssh upbit-bot --zone=asia-northeast3-a

# GCR에서 이미지 실행
docker run -d \
    --name upbit-quant-bot \
    --restart unless-stopped \
    -e UPBIT_ACCESS_KEY="your-access-key" \
    -e UPBIT_SECRET_KEY="your-secret-key" \
    -e TELEGRAM_TOKEN="your-telegram-token" \
    -e TELEGRAM_CHAT_ID="your-chat-id" \
    gcr.io/YOUR_PROJECT_ID/upbit-quant-bot:latest
```

## 관리 명령어

```bash
# 로그 확인
docker-compose logs -f trading-bot
# 또는
docker logs -f upbit-quant-bot

# 컨테이너 재시작
docker-compose restart trading-bot
# 또는
docker restart upbit-quant-bot

# 컨테이너 중지
docker-compose stop trading-bot
# 또는
docker stop upbit-quant-bot

# 컨테이너 삭제
docker-compose down
# 또는
docker rm -f upbit-quant-bot

# 이미지 업데이트 후 재배포
docker-compose build --no-cache trading-bot
docker-compose up -d trading-bot
```

## 환경 변수 설정

필수 환경 변수:
- `UPBIT_ACCESS_KEY`: Upbit API Access Key
- `UPBIT_SECRET_KEY`: Upbit API Secret Key

선택적 환경 변수:
- `TELEGRAM_TOKEN`: Telegram 봇 토큰
- `TELEGRAM_CHAT_ID`: Telegram 채팅 ID
- `TELEGRAM_ENABLED`: Telegram 알림 활성화 (default: true)
- `TRADING_TICKERS`: 거래할 종목 목록 (default: KRW-BTC,KRW-ETH,KRW-XRP,KRW-TRX)
- `TRADING_MAX_SLOTS`: 최대 보유 종목 수 (default: 4)
- `BOT_DAILY_RESET_HOUR`: 일일 리셋 시간 (default: 9)
- `BOT_DAILY_RESET_MINUTE`: 일일 리셋 분 (default: 0)

전체 환경 변수 목록은 `docker-compose.yml` 참조.

## 보안 권장사항

1. **환경 변수 관리**: `.env` 파일 대신 GCP Secret Manager 사용 권장
2. **방화벽 설정**: 필요한 포트만 열기
3. **IAM 권한**: 최소 권한 원칙 적용
4. **로그 모니터링**: Cloud Logging 연동 고려

## Secret Manager 사용 (고급)

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

## 모니터링

### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f trading-bot

# 최근 100줄
docker-compose logs --tail=100 trading-bot
```

### 헬스 체크

컨테이너는 자동으로 헬스 체크를 수행합니다. 상태 확인:

```bash
docker ps
docker inspect upbit-quant-bot | grep Health
```

## 트러블슈팅

### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker-compose logs trading-bot

# 환경 변수 확인
docker-compose config
```

### API 연결 실패

- Upbit API 키가 올바른지 확인
- 네트워크 연결 확인
- 방화벽 설정 확인

### 메모리 부족

VM의 메모리를 늘리거나 더 큰 인스턴스 타입 사용:

```bash
gcloud compute instances set-machine-type upbit-bot \
    --zone=asia-northeast3-a \
    --machine-type=e2-medium
```

## 자동 재시작 설정

`docker-compose.yml`에 `restart: unless-stopped`가 설정되어 있어, VM이 재부팅되면 자동으로 컨테이너가 시작됩니다.

## 업데이트 방법

```bash
# 1. 새 코드/이미지 준비
# 2. 기존 컨테이너 중지
docker-compose down

# 3. 새 이미지 빌드/풀
docker-compose build --no-cache
# 또는
docker-compose pull

# 4. 새 컨테이너 시작
docker-compose up -d

# 5. 로그 확인
docker-compose logs -f trading-bot
```
