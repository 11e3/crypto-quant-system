# Phase 4 Monitoring

Phase 4 모니터링은 전략/엔진의 런타임 건전성을 상시 점검하기 위한 경량 파이프라인입니다.

## 지표 계산 대상
- 거래 기반 지표: 총 수익률, CAGR, 샤프(거래 기준 연환산), 최대 드로우다운, 승률, 휩소 비율
- 입력 파일: `reports/engine_trades.csv` (닫힌 거래만 사용)

## 설정
설정 파일 예시는 `config/monitoring.yaml.example` 참고.

```yaml
thresholds:
  max_max_drawdown: -0.25
  min_cagr: 0.05
  min_sharpe: 0.40
  min_win_rate: 0.45
```

`config/monitoring.yaml`로 복사 후 값 조정.

## 실행
```bash
# 기본 경로(리포트/설정) 사용
python scripts/run_phase4_monitoring.py

# 사용자 지정 경로
python scripts/run_phase4_monitoring.py --trades reports/engine_trades.csv --config config/monitoring.yaml
```

## 결과물
- 요약: `reports/monitoring_summary.json`, `reports/monitoring_summary.txt`
- 알림 로그: `reports/alerts.log`

## 알림 연동 (선택)
- Slack Incoming Webhook URL 환경변수 `SLACK_WEBHOOK_URL` 설정 또는 `--slack_webhook` 인자 사용

```bash
set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
python scripts/run_phase4_monitoring.py
```

## 예약 실행
- Windows Task Scheduler에 일별/시간별로 등록하여 정기 점검 권장.