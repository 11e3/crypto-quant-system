# Phase 3 완료: 스크립트 통합 및 정리

## 완료된 작업

### ✅ 1. CLI 구조 생성
- **파일**: `src/cli/`
- `main.py`: CLI 진입점 및 명령어 그룹
- `commands/`: 개별 명령어 모듈
  - `collect.py`: 데이터 수집 명령어
  - `backtest.py`: 백테스트 명령어
  - `run_bot.py`: 봇 실행 명령어

### ✅ 2. CLI 명령어 구현
- **collect**: Upbit 데이터 수집
  - `--tickers`: 수집할 티커 목록
  - `--intervals`: 수집할 인터벌 목록
  - `--full-refresh`: 전체 새로고침
- **backtest**: 백테스트 실행
  - `--tickers`: 백테스트할 티커 목록
  - `--interval`: 데이터 인터벌
  - `--strategy`: 전략 변형 (vanilla, minimal, legacy)
  - `--initial-capital`, `--fee-rate`, `--max-slots`: 백테스트 설정
  - `--output`: 리포트 출력 디렉토리
- **run-bot**: 라이브 트레이딩 봇 실행
  - `--config`: 설정 파일 경로
  - `--dry-run`: 드라이런 모드 (향후 구현)

### ✅ 3. 스크립트 분류 및 정리
- **scripts/tools/**: 개발/분석 도구
  - `compare_trades.py`
  - `compare_metrics.py`
  - `check_logic_errors.py`
  - `verify_strategy_logic.py`
  - `verify_strategy_logic_detailed.py`
- **scripts/backtest/**: 백테스트 관련 스크립트
  - `legacy_bt_with_trades.py`
  - `run_backtest.py` (레거시)
- **scripts/data/**: 데이터 관리 스크립트
  - `data_collector.py` (레거시, CLI 권장)

### ✅ 4. pyproject.toml 업데이트
- CLI 진입점 추가: `upbit-quant = "src.cli.main:main"`
- `click` 의존성 추가

### ✅ 5. main.py 업데이트
- CLI 진입점으로 재구성

## 주요 개선사항

### 1. 통합된 CLI 인터페이스
- 모든 주요 기능을 CLI로 통합
- 일관된 명령어 구조
- 도움말 및 옵션 자동 생성

### 2. 스크립트 구조화
- 목적별 디렉토리 분리
- README 파일로 용도 설명
- 개발 도구와 프로덕션 스크립트 분리

### 3. 사용 편의성
- 간단한 명령어로 모든 기능 접근
- 옵션 기반 설정
- 일관된 인터페이스

## 사용 예시

### 데이터 수집
```bash
# 기본 수집
upbit-quant collect

# 특정 티커만 수집
upbit-quant collect --tickers KRW-BTC KRW-ETH

# 전체 새로고침
upbit-quant collect --full-refresh
```

### 백테스트
```bash
# 기본 백테스트
upbit-quant backtest

# 커스텀 설정
upbit-quant backtest \
  --tickers KRW-BTC KRW-ETH \
  --interval day \
  --strategy vanilla \
  --initial-capital 1000000 \
  --output reports/my_backtest
```

### 봇 실행
```bash
# 기본 설정으로 실행
upbit-quant run-bot

# 커스텀 설정 파일
upbit-quant run-bot --config custom_config.yaml
```

## 파일 구조

```
src/cli/
├── __init__.py
├── main.py              # CLI 진입점
└── commands/
    ├── __init__.py
    ├── collect.py       # 데이터 수집
    ├── backtest.py      # 백테스트
    └── run_bot.py       # 봇 실행

scripts/
├── tools/               # 개발 도구
├── backtest/            # 백테스트 스크립트
└── data/                # 데이터 관리 스크립트

main.py                  # CLI 진입점 (간단한 래퍼)
```

## 다음 단계

Phase 3 완료! 전체 리팩토링의 주요 Phase가 완료되었습니다.

남은 작업:
- Phase 2.2 통합: TradingBotFacade에 이벤트 시스템 통합 (선택사항)
- 추가 개선사항 적용
- 테스트 코드 작성
- 문서화 보완

## 참고사항

- 기존 스크립트는 하위 호환성을 위해 유지
- CLI 사용을 권장하지만 스크립트도 계속 작동
- 점진적 마이그레이션 가능
