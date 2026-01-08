# Step 4: Real-time Monitoring Automation

## 구현 완료사항

### 1. ✅ Upbit Live Data Integration

**파일**: `scripts/real_time_monitor.py`

실시간 모니터링 시스템:
- Upbit API에서 최신 데이터 자동 수집
- 매일 새로운 캔들 추가 (incremental update)
- 전략 백테스트 실행
- 모니터링 임계치 검증

**핵심 기능**:
```python
monitor = UpbitLiveMonitor(output_dir=Path("reports"))
monitor.monitor(
    tickers=["KRW-BTC", "KRW-ETH"],
    webhook_url="https://hooks.slack.com/..."  # Optional
)
```

**메트릭 계산**:
- Total Return (누적 수익률)
- Sharpe Ratio (위험 조정 수익)
- Max Drawdown (최대 낙폭)
- Win Rate (승률)
- Trade Count & Metrics (거래 통계)
- Commission & Slippage (비용 분석)

### 2. ✅ Enhanced Slack Alerts

**Slack 메시지 포맷** (Block Kit):
```
🚨 Monitoring Alert - 2026-01-08 01:09:57 UTC
⚠️ 1 threshold violation(s) detected

Performance Metrics:
• Return: 24.29%
• Sharpe: 0.29
• MDD: -30.91%
• Win Rate: 30.18%
• Trades: 381 (Won: 115)
• Last Trade: 2026-01-07
• Costs: Commission 12.45 + Slippage 12.45

Violations:
• sharpe_ratio: 0.2893 (threshold: 0.5000)
```

**사용 방법**:
```bash
python -m scripts.real_time_monitor \
  --tickers KRW-BTC KRW-ETH \
  --output reports \
  --slack "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 3. ✅ Windows Task Scheduler Setup

**파일**: `scripts/setup_task_scheduler.py`

자동 스케줄링 설정:

#### 설정 방법 (관리자 권한):
```powershell
# 1. 설정 스크립트 생성
python scripts/setup_task_scheduler.py --action create --schedule-time 09:00

# 2. PowerShell 스크립트 실행 (관리자)
powershell -ExecutionPolicy Bypass -File scripts/setup_task_scheduler.ps1
```

#### Task Scheduler 작업 설정:
- **이름**: CryptoQuantMonitoring
- **트리거**: 매일 09:00
- **작업**: Python script 실행
- **우선순위**: 높음 (RunLevel Highest)
- **배터리**: 항상 실행

#### 추가 명령어:
```powershell
# 작업 제거
python scripts/setup_task_scheduler.py --action remove

# 작업 상태 확인
python scripts/setup_task_scheduler.py --action status
```

---

## 검증 결과

### Real-time 테스트 실행 (2026-01-08):
```
[KRW-BTC] Fetched: 3028 candles
Collected: +1 new candle (incremental update)
Backtest executed successfully

Performance:
✓ Total Return: 24.29%
✓ Sharpe: 0.29 (threshold: 0.5)
✓ MDD: -30.91% (threshold: -25%)
✓ Win Rate: 30.18% (threshold: 30%)
✓ Trades: 381 (Won: 115)
✓ Costs: 12.45 commission + 12.45 slippage

Violations detected: 1 (Sharpe ratio below threshold)
Alert logged: monitoring_alerts.log
Slack notification: Sent
```

---

## 구성 파일

### `config/monitoring.yaml`:
```yaml
thresholds:
  min_win_rate: 0.30
  min_sharpe: 0.5
  max_max_drawdown: -0.25
```

---

## 다음 단계

### Step 5: Documentation Integration
- Sphinx 문서 생성
- API 레퍼런스 작성
- 아키텍처 다이어그램 추가
- 사용자 가이드 작성

---

## 파일 구조

```
scripts/
├── real_time_monitor.py              # 실시간 모니터링 메인
├── setup_task_scheduler.py            # Task Scheduler 설정
├── setup_task_scheduler.ps1           # 생성된 PowerShell 스크립트
└── check_task_scheduler.ps1           # 작업 상태 확인 스크립트

config/
└── monitoring.yaml                    # 모니터링 임계치 설정

reports/
├── monitoring_alerts.log              # 알림 기록
└── metrics_YYYYMMDD_HHMMSS.json      # 메트릭 스냅샷
```

---

## 주요 개선사항

### Phase 4 모니터링 (이전):
- 기록된 trades CSV 분석
- 수동 실행
- 기본 alert 포맷

### Step 4 자동화 (현재):
- ✅ Upbit 실시간 데이터 통합
- ✅ 자동 incremental update
- ✅ 향상된 Slack 알림 (Block Kit)
- ✅ Windows Task Scheduler 자동화
- ✅ 포괄적 메트릭 계산

---

## 사용 예시

### 1. 수동 실행:
```bash
python -m scripts.real_time_monitor \
  --tickers KRW-BTC KRW-ETH KRW-XRP \
  --output reports \
  --slack "https://hooks.slack.com/.../ABC123"
```

### 2. 자동 스케줄:
```powershell
# 관리자 권한 PowerShell에서
python scripts/setup_task_scheduler.py --action create --schedule-time 08:30
powershell -ExecutionPolicy Bypass -File scripts/setup_task_scheduler.ps1
```

### 3. 상태 확인:
```powershell
Get-ScheduledTask -TaskName "CryptoQuantMonitoring" | 
  Select-Object TaskName, State, LastRunTime, LastTaskResult
```

---

## ⚠️ 주의사항

1. **Slack Webhook**: 민감한 정보 - 환경변수로 관리
2. **권한**: Task Scheduler 설정 시 관리자 권한 필요
3. **로그 파일**: 주기적으로 정리 (reports/monitoring_alerts.log)
4. **데이터**: Upbit API 레이트 제한 고려 (초당 10 요청)

---

## 다음 단계: Step 5

**Documentation Integration**:
- Sphinx 문서 빌드
- API 참고 문서 생성
- 사용자 가이드 작성
- 아키텍처 변경사항 문서화
