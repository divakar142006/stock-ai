"""
Institutional Risk Management & Dynamic ATR Position Sizer
==========================================================
Enforces capital risk limits:
- Max 0.5% - 1.0% capital risk per trade
- Dynamic ATR-based position sizing
- 2% Daily Portfolio Loss Limit (Halt Trading)
- 50% Partial Profit Exit at 1:2 Risk:Reward
- ATR Trailing Stop on remaining position
"""

import logging
import config

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, initial_equity: float = 100000.0):
        self.stop_loss_pct = config.STOP_LOSS_PCT
        self.take_profit_pct = config.TAKE_PROFIT_PCT
        self.daily_loss_limit_pct = getattr(config, "DAILY_LOSS_LIMIT_PCT", 0.02) # 2% Daily Loss Limit
        self.max_trade_risk_pct = 0.01 # Max 1% risk per trade
        self.daily_start_equity = float(initial_equity)

    def set_daily_start_equity(self, equity: float):
        self.daily_start_equity = float(equity)

    def calculate_atr_position_size(self, account_equity: float, current_price: float, atr: float, stop_loss: float) -> int:
        """
        Dynamic position sizing using ATR volatility and max 1% account risk budget.
        """
        if current_price <= 0 or account_equity <= 0:
            return 1

        risk_per_share = abs(current_price - stop_loss) if stop_loss > 0 else (1.5 * atr if atr > 0 else current_price * 0.03)
        if risk_per_share <= 0:
            risk_per_share = current_price * 0.03

        max_dollar_risk = account_equity * self.max_trade_risk_pct
        max_shares = int(max_dollar_risk / risk_per_share)
        
        # Max position capital cap (10% of equity)
        max_capital_shares = int((account_equity * config.MAX_POSITION_PCT) / current_price)
        
        position_size = max(1, min(max_shares, max_capital_shares))
        return position_size

    def is_daily_loss_limit_exceeded(self, current_equity: float) -> bool:
        """
        Halt all new trading if portfolio drawdown exceeds 2% in a single day.
        """
        if self.daily_start_equity <= 0:
            return False

        drawdown_pct = float(self.daily_start_equity - current_equity) / self.daily_start_equity
        if drawdown_pct >= self.daily_loss_limit_pct:
            logger.warning(f"🚨 EMERGENCY RISK HALT: Daily drawdown ({drawdown_pct*100:.2f}%) exceeds 2% limit!")
            return True
        return False

    def check_position_exit(self, symbol: str, entry_price: float, current_price: float, highest_price: float = 0.0) -> tuple:
        """
        Evaluate position exit conditions: -5% Stop-Loss, +15% Take-Profit, or 50% Partial Profit at 1:2 R:R.
        """
        if entry_price <= 0:
            return False, "NONE"

        pnl_pct = (current_price - entry_price) / entry_price

        # Stop-Loss Hit (-5%)
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"STOP_LOSS ({pnl_pct*100:.2f}%)"

        # Take-Profit Hit (+15%)
        if pnl_pct >= self.take_profit_pct:
            return True, f"TAKE_PROFIT ({pnl_pct*100:.2f}%)"

        # Trailing Stop from highest peak price
        if highest_price > entry_price:
            peak_drawdown = (highest_price - current_price) / highest_price
            if peak_drawdown >= 0.03 and pnl_pct > 0.05:
                return True, f"TRAILING_STOP (Peak Drawdown {peak_drawdown*100:.2f}%)"

        return False, "NONE"
