# API 문서

이 디렉토리에는 API 참조 문서가 포함됩니다.

## 주요 모듈

### Exchange Layer
- `src.exchange.Exchange`: 거래소 인터페이스
- `src.exchange.UpbitExchange`: Upbit 구현

### Execution Layer
- `src.execution.TradingBotFacade`: 거래 봇 Facade
- `src.execution.OrderManager`: 주문 관리
- `src.execution.PositionManager`: 포지션 관리
- `src.execution.SignalHandler`: 신호 처리

### Strategy Layer
- `src.strategies.Strategy`: 전략 기본 클래스
- `src.strategies.volatility_breakout.VanillaVBO`: VBO 전략

### Data Layer
- `src.data.DataSource`: 데이터 소스 인터페이스
- `src.data.UpbitDataSource`: Upbit 데이터 소스
- `src.data.IndicatorCache`: 지표 캐싱

### Backtest Layer
- `src.backtester.VectorizedBacktestEngine`: 백테스트 엔진
- `src.backtester.BacktestReport`: 리포트 생성

## 자동 생성 문서 (예정)

Sphinx를 사용한 자동 API 문서 생성이 계획되어 있습니다.

```bash
# 문서 생성 (예정)
cd docs
sphinx-build -b html . _build/html
```
