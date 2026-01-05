# 전체 구조 리팩토링 계획

## 📋 목차
1. [현재 상태 분석](#현재-상태-분석)
2. [리팩토링 목표](#리팩토링-목표)
3. [단계별 리팩토링 계획](#단계별-리팩토링-계획)
4. [아키텍처 개선](#아키텍처-개선)
5. [구현 우선순위](#구현-우선순위)

---

## 현재 상태 분석

### ✅ 강점
- **모듈화된 전략 시스템**: Strategy, Condition, Filter 추상화 잘 되어 있음
- **벡터화된 백테스팅 엔진**: 성능 최적화 완료
- **캐싱 시스템**: 지표 계산 결과 재사용
- **설정 관리**: YAML 기반 중앙화된 설정

### ⚠️ 개선 필요 사항

#### 1. **아키텍처 문제**
- `src/execution/bot.py`가 너무 많은 책임을 가짐 (God Object)
  - API 통신, 전략 실행, 포지션 관리, 알림 전송 모두 포함
- 의존성 결합도 높음
  - `bot.py`가 `pyupbit`, `strategy`, `telegram` 모두 직접 의존
- 인터페이스 부재
  - Exchange, OrderManager, PositionManager 등 추상화 없음

#### 2. **코드 구조 문제**
- `scripts/` 폴더에 일부 핵심 로직이 분산
  - `data_collector.py`, `run_backtest.py` 등
- 테스트 코드 부재
  - `tests/` 폴더가 비어있음
- 에러 처리 불일치
  - 일부는 예외, 일부는 None 반환

#### 3. **확장성 문제**
- 다른 거래소 추가 어려움 (Upbit에 하드코딩)
- 다른 전략 추가 시 bot.py 수정 필요
- 실시간 데이터 소스 교체 어려움

---

## 리팩토링 목표

### 🎯 핵심 목표
1. **관심사 분리 (Separation of Concerns)**
   - Exchange 추상화
   - Order 관리 분리
   - Position 관리 분리
   - Signal 처리 분리

2. **의존성 역전 (Dependency Inversion)**
   - 인터페이스 기반 설계
   - 의존성 주입 패턴
   - 테스트 가능한 구조

3. **확장성 향상**
   - 플러그인 방식 전략 추가
   - 다중 거래소 지원 준비
   - 다양한 데이터 소스 지원

4. **코드 품질 향상**
   - 테스트 커버리지 확보
   - 타입 안정성 강화
   - 문서화 개선

---

## 단계별 리팩토링 계획

### Phase 0: 프로젝트 구조 현대화 (1주) 🔥 **우선 실행**

#### 0.1 pyproject.toml 기반 프로젝트 구조
```
upbit-quant-system/
├── pyproject.toml          # 프로젝트 메타데이터 및 설정
├── README.md
├── LICENSE
├── .gitignore
├── .python-version         # pyenv 지원
├── src/                    # 소스 코드 (PEP 420)
│   └── upbit_quant/        # 패키지명 변경 고려
├── tests/                  # 테스트 코드
├── docs/                   # 문서
├── scripts/                # 유틸리티 스크립트
├── config/                 # 설정 파일
└── data/                   # 데이터 (gitignore)
```

**목표:**
- PEP 621 표준 준수
- 의존성 관리 표준화
- 개발 도구 통합 설정
- 패키지 설치 가능한 구조

**작업:**
- [ ] `pyproject.toml` 생성 (PEP 621)
- [ ] 프로젝트 메타데이터 정의
- [ ] 의존성 관리 (requirements.txt → pyproject.toml)
- [ ] 빌드 시스템 설정 (setuptools 또는 hatchling)
- [ ] 개발 도구 설정 (black, mypy, pytest, ruff)
- [ ] 패키지 구조 정의
- [ ] `setup.py` 제거 (pyproject.toml로 대체)

#### 0.2 개발 도구 통합
```
pyproject.toml
├── [project]              # PEP 621 메타데이터
├── [build-system]         # 빌드 시스템
├── [tool.black]           # 코드 포맷팅
├── [tool.mypy]            # 타입 체크
├── [tool.pytest.ini_options]  # 테스트 설정
├── [tool.ruff]            # 린터 (flake8 + isort 대체)
└── [tool.coverage]        # 커버리지
```

**작업:**
- [ ] Black 설정 (코드 포맷팅)
- [ ] MyPy 설정 (타입 체크)
- [ ] Ruff 설정 (린팅, import 정렬)
- [ ] Pytest 설정 (테스트 프레임워크)
- [ ] Coverage 설정 (커버리지 측정)
- [ ] Pre-commit hooks 설정 (선택사항)

#### 0.3 패키지 구조 개선
```
src/
└── upbit_quant/           # 또는 기존 구조 유지
    ├── __init__.py
    ├── __version__.py     # 버전 관리
    ├── backtester/
    ├── config/
    ├── data/
    ├── execution/
    ├── strategies/
    └── utils/
```

**작업:**
- [ ] 패키지명 결정 (upbit_quant vs 기존 구조)
- [ ] `__version__.py` 추가
- [ ] `__init__.py`에서 주요 API export
- [ ] 네임스페이스 패키지 고려

#### 0.4 빌드 및 배포 설정
```
# 설치 가능한 패키지로 변환
pip install -e .              # 개발 모드 설치
pip install .                # 일반 설치
pip install -e ".[dev]"      # 개발 의존성 포함
```

**작업:**
- [ ] 개발 의존성 분리 (dev, test, docs)
- [ ] 선택적 의존성 그룹 정의
- [ ] 버전 관리 전략 수립
- [ ] 배포 준비 (PyPI 고려)

### Phase 1: 인터페이스 정의 및 추상화 (1-2주)

#### 1.1 Exchange 인터페이스 정의
```
src/exchange/
├── __init__.py
├── base.py          # Exchange 추상 클래스
├── upbit.py         # Upbit 구현
└── types.py         # 공통 타입 정의
```

**목표:**
- 거래소 독립적인 인터페이스 설계
- Order, Balance, Ticker 등 공통 타입 정의
- Upbit 구현을 인터페이스로 이동

**작업:**
- [ ] `Exchange` 추상 클래스 정의
- [ ] `Order`, `Balance`, `Ticker` 데이터 클래스 정의
- [ ] `UpbitExchange` 구현
- [ ] 기존 `bot.py`의 Upbit 로직을 `UpbitExchange`로 이동

#### 1.2 Order Manager 분리
```
src/execution/
├── __init__.py
├── order_manager.py  # 주문 관리
├── position_manager.py  # 포지션 관리
└── signal_handler.py    # 신호 처리
```

**목표:**
- 주문 실행 로직 분리
- 포지션 추적 로직 분리
- 신호 처리 로직 분리

**작업:**
- [ ] `OrderManager` 클래스 생성
- [ ] `PositionManager` 클래스 생성
- [ ] `SignalHandler` 클래스 생성
- [ ] `bot.py`에서 해당 로직 추출

#### 1.3 Data Source 추상화
```
src/data/
├── __init__.py
├── base.py          # DataSource 추상 클래스
├── upbit_source.py  # Upbit 데이터 소스
└── cache.py         # 기존 캐시 (유지)
```

**목표:**
- 데이터 소스 독립성 확보
- 실시간/히스토리컬 데이터 통합 인터페이스

**작업:**
- [ ] `DataSource` 추상 클래스 정의
- [ ] `UpbitDataSource` 구현
- [ ] 기존 `collector.py` 로직 통합

---

### Phase 2: Bot 리팩토링 (1주)

#### 2.1 TradingBot 재설계
```
src/execution/
├── bot.py           # 메인 봇 (오케스트레이션만)
├── order_manager.py
├── position_manager.py
└── signal_handler.py
```

**목표:**
- `TradingBot`은 오케스트레이션만 담당
- 각 컴포넌트는 인터페이스에 의존

**작업:**
- [ ] `TradingBot`을 Facade 패턴으로 재구성
- [ ] 의존성 주입 구조로 변경
- [ ] 각 컴포넌트를 인터페이스로 주입

#### 2.2 이벤트 기반 아키텍처 도입
```
src/execution/
├── events.py        # 이벤트 정의
├── event_bus.py     # 이벤트 버스
└── handlers/        # 이벤트 핸들러
    ├── trade_handler.py
    ├── signal_handler.py
    └── notification_handler.py
```

**목표:**
- 느슨한 결합
- 확장 가능한 이벤트 처리

**작업:**
- [ ] 이벤트 타입 정의
- [ ] 이벤트 버스 구현
- [ ] 핸들러 등록 시스템

---

### Phase 3: 스크립트 통합 및 정리 (1주)

#### 3.1 스크립트 분류 및 통합
```
scripts/
├── tools/           # 개발/분석 도구
│   ├── compare_*.py
│   └── verify_*.py
├── data/            # 데이터 관리
│   └── collect.py   # data_collector.py 통합
└── backtest/        # 백테스트 실행
    └── run.py       # run_backtest.py 통합

src/
└── cli/             # CLI 인터페이스
    ├── __init__.py
    ├── commands/
    │   ├── backtest.py
    │   ├── collect.py
    │   └── run_bot.py
    └── main.py      # main.py 이동
```

**목표:**
- 스크립트 구조화
- CLI 인터페이스 통합
- 재사용 가능한 모듈로 변환

**작업:**
- [ ] 스크립트 분류 및 이동
- [ ] CLI 프레임워크 도입 (click 또는 argparse)
- [ ] `main.py`를 CLI 진입점으로 재구성

---

### Phase 4: 테스트 인프라 구축 (1-2주)

#### 4.1 테스트 구조 설계
```
tests/
├── __init__.py
├── conftest.py      # pytest 설정
├── unit/
│   ├── test_strategies/
│   ├── test_indicators/
│   ├── test_exchange/
│   └── test_execution/
├── integration/
│   ├── test_backtest/
│   └── test_data_collection/
└── fixtures/
    └── sample_data.py
```

**목표:**
- 단위 테스트 커버리지 80% 이상
- 통합 테스트로 주요 플로우 검증
- Mock을 활용한 외부 의존성 격리

**작업:**
- [ ] pytest 설정
- [ ] 핵심 모듈 단위 테스트 작성
- [ ] Mock Exchange 구현
- [ ] 백테스트 통합 테스트

#### 4.2 테스트 데이터 관리
```
tests/
└── fixtures/
    ├── data/        # 샘플 OHLCV 데이터
    └── config/      # 테스트용 설정
```

**작업:**
- [ ] 샘플 데이터 생성
- [ ] 테스트용 설정 파일
- [ ] Fixture 정의

---

### Phase 5: 에러 처리 및 로깅 표준화 (1주)

#### 5.1 커스텀 예외 정의
```
src/exceptions/
├── __init__.py
├── exchange.py      # Exchange 관련 예외
├── order.py         # Order 관련 예외
└── strategy.py      # Strategy 관련 예외
```

**작업:**
- [ ] 예외 계층 구조 정의
- [ ] 기존 예외 처리 리팩토링
- [ ] 에러 복구 전략 정의

#### 5.2 로깅 표준화
```
src/utils/
└── logger.py        # 기존 개선
    - 구조화된 로깅
    - 로그 레벨 관리
    - 파일/콘솔 출력 분리
```

**작업:**
- [ ] 로그 포맷 표준화
- [ ] 컨텍스트 로깅 추가
- [ ] 성능 로깅 추가

---

### Phase 6: 문서화 및 타입 안정성 (1주)

#### 6.1 타입 힌트 강화
- 모든 공개 API에 타입 힌트 추가
- `mypy`로 타입 체크 통과
- `Protocol` 활용한 구조적 서브타이핑

#### 6.2 문서화
```
docs/
├── architecture.md      # 아키텍처 설명
├── api/                 # API 문서
├── guides/              # 사용 가이드
└── REFACTORING_PLAN.md  # 이 문서
```

**작업:**
- [ ] 아키텍처 다이어그램
- [ ] API 문서 자동 생성 (Sphinx)
- [ ] 사용 예제 추가

---

## 아키텍처 개선

### 현재 아키텍처
```
┌─────────────┐
│  TradingBot │  (God Object)
└──────┬──────┘
       │
       ├─── pyupbit (직접 의존)
       ├─── Strategy (직접 의존)
       ├─── Telegram (직접 의존)
       └─── 모든 로직 포함
```

### 개선된 아키텍처
```
┌─────────────────────────────────────────┐
│           TradingBot (Facade)            │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Signal  │  │  Order   │  │Position│ │
│  │ Handler  │  │ Manager  │  │Manager │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
└───────┼──────────────┼────────────┼──────┘
        │              │            │
        │              │            │
┌───────▼──────────────▼────────────▼──────┐
│         Exchange (Interface)             │
│  ┌──────────┐  ┌──────────┐             │
│  │  Upbit   │  │  (Future)│             │
│  │ Exchange │  │  Binance │             │
│  └──────────┘  └──────────┘             │
└──────────────────────────────────────────┘
```

### 레이어 구조
```
┌─────────────────────────────────────┐
│      Presentation Layer             │
│  (CLI, API, Web UI - Future)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Application Layer               │
│  (TradingBot, SignalHandler)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Domain Layer                    │
│  (Strategy, Order, Position)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Infrastructure Layer            │
│  (Exchange, DataSource, Cache)       │
└─────────────────────────────────────┘
```

---

## 구현 우선순위

### 🔴 High Priority (즉시 시작)
1. **Exchange 인터페이스 정의**
   - 다른 거래소 추가의 기반
   - 테스트 가능성 향상

2. **Order/Position Manager 분리**
   - `bot.py` 복잡도 감소
   - 단위 테스트 가능

3. **테스트 인프라 구축**
   - 리팩토링 안전성 확보
   - 회귀 테스트 가능

### 🟡 Medium Priority (Phase 1 완료 후)
4. **이벤트 기반 아키텍처**
   - 확장성 향상
   - 플러그인 시스템 기반

5. **CLI 통합**
   - 사용성 향상
   - 스크립트 정리

### 🟢 Low Priority (나중에)
6. **다중 거래소 지원**
   - Binance, Coinbase 등
   - Exchange 인터페이스 활용

7. **웹 UI (선택사항)**
   - 대시보드
   - 실시간 모니터링

---

## 마이그레이션 전략

### 점진적 리팩토링
1. **인터페이스 먼저 정의**
   - 기존 코드는 그대로 유지
   - 새 인터페이스와 병행

2. **어댑터 패턴 활용**
   - 기존 코드를 새 인터페이스로 래핑
   - 점진적 교체

3. **기능 플래그**
   - 새/구 코드 전환 가능
   - 롤백 용이

### 테스트 전략
- 기존 기능은 모두 테스트로 보호
- 리팩토링 후 동일 결과 검증
- 통합 테스트로 전체 플로우 검증

---

## 예상 소요 시간

| Phase | 작업 | 예상 시간 |
|-------|------|----------|
| **Phase 0** | **프로젝트 구조 현대화** | **1주** |
| Phase 1 | 인터페이스 정의 | 1-2주 |
| Phase 2 | Bot 리팩토링 | 1주 |
| Phase 3 | 스크립트 통합 | 1주 |
| Phase 4 | 테스트 인프라 | 1-2주 |
| Phase 5 | 에러 처리 표준화 | 1주 |
| Phase 6 | 문서화 | 1주 |
| **총계** | | **7-9주** |

---

## 성공 지표

### 코드 품질
- [ ] 테스트 커버리지 80% 이상
- [ ] Cyclomatic Complexity < 10
- [ ] 타입 체크 100% 통과

### 아키텍처
- [ ] Exchange 인터페이스로 거래소 교체 가능
- [ ] 전략 추가 시 bot.py 수정 불필요
- [ ] 모든 의존성이 인터페이스로 주입

### 유지보수성
- [ ] 새 기능 추가 시간 50% 감소
- [ ] 버그 수정 시간 30% 감소
- [ ] 코드 리뷰 시간 40% 감소

---

## 다음 단계

1. **Phase 0 시작**: pyproject.toml 기반 프로젝트 구조 현대화 ⭐ **최우선**
   - 상세 가이드: `docs/PYPROJECT_MIGRATION.md` 참조
   - 예상 소요: 1주
   - 즉시 시작 가능 (다른 Phase와 독립적)

2. **Phase 1.1 시작**: Exchange 인터페이스 정의
3. **검토 및 승인**: 이 계획 검토 후 Phase별 승인
4. **작업 분할**: 각 Phase를 세부 작업으로 분할
5. **일일 진행 상황 추적**: GitHub Issues/Projects 활용

## Phase 0 상세 가이드

Phase 0의 상세 마이그레이션 가이드는 `docs/PYPROJECT_MIGRATION.md`를 참조하세요.

주요 내용:
- pyproject.toml 구조 및 설정
- 의존성 마이그레이션 방법
- 개발 도구 통합 (black, mypy, ruff, pytest)
- 빌드 시스템 선택 가이드
- CLI 진입점 정의
- 마이그레이션 체크리스트

---

## 참고사항

- 기존 기능은 모두 유지
- 레거시 코드는 `legacy/`에 보존
- 각 Phase는 독립적으로 테스트 가능
- 점진적 마이그레이션으로 리스크 최소화
