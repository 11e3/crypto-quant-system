import datetime
import time

import pyupbit
import requests

# --- [CONFIGURATION] ---
ACCESS_KEY = ""
SECRET_KEY = ""

# Telegram Settings
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# Trading Settings
TICKERS = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-TRX"]
FEE = 0.0005
TARGET_SLOTS = 4  # 최대 보유 가능 종목 수

# Strategy Parameters (Based on bt5.py)
SMA_PERIOD = 5  # 단기 이평선 및 단기 노이즈 기간
N = 2  # 장기 기간 배수
TREND_SMA_PERIOD = SMA_PERIOD * N  # 10일 (추세 판단용)
LONG_NOISE_PERIOD = SMA_PERIOD * N  # 10일 (노이즈 베이스라인)

# Initialize Upbit
upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)


def send_telegram(message):
    """Sends a message to Telegram."""
    if not TELEGRAM_TOKEN or "YOUR_" in TELEGRAM_TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")


def get_balance_safe(currency):
    try:
        balance = upbit.get_balance(currency)
        if balance is None:
            return 0.0
        return float(balance)
    except Exception:
        return 0.0


def get_krw_balance():
    return get_balance_safe("KRW")


def get_current_price_safe(ticker):
    try:
        price = pyupbit.get_current_price(ticker)
        if price is None:
            return 0.0
        return float(price)
    except Exception:
        return 0.0


def get_daily_metrics(ticker):
    """
    bt5.py 로직에 맞춰 지표 계산:
    1. Short Noise (K): 최근 5일 노이즈 평균
    2. Long Noise: 최근 10일 노이즈 평균
    3. SMA5: Exit용
    4. SMA10: Trend Filter용
    """
    try:
        # 충분한 데이터를 가져옴 (20일)
        df = pyupbit.get_ohlcv(ticker, interval="day", count=20)
        if df is None or len(df) < TREND_SMA_PERIOD:
            return None

        # 노이즈 계산: 1 - abs(open-close)/(high-low)
        # 0으로 나누기 방지 처리
        ranges = df["high"] - df["low"]
        noise_series = 1 - abs(df["open"] - df["close"]) / ranges.replace(0, 1)
        # range가 0인 경우 noise는 0으로 처리 (혹은 1로 처리, 여기선 안전하게 0)
        noise_series[ranges == 0] = 0

        # 어제까지의 데이터만 사용 (오늘 데이터 제외)
        # iloc[-1]은 오늘(현재 진행중), iloc[-2]가 어제 확정봉

        # 1. Short Noise (최근 5일 평균) -> K값
        short_noise = noise_series.iloc[-1 - SMA_PERIOD : -1].mean()

        # 2. Long Noise (최근 10일 평균) -> 필터 기준값
        long_noise = noise_series.iloc[-1 - LONG_NOISE_PERIOD : -1].mean()

        # 3. SMA5
        sma5 = df["close"].iloc[-1 - SMA_PERIOD : -1].mean()

        # 4. SMA10 (Trend SMA)
        sma10 = df["close"].iloc[-1 - TREND_SMA_PERIOD : -1].mean()

        # Target Calculation
        today_open = df.iloc[-1]["open"]
        prev_range = df.iloc[-2]["high"] - df.iloc[-2]["low"]
        target = today_open + prev_range * short_noise

        return {
            "target": target,
            "k": short_noise,
            "long_noise": long_noise,
            "sma5": sma5,
            "sma10": sma10,
        }
    except Exception as e:
        print(f"Error metrics {ticker}: {e}")
        return None


def sell_all(ticker):
    try:
        currency = ticker.split("-")[1]
        balance = get_balance_safe(currency)
        curr_price = get_current_price_safe(ticker)
        if balance > 0 and curr_price > 0 and (balance * curr_price > 5000):
            upbit.sell_market_order(ticker, balance)
            send_telegram(f"[SELL] Sold all {ticker}")
    except Exception as e:
        print(f"Sell Error {ticker}: {e}")


def run_bot():
    print("Starting Trading Bot (Dynamic Relative Noise Strategy)...")

    # Run Diagnostic
    try:
        upbit.get_balances()
        print("SUCCESS: API Keys are valid and working.")
    except Exception as e:
        print(f"!!! API CONNECTION FAILED: {e}")
        time.sleep(3)

    send_telegram("🚀 Bot Started: Dynamic Noise Filter (N=2) + Trend Filter")

    has_bought = dict.fromkeys(TICKERS, False)
    target_info = {}  # stores full dict of metrics

    print("Initializing Targets...")
    for ticker in TICKERS:
        metrics = get_daily_metrics(ticker)
        if metrics:
            target_info[ticker] = metrics
            print(
                f"[{ticker}] Tgt:{metrics['target']:.0f} | K:{metrics['k']:.2f} vs Base:{metrics['long_noise']:.2f} | SMA5:{metrics['sma5']:.0f} SMA10:{metrics['sma10']:.0f}"
            )
        else:
            print(f"{ticker}: Failed to calculate targets.")
        time.sleep(0.5)

    # Re-check holdings on restart
    print("Checking existing holdings...")
    for ticker in TICKERS:
        currency = ticker.split("-")[1]
        balance = get_balance_safe(currency)
        curr_price = get_current_price_safe(ticker)
        if balance > 0 and curr_price > 0 and (balance * curr_price > 5000):
            has_bought[ticker] = True
            print(f"✅ Recovered: Holding {ticker}")

    print("Entering Trading Loop...")

    try:
        wm = pyupbit.WebSocketManager("ticker", TICKERS)
    except Exception as e:
        print(f"WebSocket Connection Failed: {e}")
        return

    while True:
        try:
            data = wm.get()
            if data["type"] == "ticker":
                ticker = data["code"]
                curr_price = data["trade_price"]

                now = datetime.datetime.now()

                # --- [Daily Reset Logic: 09:00:00] ---
                if now.hour == 9 and now.minute == 0 and now.second <= 10:
                    wm.terminate()
                    print("Performing Daily Reset...")
                    time.sleep(5)

                    # 1. Exit Logic (종가가 SMA5 이탈 시 매도)
                    for t in TICKERS:
                        try:
                            # 어제 종가 확인을 위해 데이터 호출
                            df = pyupbit.get_ohlcv(t, interval="day", count=10)
                            if df is not None and len(df) >= 7:
                                yesterday_close = df.iloc[-2]["close"]
                                # Exit 기준 SMA5 (어제 기준)
                                sma5_exit = df["close"].iloc[-7:-2].mean()

                                if has_bought[t]:
                                    if yesterday_close < sma5_exit:
                                        sell_all(t)
                                        has_bought[t] = False
                                        send_telegram(
                                            f"📉 [EXIT] {t} Trend Broken (Close {yesterday_close} < SMA {sma5_exit:.1f})"
                                        )
                                    else:
                                        send_telegram(f"✊ [HOLD] {t} Trend Intact")
                        except Exception as e:
                            print(f"Error daily check {t}: {e}")

                    # 2. Recalculate Targets
                    target_info = {}
                    msg = "[DAILY UPDATE]\n"

                    # 매수 우선순위를 위해 리스트에 담기 (선택사항이나 여기선 단순 루프)
                    for t in TICKERS:
                        for _ in range(3):  # Retry
                            metrics = get_daily_metrics(t)
                            if metrics:
                                target_info[t] = metrics
                                msg += f"{t}: Tgt {metrics['target']:.0f}, K {metrics['k']:.2f}\n"
                                break
                            time.sleep(1)
                    send_telegram(msg)
                    print(msg)

                    time.sleep(6)
                    wm = pyupbit.WebSocketManager("ticker", TICKERS)
                    continue

                # --- [Entry Logic] ---
                if has_bought[ticker]:
                    continue

                metrics = target_info.get(ticker)
                if not metrics:
                    continue

                # 1. Basic Breakout
                cond_breakout = curr_price >= metrics["target"]
                # 2. Above SMA5
                cond_sma5 = metrics["target"] > metrics["sma5"]
                # 3. Above Trend SMA (SMA10)
                cond_trend = metrics["target"] > metrics["sma10"]
                # 4. Dynamic Relative Noise (Short < Long)
                cond_noise = metrics["k"] < metrics["long_noise"]

                if cond_breakout and cond_sma5 and cond_trend and cond_noise:
                    krw_bal = get_krw_balance()
                    if krw_bal > 5000:
                        # 자금 분할 (최대 4분할)
                        current_held = sum(has_bought.values())
                        available_slots = TARGET_SLOTS - current_held

                        if available_slots > 0:
                            # 남은 자금을 남은 슬롯 수로 나눔 (단, 이미 다른거 샀으면 그만큼 줄어든 예수금에서 나눔)
                            # 간단하게: 현재 예수금 / 남은 슬롯 수
                            buy_amount = (krw_bal / available_slots) * (1 - FEE)

                            if buy_amount > 5000:
                                res = upbit.buy_market_order(ticker, buy_amount)
                                if res and "uuid" in res:
                                    has_bought[ticker] = True
                                    msg = (
                                        f"🔥 [BUY] {ticker}\n"
                                        f"Price: {curr_price}\n"
                                        f"Target: {metrics['target']:.0f}\n"
                                        f"Noise: {metrics['k']:.2f} < {metrics['long_noise']:.2f}"
                                    )
                                    send_telegram(msg)
                                    print(msg)
                                else:
                                    print(f"Buy Failed: {res}")

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(3)
            try:
                wm.terminate()
            except:
                pass
            wm = pyupbit.WebSocketManager("ticker", TICKERS)


if __name__ == "__main__":
    run_bot()
