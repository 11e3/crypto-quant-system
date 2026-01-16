"""
BTC Market Filter Strategy Backtest

Buy Conditions (ALL must be true):
- Daily high >= Target price (Open + (Prev High - Prev Low) × 0.5)
- Previous close > Previous MA5
- Previous BTC close > Previous BTC MA20

Sell Conditions (ANY triggers exit):
- Previous close < Previous MA5
- Previous BTC close < Previous BTC MA20

Execution Prices:
- Buy: Target price + 0.05% slippage
- Sell: Daily open - 0.05% slippage
- Fee: 0.05%
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyupbit


def load_btc_data() -> pd.DataFrame:
    """Load BTC daily data from Upbit."""
    print("Loading BTC daily data...")
    df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=3000)
    if df is None or df.empty:
        raise ValueError("Failed to load BTC data")

    # Rename columns for consistency
    df.columns = [c.lower() for c in df.columns]
    print(f"Loaded {len(df)} bars from {df.index.min()} to {df.index.max()}")
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate required indicators."""
    df = df.copy()

    # Previous bar values (shift by 1 to avoid look-ahead bias)
    df["prev_high"] = df["high"].shift(1)
    df["prev_low"] = df["low"].shift(1)
    df["prev_close"] = df["close"].shift(1)
    df["prev_range"] = df["prev_high"] - df["prev_low"]

    # Target price = Open + (Prev High - Prev Low) × 0.5
    df["target"] = df["open"] + df["prev_range"] * 0.5

    # MA5 of close (shifted for "previous MA5")
    df["ma5"] = df["close"].shift(1).rolling(window=5).mean()

    # MA20 of close (shifted for "previous MA20")
    df["ma20"] = df["close"].shift(1).rolling(window=20).mean()

    # Previous values for conditions (comparing previous close with previous MA)
    df["prev_ma5"] = df["ma5"].shift(1)
    df["prev_ma20"] = df["ma20"].shift(1)
    df["prev_close_for_condition"] = df["close"].shift(2)  # close 2 bars ago

    return df


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 100_000_000,  # 1억원
    fee_rate: float = 0.0005,  # 0.05%
    slippage_rate: float = 0.0005,  # 0.05%
) -> dict:
    """Run the backtest with exact strategy rules."""

    df = calculate_indicators(df)

    # State variables
    capital = initial_capital
    position = 0.0  # BTC amount
    entry_price = 0.0

    # Track results
    trades: list[dict] = []
    equity_curve: list[float] = []
    daily_returns: list[float] = []

    peak_equity = initial_capital
    max_drawdown = 0.0

    in_position = False

    for i in range(len(df)):
        row = df.iloc[i]
        date = df.index[i]

        # Skip if not enough data for indicators
        if pd.isna(row["ma20"]) or pd.isna(row["prev_ma5"]):
            equity = capital + position * row["close"] if in_position else capital
            equity_curve.append(equity)
            if len(equity_curve) > 1:
                daily_returns.append((equity_curve[-1] / equity_curve[-2]) - 1)
            continue

        # Calculate current equity
        if in_position:
            current_equity = capital + position * row["close"]
        else:
            current_equity = capital

        # --- EXIT CONDITIONS (check first) ---
        if in_position:
            # Sell if ANY condition is true (using previous bar values)
            sell_condition_1 = row["prev_close"] < row["prev_ma5"]  # prev close < prev MA5
            sell_condition_2 = row["prev_close"] < row["prev_ma20"]  # prev close < prev MA20

            if sell_condition_1 or sell_condition_2:
                # Sell at open - slippage
                sell_price = row["open"] * (1 - slippage_rate)
                sell_value = position * sell_price
                fee = sell_value * fee_rate
                capital = capital + sell_value - fee

                # Record trade
                pnl = (sell_price / entry_price - 1) * 100
                trades.append({
                    "date": date,
                    "type": "SELL",
                    "price": sell_price,
                    "amount": position,
                    "value": sell_value,
                    "fee": fee,
                    "pnl_pct": pnl,
                    "reason": "MA5 break" if sell_condition_1 else "MA20 break",
                })

                position = 0.0
                entry_price = 0.0
                in_position = False
                current_equity = capital

        # --- ENTRY CONDITIONS ---
        if not in_position:
            # Buy if ALL conditions are true
            # Condition 1: Daily high >= Target
            breakout_condition = row["high"] >= row["target"]

            # Condition 2: Previous close > Previous MA5
            ma5_condition = row["prev_close"] > row["prev_ma5"]

            # Condition 3: Previous BTC close > Previous BTC MA20 (same as asset for BTC)
            ma20_condition = row["prev_close"] > row["prev_ma20"]

            if breakout_condition and ma5_condition and ma20_condition:
                # Buy at target price + slippage
                buy_price = row["target"] * (1 + slippage_rate)

                # Use all capital
                buy_value = capital
                fee = buy_value * fee_rate
                position = (buy_value - fee) / buy_price
                capital = 0.0
                entry_price = buy_price
                in_position = True

                trades.append({
                    "date": date,
                    "type": "BUY",
                    "price": buy_price,
                    "amount": position,
                    "value": buy_value,
                    "fee": fee,
                    "pnl_pct": 0,
                    "reason": "Breakout",
                })

                current_equity = position * row["close"]

        # Track equity and drawdown
        equity_curve.append(current_equity)
        if len(equity_curve) > 1:
            daily_returns.append((equity_curve[-1] / equity_curve[-2]) - 1)

        if current_equity > peak_equity:
            peak_equity = current_equity

        drawdown = (peak_equity - current_equity) / peak_equity
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Final equity
    final_equity = capital + position * df.iloc[-1]["close"] if in_position else capital

    # Calculate metrics
    total_return = (final_equity / initial_capital - 1) * 100

    # CAGR
    days = (df.index[-1] - df.index[0]).days
    years = days / 365.25
    cagr = ((final_equity / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

    # Win rate
    completed_trades = [t for t in trades if t["type"] == "SELL"]
    winning_trades = [t for t in completed_trades if t["pnl_pct"] > 0]
    win_rate = len(winning_trades) / len(completed_trades) * 100 if completed_trades else 0

    # Average profit/loss
    avg_profit = np.mean([t["pnl_pct"] for t in winning_trades]) if winning_trades else 0
    losing_trades = [t for t in completed_trades if t["pnl_pct"] <= 0]
    avg_loss = np.mean([t["pnl_pct"] for t in losing_trades]) if losing_trades else 0

    # Profit factor
    gross_profit = sum(t["pnl_pct"] for t in winning_trades) if winning_trades else 0
    gross_loss = abs(sum(t["pnl_pct"] for t in losing_trades)) if losing_trades else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    # Sharpe ratio (annualized)
    if daily_returns:
        returns_arr = np.array(daily_returns)
        sharpe = np.sqrt(365) * np.mean(returns_arr) / np.std(returns_arr) if np.std(returns_arr) > 0 else 0
    else:
        sharpe = 0

    # Sortino ratio
    if daily_returns:
        downside_returns = returns_arr[returns_arr < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1
        sortino = np.sqrt(365) * np.mean(returns_arr) / downside_std if downside_std > 0 else 0
    else:
        sortino = 0

    # Calmar ratio
    calmar = cagr / (max_drawdown * 100) if max_drawdown > 0 else 0

    return {
        "initial_capital": initial_capital,
        "final_equity": final_equity,
        "total_return": total_return,
        "cagr": cagr,
        "mdd": max_drawdown * 100,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "total_trades": len(completed_trades),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": win_rate,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "trades": trades,
        "equity_curve": equity_curve,
        "start_date": df.index[0],
        "end_date": df.index[-1],
        "days": days,
        "years": years,
    }


def print_results(results: dict) -> None:
    """Print backtest results."""
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS: BTC Market Filter Strategy")
    print("=" * 60)

    print(f"\n[Period]")
    print(f"  Start Date:     {results['start_date'].strftime('%Y-%m-%d')}")
    print(f"  End Date:       {results['end_date'].strftime('%Y-%m-%d')}")
    print(f"  Total Days:     {results['days']:,}")
    print(f"  Years:          {results['years']:.2f}")

    print(f"\n[Capital]")
    print(f"  Initial:        {results['initial_capital']:,.0f} KRW")
    print(f"  Final:          {results['final_equity']:,.0f} KRW")

    print(f"\n[Returns]")
    print(f"  Total Return:   {results['total_return']:.2f}%")
    print(f"  CAGR:           {results['cagr']:.2f}%")

    print(f"\n[Risk]")
    print(f"  Max Drawdown:   {results['mdd']:.2f}%")

    print(f"\n[Risk-Adjusted Returns]")
    print(f"  Sharpe Ratio:   {results['sharpe']:.2f}")
    print(f"  Sortino Ratio:  {results['sortino']:.2f}")
    print(f"  Calmar Ratio:   {results['calmar']:.2f}")

    print(f"\n[Trade Statistics]")
    print(f"  Total Trades:   {results['total_trades']}")
    print(f"  Winning:        {results['winning_trades']}")
    print(f"  Losing:         {results['losing_trades']}")
    print(f"  Win Rate:       {results['win_rate']:.2f}%")
    print(f"  Profit Factor:  {results['profit_factor']:.2f}")

    print(f"\n[Per-Trade]")
    print(f"  Avg Profit:     {results['avg_profit']:.2f}%")
    print(f"  Avg Loss:       {results['avg_loss']:.2f}%")

    print("\n" + "=" * 60)

    # Print recent trades
    print("\n[Recent Trades (last 10)]")
    print("-" * 80)
    print(f"{'Date':<12} {'Type':<6} {'Price':>14} {'PnL %':>10} {'Reason':<15}")
    print("-" * 80)
    for trade in results["trades"][-10:]:
        pnl_str = f"{trade['pnl_pct']:.2f}%" if trade["type"] == "SELL" else "-"
        print(
            f"{trade['date'].strftime('%Y-%m-%d'):<12} "
            f"{trade['type']:<6} "
            f"{trade['price']:>14,.0f} "
            f"{pnl_str:>10} "
            f"{trade['reason']:<15}"
        )


def compare_with_buy_and_hold(df: pd.DataFrame, strategy_results: dict) -> None:
    """Compare strategy with buy and hold."""
    print("\n" + "=" * 60)
    print("COMPARISON: Strategy vs Buy & Hold")
    print("=" * 60)

    # Buy and hold calculation
    initial_price = df.iloc[0]["close"]
    final_price = df.iloc[-1]["close"]
    bh_return = (final_price / initial_price - 1) * 100

    days = (df.index[-1] - df.index[0]).days
    years = days / 365.25
    bh_cagr = ((final_price / initial_price) ** (1 / years) - 1) * 100

    # Calculate buy & hold MDD
    cummax = df["close"].cummax()
    drawdown = (cummax - df["close"]) / cummax
    bh_mdd = drawdown.max() * 100

    print(f"\n{'Metric':<20} {'Strategy':>15} {'Buy & Hold':>15} {'Diff':>15}")
    print("-" * 65)
    print(f"{'Total Return':<20} {strategy_results['total_return']:>14.2f}% {bh_return:>14.2f}% {strategy_results['total_return'] - bh_return:>14.2f}%")
    print(f"{'CAGR':<20} {strategy_results['cagr']:>14.2f}% {bh_cagr:>14.2f}% {strategy_results['cagr'] - bh_cagr:>14.2f}%")
    print(f"{'Max Drawdown':<20} {strategy_results['mdd']:>14.2f}% {bh_mdd:>14.2f}% {strategy_results['mdd'] - bh_mdd:>14.2f}%")
    print(f"{'Sharpe Ratio':<20} {strategy_results['sharpe']:>15.2f} {'N/A':>15}")
    print(f"{'Calmar Ratio':<20} {strategy_results['calmar']:>15.2f} {bh_cagr/bh_mdd:>15.2f}")


if __name__ == "__main__":
    # Load data
    df = load_btc_data()

    # Run backtest
    results = run_backtest(
        df,
        initial_capital=100_000_000,  # 1억원
        fee_rate=0.0005,  # 0.05%
        slippage_rate=0.0005,  # 0.05%
    )

    # Print results
    print_results(results)

    # Compare with buy and hold
    compare_with_buy_and_hold(df, results)
