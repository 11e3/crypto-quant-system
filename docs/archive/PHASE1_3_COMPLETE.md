# Phase 1.3 완료: Data Source 추상화

## 완료된 작업

### ✅ 1. DataSource 인터페이스 정의
- **파일**: `src/data/base.py`
- `DataSource` 추상 클래스:
  - `get_ohlcv()`: OHLCV 데이터 조회
  - `get_current_price()`: 현재가 조회
  - `save_ohlcv()`: 데이터 저장
  - `load_ohlcv()`: 데이터 로드
  - `update_ohlcv()`: 증분 업데이트
- 예외 클래스:
  - `DataSourceError` (기본)
  - `DataSourceConnectionError`
  - `DataSourceNotFoundError`

### ✅ 2. UpbitDataSource 구현
- **파일**: `src/data/upbit_source.py`
- 모든 DataSource 인터페이스 메서드 구현
- pyupbit API를 사용한 데이터 페칭
- Parquet 파일 기반 로컬 스토리지
- 증분 업데이트 지원
- 날짜 범위 기반 데이터 조회 지원

### ✅ 3. 패키지 통합
- `src/data/__init__.py`에서 DataSource 관련 클래스 export
- 기존 `UpbitDataCollector`와 공존 (하위 호환성 유지)

## 주요 개선사항

### 1. 데이터 소스 독립성
- `DataSource` 인터페이스로 다양한 데이터 소스 지원 가능
- 다른 거래소나 데이터 제공자 추가 시 인터페이스만 구현하면 됨

### 2. 통합 인터페이스
- 실시간 데이터와 히스토리컬 데이터를 동일한 인터페이스로 처리
- `Exchange.get_ohlcv()`와 `DataSource.get_ohlcv()` 통합 가능

### 3. 확장성
- `UpbitDataCollector`는 고급 기능 (pagination, bulk collection) 제공
- `UpbitDataSource`는 표준 인터페이스 제공
- 두 가지 모두 사용 가능

## 파일 구조

```
src/data/
├── __init__.py
├── base.py              # DataSource 인터페이스
├── upbit_source.py      # UpbitDataSource 구현
├── collector.py         # UpbitDataCollector (기존, 유지)
├── cache.py             # IndicatorCache (기존, 유지)
└── converters.py        # CSV 변환 (기존, 유지)
```

## 사용 예시

### DataSource 인터페이스 사용
```python
from src.data import UpbitDataSource

source = UpbitDataSource()

# 데이터 조회
df = source.get_ohlcv("KRW-BTC", interval="day", count=100)

# 증분 업데이트
updated_df = source.update_ohlcv("KRW-BTC", interval="day")

# 데이터 저장/로드
source.save_ohlcv("KRW-BTC", "day", df)
loaded_df = source.load_ohlcv("KRW-BTC", "day")
```

### 기존 UpbitDataCollector 사용 (하위 호환)
```python
from src.data import UpbitDataCollector

collector = UpbitDataCollector()
count = collector.collect("KRW-BTC", "day")
```

## 다음 단계

Phase 1.3 완료! Phase 1 전체 완료!

다음은:
- **Phase 2: Bot 리팩토링**
  - TradingBot을 Facade 패턴으로 재구성
  - 의존성 주입 구조로 변경
  - 이벤트 기반 아키텍처 도입

## 참고사항

- `UpbitDataCollector`는 기존 코드와의 호환성을 위해 유지
- `UpbitDataSource`는 새로운 표준 인터페이스
- 두 클래스 모두 동일한 기능을 제공하지만 인터페이스가 다름
- 필요에 따라 선택적으로 사용 가능
