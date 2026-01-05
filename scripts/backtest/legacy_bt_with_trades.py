"""
Modified legacy/bt.py to record trades for comparison.
"""

import datetime
import os

import pandas as pd

# Configuration
FEE = 0.0005  # 0.05%
SLIPPAGE = 0.0005  # 0.05%
Initial_Capital = 1.0
TARGET_SLOTS = 4

# --- [Dynamic Filter Configuration] ---
SMA_PERIOD = 5
N = 2
# --------------------------------------

TREND_SMA_PERIOD = SMA_PERIOD * N
SHORT_TERM_NOISE_PERIOD = SMA_PERIOD
LONG_TERM_NOISE_PERIOD = SMA_PERIOD * N


def parse_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_date(dt_str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def calculate_cagr(start_val, end_val, days):
    if days <= 0:
        return 0.0
    if start_val <= 0:
        return 0.0
    if end_val <= 0:
        return -100.0
    return (end_val / start_val) ** (365.0 / days) - 1.0


def calculate_mdd(cum_returns):
    max_val = -float("inf")
    mdd = 0.0
    for val in cum_returns:
        if val > max_val:
            max_val = val
        if max_val > 0:
            dd = (max_val - val) / max_val
            if dd > mdd:
                mdd = dd
    return mdd * 100.0


def load_and_prep_data(filepath, noise_period=SHORT_TERM_NOISE_PERIOD, sma_period=SMA_PERIOD):
    # Read parquet file directly (no context manager needed)
    df = pd.read_parquet(filepath)

    # Reset index if datetime index exists
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        # Rename index column to 'date' if it exists
        if "datetime" in df.columns:
            df = df.rename(columns={"datetime": "date"})
        elif "index" in df.columns:
            df = df.rename(columns={"index": "date"})

    # Ensure 'date' column exists
    if "date" not in df.columns:
        # If no date column, create one from index
        df["date"] = df.index

    # Convert to list of dicts
    raw_data = df.to_dict(orient="records")

    if not raw_data:
        return []
    raw_data.sort(key=lambda x: x["date"])

    processed_data = {}
    noise_ratios = []

    trend_sma_period = TREND_SMA_PERIOD
    long_noise_period = LONG_TERM_NOISE_PERIOD

    for i in range(len(raw_data)):
        d = raw_data[i]
        rng = d["high"] - d["low"]
        noise = (1 - abs(d["close"] - d["open"]) / rng) if rng > 0 else 0.0
        noise_ratios.append(noise)

        # 데이터가 충분치 않으면 스킵
        if i < max(noise_period, trend_sma_period, long_noise_period):
            continue

        # 단기 노이즈 (K값)
        short_noise = sum(noise_ratios[i - noise_period : i]) / noise_period

        # 장기 노이즈
        long_noise = sum(noise_ratios[i - long_noise_period : i]) / long_noise_period

        # SMA for Trend
        closes_trend = [x["close"] for x in raw_data[i - trend_sma_period : i]]
        sma_trend = sum(closes_trend) / trend_sma_period

        # Exit Signal용 sma (기본)
        closes = [x["close"] for x in raw_data[i - SMA_PERIOD : i]]
        sma = sum(closes) / SMA_PERIOD

        prev_day = raw_data[i - 1]

        processed_data[d["date"]] = {
            "open": d["open"],
            "high": d["high"],
            "low": d["low"],
            "close": d["close"],
            "target": d["open"] + (prev_day["high"] - prev_day["low"]) * short_noise,
            "sma": sma,
            "sma_trend": sma_trend,
            "short_noise": short_noise,  # K
            "long_noise": long_noise,  # Baseline
        }
    return processed_data


def run_portfolio_simulation(file_paths):
    print(f"\n{'=' * 20} PORTFOLIO SIMULATION (Dynamic Relative Filter) {'=' * 20}")
    print(f"SMA: {SMA_PERIOD}, N: {N}")

    market_data = {}
    all_dates = set()
    coin_names = []

    for fp in file_paths:
        c_name = os.path.basename(fp).replace("KRW-", "").replace("_day.parquet", "")
        coin_names.append(c_name)
        p_data = load_and_prep_data(fp)
        for dt, row in p_data.items():
            if dt not in market_data:
                market_data[dt] = {}
            market_data[dt][c_name] = row
            all_dates.add(dt)

    sorted_dates = sorted(list(all_dates))
    if not sorted_dates:
        return

    cash = Initial_Capital
    positions = {}
    trades = []  # Track all trades
    equity_curve = []  # Track equity curve

    # 4슬롯 유지 (Best Case)
    MAX_SLOTS = min(len(file_paths), TARGET_SLOTS)

    for dt in sorted_dates:
        daily_market = market_data.get(dt, {})

        # [Step 1] 매도 (Exit) - sma 이탈
        sold_coins = []
        for coin, pos in positions.items():
            if coin not in daily_market:
                continue
            row = daily_market[coin]

            if row["close"] < row["sma"]:
                sell_price = row["close"] * (1 - SLIPPAGE)
                revenue = pos["amount"] * sell_price * (1 - FEE)
                cash += revenue

                # Record exit trade
                entry_price = pos.get("entry_price", 0)
                entry_date = pos.get("entry_date", dt)
                pnl = revenue - (pos["amount"] * entry_price)
                pnl_pct = (sell_price / entry_price - 1) * 100 if entry_price > 0 else 0

                trades.append(
                    {
                        "ticker": f"KRW-{coin}",
                        "entry_date": entry_date,
                        "entry_price": entry_price,
                        "exit_date": dt,
                        "exit_price": sell_price,
                        "amount": pos["amount"],
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "is_whipsaw": False,
                    }
                )

                sold_coins.append(coin)

        for c in sold_coins:
            del positions[c]

        # [Step 2] 매수 (Entry)
        candidates = [c for c in coin_names if c in daily_market]
        # 노이즈 낮은 순 정렬 (Relative Check를 하더라도 낮은 게 좋음)
        candidates.sort(key=lambda x: daily_market[x]["short_noise"])

        for coin in candidates:
            if coin in positions:
                continue
            row = daily_market[coin]

            available_slots = MAX_SLOTS - len(positions)
            if available_slots <= 0:
                break

            # --- [진입 조건] ---
            # 1. Breakout & sma
            basic_cond = (row["target"] > row["sma"]) and (row["high"] >= row["target"])

            # 2. Trend Filter
            trend_cond = row["target"] > row["sma_trend"]

            # 3. Dynamic Relative Noise Filter
            # "지금 시장이 평소보다 얌전한가?"
            noise_cond = row["short_noise"] < row["long_noise"]

            if basic_cond and trend_cond and noise_cond:
                invest_money = cash / available_slots

                # 휩소 체크
                if row["close"] < row["sma"]:
                    buy_price = row["target"] * (1 + SLIPPAGE)
                    sell_price = row["close"] * (1 - SLIPPAGE)
                    amount = invest_money / buy_price * (1 - FEE)
                    return_money = amount * sell_price * (1 - FEE)
                    cash = cash - invest_money + return_money

                    # Record whipsaw trade
                    pnl = return_money - invest_money
                    pnl_pct = (sell_price / buy_price - 1) * 100

                    trades.append(
                        {
                            "ticker": f"KRW-{coin}",
                            "entry_date": dt,
                            "entry_price": buy_price,
                            "exit_date": dt,
                            "exit_price": sell_price,
                            "amount": amount,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "is_whipsaw": True,
                        }
                    )
                else:
                    buy_price = row["target"] * (1 + SLIPPAGE)
                    amount = invest_money / buy_price * (1 - FEE)
                    positions[coin] = {
                        "amount": amount,
                        "entry_price": buy_price,
                        "entry_date": dt,
                    }
                    cash -= invest_money

                    # Record entry (open position)
                    trades.append(
                        {
                            "ticker": f"KRW-{coin}",
                            "entry_date": dt,
                            "entry_price": buy_price,
                            "exit_date": None,
                            "exit_price": None,
                            "amount": amount,
                            "pnl": 0.0,
                            "pnl_pct": 0.0,
                            "is_whipsaw": False,
                        }
                    )

        # Calculate daily equity
        daily_equity = cash
        for coin, pos in positions.items():
            if coin in daily_market:
                daily_equity += pos["amount"] * daily_market[coin]["close"]
        equity_curve.append(daily_equity)
        print(f"EQUITY_CURVE:{daily_equity}")

    if len(equity_curve) == 0:
        return [], [], []

    final_equity = equity_curve[-1]
    total_days = (sorted_dates[-1] - sorted_dates[0]).days

    from legacy.bt import calculate_cagr, calculate_mdd

    cagr = calculate_cagr(Initial_Capital, final_equity, total_days) * 100
    mdd = calculate_mdd(equity_curve)

    print(
        f"[PORTFOLIO FINAL] CAGR: {cagr:.2f}% | MDD: {mdd:.2f}% | Calmar: {cagr / mdd if mdd > 0 else 0:.2f}"
    )
    print(f"Final Equity: {final_equity:.2f}")

    return trades, equity_curve, sorted_dates


def main():
    upbit_files = [
        "data/raw/KRW-BTC_day.parquet",
        "data/raw/KRW-ETH_day.parquet",
        "data/raw/KRW-XRP_day.parquet",
        "data/raw/KRW-TRX_day.parquet",
    ]
    trades, equity_curve, dates = run_portfolio_simulation(upbit_files)

    # Save equity curve
    import json

    equity_data = {
        "equity_curve": equity_curve,
        "dates": [str(d) for d in dates],
    }
    with open("reports/legacy_equity_curve.json", "w") as f:
        json.dump(equity_data, f)
    print("\n[+] Legacy equity curve saved to: reports/legacy_equity_curve.json")

    if trades:
        trades_df = pd.DataFrame(trades)
        output_path = "reports/legacy_trades.csv"
        trades_df.to_csv(output_path, index=False)
        print(f"\n[+] Legacy trades saved to: {output_path}")
        print(f"\n[Legacy] Total Trades: {len(trades_df)}")
        print(f"[Legacy] Closed Trades: {len(trades_df[trades_df['exit_date'].notna()])}")
        print(f"[Legacy] Open Trades: {len(trades_df[trades_df['exit_date'].isna()])}")
        print("\n[Legacy] First 20 Trades:")
        print(trades_df.head(20).to_string())
    else:
        print("\n[Legacy] No trades found!")


if __name__ == "__main__":
    main()
