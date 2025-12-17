"""
Production-Grade Trading Environment v2

Features:
- Technical indicators (RSI, SMA, EMA, MACD, Bollinger Bands)
- Volatility metrics
- Better reward shaping for directional prediction
- Optimized for next-day prediction (your options strategy)
"""
import numpy as np


class TradingEnvV2:
    """
    Enhanced trading environment with technical indicators.
    Optimized for predicting next-day direction (UP/DOWN).
    """

    def __init__(self, symbol="AAPL", window_size=20):
        self.symbol = symbol
        self.window_size = window_size

        # State: technical indicators + price features
        # [normalized_prices(10), rsi, sma_ratio, ema_ratio, macd, volatility,
        #  momentum_5d, momentum_10d, position, profit]
        self.state_size = 10 + 8 + 2  # 20 features total

        self.action_space_n = 3  # 0=HOLD, 1=BUY (predict UP), 2=SELL (predict DOWN)

        self.data = None
        self.volumes = None
        self.current_step = 0
        self.position = 0
        self.entry_price = 0
        self.total_profit = 0

    def load_data(self, prices, volumes=None):
        """Load price data and optional volume data"""
        self.data = np.array(prices, dtype=np.float32)
        self.volumes = np.array(volumes, dtype=np.float32) if volumes is not None else None

    def reset(self):
        """Reset environment to start"""
        self.current_step = self.window_size
        self.position = 0
        self.entry_price = 0
        self.total_profit = 0
        return self._get_state()

    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_sma(self, prices, period):
        """Simple Moving Average"""
        if len(prices) < period:
            return prices[-1]
        return np.mean(prices[-period:])

    def _calculate_ema(self, prices, period):
        """Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1]

        multiplier = 2 / (period + 1)
        ema = prices[-period]

        for price in prices[-period+1:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def _calculate_macd(self, prices):
        """MACD (12, 26, 9)"""
        if len(prices) < 26:
            return 0.0

        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        macd_line = ema12 - ema26

        # Normalize by current price
        return macd_line / prices[-1] * 100

    def _calculate_bollinger_position(self, prices, period=20):
        """Position within Bollinger Bands (-1 to 1)"""
        if len(prices) < period:
            return 0.0

        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])

        if std == 0:
            return 0.0

        upper = sma + 2 * std
        lower = sma - 2 * std

        current = prices[-1]

        # Normalize to -1 to 1 range
        if current > upper:
            return 1.0
        elif current < lower:
            return -1.0
        else:
            return (current - sma) / (2 * std)

    def _get_state(self):
        """
        Build state with technical indicators.

        Features (20 total):
        - Normalized price window (10)
        - RSI normalized to 0-1 (1)
        - SMA ratio (price/SMA20) (1)
        - EMA ratio (price/EMA12) (1)
        - MACD (1)
        - Volatility (20-day std / price) (1)
        - 5-day momentum (1)
        - 10-day momentum (1)
        - Bollinger position (1)
        - Position (1)
        - Profit (1)
        """
        # Get price history
        start_idx = max(0, self.current_step - self.window_size)
        prices = self.data[start_idx:self.current_step]
        current_price = self.data[self.current_step - 1]

        # Pad if needed
        if len(prices) < self.window_size:
            prices = np.pad(prices, (self.window_size - len(prices), 0), mode='edge')

        # 1. Normalized price window (last 10 prices)
        recent_prices = prices[-10:]
        normalized_prices = (recent_prices - recent_prices[0]) / (recent_prices[0] + 1e-8)

        # 2. RSI (0-1)
        rsi = self._calculate_rsi(prices) / 100.0

        # 3. SMA ratio
        sma20 = self._calculate_sma(prices, 20)
        sma_ratio = (current_price / sma20) - 1.0 if sma20 > 0 else 0.0

        # 4. EMA ratio
        ema12 = self._calculate_ema(prices, 12)
        ema_ratio = (current_price / ema12) - 1.0 if ema12 > 0 else 0.0

        # 5. MACD
        macd = self._calculate_macd(prices) / 10.0  # Scale down

        # 6. Volatility (normalized)
        volatility = np.std(prices[-20:]) / current_price if len(prices) >= 20 else 0.0

        # 7. 5-day momentum
        if len(prices) >= 5:
            momentum_5d = (current_price / prices[-5]) - 1.0
        else:
            momentum_5d = 0.0

        # 8. 10-day momentum
        if len(prices) >= 10:
            momentum_10d = (current_price / prices[-10]) - 1.0
        else:
            momentum_10d = 0.0

        # 9. Bollinger position
        bb_position = self._calculate_bollinger_position(prices)

        # 10. Position and profit
        position_normalized = self.position  # 0 or 1
        profit_normalized = self.total_profit / 1000.0  # Scale

        # Combine all features
        state = np.concatenate([
            normalized_prices,           # 10 features
            [rsi],                       # 1
            [sma_ratio],                 # 1
            [ema_ratio],                 # 1
            [macd],                      # 1
            [volatility],                # 1
            [momentum_5d],               # 1
            [momentum_10d],              # 1
            [bb_position],               # 1
            [position_normalized],       # 1
            [profit_normalized]          # 1
        ])

        return state.astype(np.float32)

    def step(self, action):
        """
        Execute action and return next state.

        Reward shaping optimized for directional prediction:
        - Reward for correct direction prediction
        - Penalty for wrong direction
        - Small penalty for holding when there's a clear trend
        """
        current_price = self.data[self.current_step - 1]

        # Move to next day
        self.current_step += 1
        done = self.current_step >= len(self.data)

        if done:
            next_price = current_price
        else:
            next_price = self.data[self.current_step - 1]

        # Calculate actual price change
        price_change = (next_price - current_price) / current_price
        actual_direction = 1 if price_change > 0 else -1

        reward = 0

        # Action: 0=HOLD, 1=BUY (predict UP), 2=SELL (predict DOWN)
        if action == 1:  # BUY - predicting UP
            if self.position == 0:
                self.position = 1
                self.entry_price = current_price

            # Reward based on actual direction
            if actual_direction == 1:
                reward = abs(price_change) * 100  # Correct prediction
            else:
                reward = -abs(price_change) * 100  # Wrong prediction

        elif action == 2:  # SELL - predicting DOWN
            if self.position == 1:
                profit = next_price - self.entry_price
                self.total_profit += profit
                self.position = 0
                self.entry_price = 0

            # Reward based on actual direction
            if actual_direction == -1:
                reward = abs(price_change) * 100  # Correct prediction
            else:
                reward = -abs(price_change) * 100  # Wrong prediction

        else:  # HOLD
            # Small penalty for holding during strong trends
            if abs(price_change) > 0.01:  # More than 1% move
                reward = -abs(price_change) * 20  # Missed opportunity
            else:
                reward = 0.1  # Small reward for correct hold during sideways

        # Bonus for position profit
        if self.position == 1:
            unrealized = (next_price - self.entry_price) / self.entry_price
            reward += unrealized * 10

        next_state = self._get_state() if not done else np.zeros(self.state_size)

        info = {
            "price": next_price,
            "position": self.position,
            "total_profit": self.total_profit,
            "price_change": price_change,
            "action": action
        }

        return next_state, reward, done, info


class TradingEnvV3(TradingEnvV2):
    """
    Enhanced environment with market context (VIX, SPY, Volume).

    Additional features:
    - VIX (market fear gauge)
    - SPY trend (market regime)
    - Volume ratio (current vs average)
    - ATR (Average True Range)
    - Stochastic oscillator
    - Price vs 50-day SMA
    """

    def __init__(self, symbol="AAPL", window_size=20):
        super().__init__(symbol, window_size)

        # Extended state size: base 20 + 7 new features = 27
        self.state_size = 27

        # Market context data
        self.vix_data = None
        self.spy_data = None
        self.volume_data = None

    def load_data(self, prices, volumes=None, vix=None, spy=None):
        """Load price data with market context"""
        super().load_data(prices, volumes)
        self.volume_data = np.array(volumes, dtype=np.float32) if volumes is not None else None
        self.vix_data = np.array(vix, dtype=np.float32) if vix is not None else None
        self.spy_data = np.array(spy, dtype=np.float32) if spy is not None else None

    def _calculate_atr(self, prices, period=14):
        """Average True Range - volatility indicator"""
        if len(prices) < period + 1:
            return 0.0

        # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
        # Simplified using close prices only
        tr = np.abs(np.diff(prices[-period-1:]))
        atr = np.mean(tr)
        return atr / prices[-1]  # Normalize by current price

    def _calculate_stochastic(self, prices, period=14):
        """Stochastic oscillator %K"""
        if len(prices) < period:
            return 50.0

        recent = prices[-period:]
        lowest = np.min(recent)
        highest = np.max(recent)

        if highest == lowest:
            return 50.0

        k = ((prices[-1] - lowest) / (highest - lowest)) * 100
        return k

    def _get_state(self):
        """Build extended state with market context"""
        # Get base state from V2
        base_state = super()._get_state()

        # Get price history
        start_idx = max(0, self.current_step - self.window_size)
        prices = self.data[start_idx:self.current_step]
        current_price = self.data[self.current_step - 1]

        # Pad if needed
        if len(prices) < self.window_size:
            prices = np.pad(prices, (self.window_size - len(prices), 0), mode='edge')

        # New feature 1: VIX level (normalized 0-1, typical range 10-40)
        if self.vix_data is not None and self.current_step < len(self.vix_data):
            vix = self.vix_data[self.current_step - 1]
            vix_normalized = np.clip((vix - 10) / 30, 0, 1)  # Normalize 10-40 range
        else:
            vix_normalized = 0.5  # Neutral

        # New feature 2: VIX change (is fear increasing?)
        if self.vix_data is not None and self.current_step >= 2 and self.current_step < len(self.vix_data):
            vix_prev = self.vix_data[self.current_step - 2]
            vix_curr = self.vix_data[self.current_step - 1]
            vix_change = (vix_curr - vix_prev) / (vix_prev + 1e-8)
        else:
            vix_change = 0.0

        # New feature 3: SPY trend (market direction)
        if self.spy_data is not None and self.current_step >= 10 and self.current_step < len(self.spy_data):
            spy_recent = self.spy_data[self.current_step-10:self.current_step]
            spy_trend = (spy_recent[-1] / spy_recent[0]) - 1.0  # 10-day market momentum
        else:
            spy_trend = 0.0

        # New feature 4: Volume ratio (current vs 20-day average)
        if self.volume_data is not None and self.current_step >= 20 and self.current_step < len(self.volume_data):
            vol_avg = np.mean(self.volume_data[self.current_step-20:self.current_step])
            vol_current = self.volume_data[self.current_step - 1]
            volume_ratio = (vol_current / (vol_avg + 1e-8)) - 1.0  # > 0 = above average
        else:
            volume_ratio = 0.0

        # New feature 5: ATR (volatility)
        atr = self._calculate_atr(prices)

        # New feature 6: Stochastic oscillator (0-100 -> 0-1)
        stochastic = self._calculate_stochastic(prices) / 100.0

        # New feature 7: Price vs 50-day SMA (longer trend)
        if len(self.data) >= 50 and self.current_step >= 50:
            sma50_start = max(0, self.current_step - 50)
            sma50 = np.mean(self.data[sma50_start:self.current_step])
            price_vs_sma50 = (current_price / sma50) - 1.0
        else:
            price_vs_sma50 = 0.0

        # Combine base state with new features
        extended_state = np.concatenate([
            base_state,                # 20 features
            [vix_normalized],          # 1 - VIX level
            [vix_change],              # 1 - VIX momentum
            [spy_trend],               # 1 - Market trend
            [volume_ratio],            # 1 - Volume spike
            [atr],                     # 1 - Volatility
            [stochastic],              # 1 - Stochastic
            [price_vs_sma50]           # 1 - Longer trend
        ])

        return extended_state.astype(np.float32)


# Test the environment
if __name__ == "__main__":
    import yfinance as yf

    # Download test data
    ticker = yf.Ticker("AAPL")
    df = ticker.history(period="1y")
    prices = df['Close'].values
    volumes = df['Volume'].values

    # Download VIX and SPY
    vix = yf.Ticker("^VIX").history(period="1y")['Close'].values
    spy = yf.Ticker("SPY").history(period="1y")['Close'].values

    # Test V2 environment
    print("Testing V2 (base):")
    env_v2 = TradingEnvV2(symbol="AAPL", window_size=20)
    env_v2.load_data(prices)
    state_v2 = env_v2.reset()
    print(f"  State shape: {state_v2.shape}")

    # Test V3 environment
    print("\nTesting V3 (enhanced):")
    env_v3 = TradingEnvV3(symbol="AAPL", window_size=20)
    env_v3.load_data(prices, volumes=volumes, vix=vix, spy=spy)
    state_v3 = env_v3.reset()
    print(f"  State shape: {state_v3.shape}")
    print(f"  New features: VIX={state_v3[20]:.2f}, VIX_chg={state_v3[21]:.2f}, "
          f"SPY={state_v3[22]:.2f}, Vol={state_v3[23]:.2f}")

    # Test step
    next_state, reward, done, info = env_v3.step(1)  # BUY
    print(f"\nAfter BUY:")
    print(f"  Reward: {reward:.4f}")
    print(f"  Info: {info}")
