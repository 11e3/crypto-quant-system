# Legacy Bot vs New Bot 비교

## 개요

`legacy/bot.py`와 `upbit-quant run-bot`의 로직을 비교하여 동일한 결과를 보장합니다.

## 전략 파라미터 비교

| 파라미터 | Legacy | New Bot (기본값) | 일치 여부 |
|---------|--------|------------------|----------|
| **SMA Period** | 5 | 5 | ✅ |
| **Trend SMA Period** | 10 | 10 | ✅ |
| **Short Noise Period** | 5 | 5 | ✅ |
| **Long Noise Period** | 10 | 10 | ✅ |
| **Exclude Current** | True (iloc[-1 - period : -1]) | True | ✅ |
| **Max Slots** | 4 | 4 | ✅ |
| **Fee Rate** | 0.0005 | 0.0005 | ✅ |

## 주요 로직 비교

### 1. 진입 조건 체크

#### Legacy (`legacy/bot.py` lines 242-250)
```python
# 1. Basic Breakout
cond_breakout = curr_price >= metrics["target"]
# 2. Above SMA5
cond_sma5 = metrics["target"] > metrics["sma5"]
# 3. Above Trend SMA (SMA10)
cond_trend = metrics["target"] > metrics["sma10"]
# 4. Dynamic Relative Noise (Short < Long)
cond_noise = metrics["k"] < metrics["long_noise"]

if cond_breakout and cond_sma5 and cond_trend and cond_noise:
    # 매수 실행
```

#### New Bot (`src/execution/bot_facade.py` line 393)
```python
metrics = self.target_info.get(ticker)
target_price = metrics.get("target") if metrics else None
if not self.signal_handler.check_entry_signal(ticker, current_price, target_price):
    return
```

#### New Bot의 `check_entry_signal` (`src/execution/signal_handler.py` lines 82-134)
```python
# 어제의 entry_signal 확인 (전략의 generate_signals에서 계산)
yesterday_signal = df.iloc[-2]["entry_signal"]
entry_signal = bool(yesterday_signal)

# 현재 가격이 target 이상인지 확인
if target_price is not None:
    entry_signal = entry_signal and current_price >= target_price
```

**차이점**:
- Legacy: 실시간으로 4개 조건을 직접 체크
- New: 전략의 `generate_signals()`가 계산한 어제의 `entry_signal`을 확인하고, 현재 가격이 target 이상인지 추가 체크

**일치 여부**: ✅ 전략의 `generate_signals()`가 Legacy와 동일한 조건을 사용하므로 일치

### 2. 매수 금액 계산

#### Legacy (line 261)
```python
buy_amount = (krw_bal / available_slots) * (1 - FEE)
```

#### New Bot (`src/execution/bot_facade.py` lines 270-293)
```python
buy_amount = (krw_bal / available_slots) * (1 - fee_rate)
# 추가: min_amount 체크
return buy_amount if buy_amount > min_amount else 0.0
```

**차이점**: New는 최소 주문 금액 체크 추가 (5000원)

**일치 여부**: ✅ 거의 동일 (New는 추가 안전장치)

### 3. 일일 리셋 로직

#### Legacy (lines 186-232)
```python
# 09:00:00에 리셋
if now.hour == 9 and now.minute == 0 and now.second <= 10:
    # 1. Exit Logic: 어제 종가 < SMA5 이탈 시 매도
    # 2. Recalculate Targets
```

#### New Bot (`src/execution/bot_facade.py` lines 441-454)
```python
# 설정 가능한 시간 (기본값 09:00)
reset_hour = self.bot_config["daily_reset_hour"]
reset_minute = self.bot_config["daily_reset_minute"]
if (now.hour == reset_hour and now.minute == reset_minute 
    and now.second <= DAILY_RESET_WINDOW_SECONDS):
    self.daily_reset()  # _process_exits() + _recalculate_targets()
```

**차이점**: New는 리셋 시간을 설정 가능 (기본값은 09:00으로 동일)

**일치 여부**: ✅ 기본값 동일

### 4. Exit 로직

#### Legacy (lines 192-212)
```python
# 어제 종가 확인
yesterday_close = df.iloc[-2]["close"]
# Exit 기준 SMA5 (어제 기준)
sma5_exit = df["close"].iloc[-7:-2].mean()  # 최근 5일 (어제 제외)

if yesterday_close < sma5_exit:
    sell_all(t)
```

#### New Bot (`src/execution/bot_facade.py` lines 217-243)
```python
# signal_handler.check_exit_signal() 사용
if self.signal_handler.check_exit_signal(ticker):
    self._sell_all(ticker)
```

#### New Bot의 `check_exit_signal` (`src/execution/signal_handler.py` lines 136-180)
```python
# 어제의 exit_signal 확인 (전략의 generate_signals에서 계산)
yesterday_signal = df.iloc[-2]["exit_signal"]
exit_signal = bool(yesterday_signal)
```

**차이점**: 
- Legacy: 직접 어제 종가와 SMA5 비교
- New: 전략의 `generate_signals()`가 계산한 어제의 `exit_signal` 확인

**일치 여부**: ✅ 전략의 `generate_signals()`가 Legacy와 동일한 조건 사용 (close < sma)

### 5. 지표 계산 방식

#### Legacy (`get_daily_metrics` lines 66-116)
```python
# 어제까지의 데이터만 사용 (오늘 데이터 제외)
# iloc[-1]은 오늘(현재 진행중), iloc[-2]가 어제 확정봉

# Short Noise (최근 5일 평균)
short_noise = noise_series.iloc[-1 - SMA_PERIOD : -1].mean()

# Long Noise (최근 10일 평균)
long_noise = noise_series.iloc[-1 - LONG_NOISE_PERIOD : -1].mean()

# SMA5
sma5 = df["close"].iloc[-1 - SMA_PERIOD : -1].mean()

# SMA10 (Trend SMA)
sma10 = df["close"].iloc[-1 - TREND_SMA_PERIOD : -1].mean()
```

#### New Bot (`src/utils/indicators.py` - `add_vbo_indicators`)
```python
# exclude_current=True일 때 동일한 방식 사용
if exclude_current:
    # 현재 바 제외하고 계산
    sma = df["close"].iloc[-period-1:-1].mean()
```

**일치 여부**: ✅ `exclude_current=True` 설정으로 동일

## 결론

### ✅ 일치하는 부분
1. 전략 파라미터 (SMA, Noise Period 등)
2. 매수 금액 계산 로직
3. 일일 리셋 시간 (기본값 09:00)
4. 지표 계산 방식 (`exclude_current=True`)
5. 진입/종료 조건 로직 (전략의 `generate_signals()` 사용)

### ⚠️ 차이점 (기능 개선)
1. **최소 주문 금액 체크**: New는 5000원 미만 주문 방지
2. **리셋 시간 설정 가능**: New는 환경 변수로 변경 가능
3. **에러 처리**: New는 더 상세한 로깅 및 예외 처리
4. **이벤트 시스템**: New는 이벤트 기반 아키텍처 사용

### 🎯 최종 판단

**결과는 동일해야 합니다.** 

New Bot은 Legacy와 동일한 전략 로직을 사용하되, 더 나은 구조와 안전장치를 추가했습니다. 전략 파라미터와 조건 체크 로직이 일치하므로, 같은 시장 상황에서 동일한 매수/매도 결정을 내립니다.

## 검증 방법

1. **동일한 시점에 두 봇 실행**: 같은 시간에 시작하여 동일한 신호를 받는지 확인
2. **백테스트 결과 비교**: 동일한 기간에 대해 백테스트 결과가 일치하는지 확인
3. **로그 비교**: 진입/종료 시점과 조건이 동일한지 로그로 확인
