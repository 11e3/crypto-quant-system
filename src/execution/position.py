"""
Position model for tracking trading positions.
"""

__all__ = ["Position"]


class Position:
    """Represents a single trading position."""

    def __init__(
        self,
        ticker: str,
        entry_price: float,
        amount: float,
        entry_date: str | None = None,
    ) -> None:
        """
        Initialize position.

        Args:
            ticker: Trading pair symbol
            entry_price: Entry price
            amount: Position size (in base currency)
            entry_date: Entry date (optional)
        """
        self.ticker = ticker
        self.entry_price = entry_price
        self.amount = amount
        self.entry_date = entry_date

    @property
    def value(self) -> float:
        """Calculate position value (entry_price * amount)."""
        return self.entry_price * self.amount

    def __repr__(self) -> str:
        return f"Position({self.ticker}, entry={self.entry_price:.0f}, amount={self.amount:.6f})"
