"""
Trading AI - Next-Day Direction Predictor

Predicts whether a stock will go UP or DOWN tomorrow.
Optimized for options/futures trading strategies.

Features:
- Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands)
- Deeper neural network (3 layers, 256 units)
- Directional accuracy tracking
- End-of-day signal generation
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import yfinance as yf
from trading_env import TradingEnvV2, TradingEnvV3
import os
import pandas as pd
from datetime import datetime, timedelta

# Directories
DATA_DIR = "data"
MODELS_DIR = "models"


# ============== Neural Network (Anti-Overfit) ==============
class ActorCriticV2(nn.Module):
    """
    Smaller, regularized network to prevent overfitting.
    2 hidden layers with 64 units - much smaller for limited data.
    """

    def __init__(self, state_size, action_size, hidden_size=64):
        super().__init__()

        # Smaller shared feature extractor (2 layers)
        self.shared = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),  # Higher dropout

            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
        )

        # Actor head (policy) - simpler
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, action_size)
        )

        # Critic head (value) - simpler
        self.critic = nn.Sequential(
            nn.Linear(hidden_size, 1)
        )

    def forward(self, x):
        shared = self.shared(x)
        action_probs = torch.softmax(self.actor(shared), dim=-1)
        value = self.critic(shared)
        return action_probs, value


# ============== PPO Agent ==============
class PPOAgentV2:
    def __init__(self, state_size, action_size, lr=0.0003, gamma=0.99,
                 epsilon=0.2, epochs=5, gae_lambda=0.95):
        self.gamma = gamma
        self.epsilon = epsilon
        self.epochs = epochs  # Fewer epochs per update to prevent overfitting
        self.gae_lambda = gae_lambda

        self.network = ActorCriticV2(state_size, action_size)
        # Add weight decay (L2 regularization)
        self.optimizer = optim.Adam(self.network.parameters(), lr=lr, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=500, gamma=0.9)

        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []

        # Track directional accuracy
        self.correct_predictions = 0
        self.total_predictions = 0

    def select_action(self, state, deterministic=False):
        state = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            action_probs, value = self.network(state)

        if deterministic:
            action = torch.argmax(action_probs, dim=-1)
            log_prob = torch.log(action_probs[0, action])
        else:
            dist = torch.distributions.Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)

        return action.item(), log_prob.item(), value.item()

    def store(self, state, action, reward, log_prob, value, done):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)

    def compute_gae(self, next_value):
        rewards = self.rewards
        values = self.values + [next_value]
        dones = self.dones

        advantages = []
        gae = 0

        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t+1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)

        returns = [adv + val for adv, val in zip(advantages, values[:-1])]
        return advantages, returns

    def update(self, next_value):
        advantages, returns = self.compute_gae(next_value)

        states = torch.FloatTensor(np.array(self.states))
        actions = torch.LongTensor(self.actions)
        old_log_probs = torch.FloatTensor(self.log_probs)
        advantages = torch.FloatTensor(advantages)
        returns = torch.FloatTensor(returns)

        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        for _ in range(self.epochs):
            action_probs, values = self.network(states)
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages

            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(values.squeeze(), returns)
            loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network.parameters(), 0.5)
            self.optimizer.step()

        self.scheduler.step()

        self.states, self.actions, self.rewards = [], [], []
        self.log_probs, self.values, self.dones = [], [], []

    def save(self, path):
        torch.save({
            'model_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, path)
        print(f"Model saved to {path}")

    def load(self, path):
        if os.path.exists(path):
            checkpoint = torch.load(path, weights_only=True)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.network.load_state_dict(checkpoint['model_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            else:
                # Legacy format
                self.network.load_state_dict(checkpoint)
            print(f"Model loaded from {path}")
            return True
        return False


# ============== Data Functions ==============
def get_mega_caps():
    """Mega cap stocks only"""
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]


def get_model_path(symbol):
    """Get model path for a symbol"""
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    return os.path.join(MODELS_DIR, f"{symbol}.pth")


def get_stock_data(symbol, period="2y", force_download=False):
    """Get stock data with caching"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    cache_file = os.path.join(DATA_DIR, f"{symbol}_prices.csv")

    use_cache = False
    if os.path.exists(cache_file) and not force_download:
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        age = datetime.now() - file_time

        if age < timedelta(days=1):
            use_cache = True
            print(f"Using cached {symbol} data")

    if use_cache:
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    else:
        print(f"Downloading {symbol} data...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        df.to_csv(cache_file)
        print(f"Saved to {cache_file}")

    return df['Close'].values


def get_full_stock_data(symbol, period="5y"):
    """Get stock data with volume, VIX, and SPY for V3 training"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Get stock data
    print(f"Downloading {symbol} full data...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)
    prices = df['Close'].values
    volumes = df['Volume'].values

    # Get VIX
    print("Downloading VIX...")
    vix_df = yf.Ticker("^VIX").history(period=period)
    vix = vix_df['Close'].values

    # Get SPY
    print("Downloading SPY...")
    spy_df = yf.Ticker("SPY").history(period=period)
    spy = spy_df['Close'].values

    # Align lengths (VIX/SPY may have slightly different dates)
    min_len = min(len(prices), len(vix), len(spy), len(volumes))
    prices = prices[-min_len:]
    volumes = volumes[-min_len:]
    vix = vix[-min_len:]
    spy = spy[-min_len:]

    print(f"Data aligned: {min_len} days")
    return prices, volumes, vix, spy


# ============== Training ==============
def evaluate_on_validation(agent, val_prices, window_size=20, symbol="AAPL"):
    """Evaluate model on validation set - returns accuracy"""
    val_env = TradingEnvV2(symbol=symbol, window_size=window_size)
    val_env.load_data(val_prices)

    state = val_env.reset()
    done = False
    correct = 0
    total = 0

    agent.network.eval()  # Eval mode (disables dropout)
    while not done:
        action, _, _ = agent.select_action(state, deterministic=True)
        next_state, reward, done, info = val_env.step(action)

        if action in [1, 2]:
            total += 1
            actual_up = info['price_change'] > 0
            predicted_up = action == 1
            if predicted_up == actual_up:
                correct += 1
        state = next_state
    agent.network.train()  # Back to train mode

    return (correct / total * 100) if total > 0 else 0


def train(symbol="AAPL", episodes=2000, window_size=20):
    """
    Anti-overfit training with validation-based model selection.
    """
    # Get data - 5 years for more training samples
    prices = get_stock_data(symbol, period="5y")

    # Split 70/15/15 - train/val/test
    n = len(prices)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train_prices = prices[:train_end]
    val_prices = prices[train_end:val_end]
    test_prices = prices[val_end:]

    print(f"\n{'='*60}")
    print(f"  TRAINING: {symbol} (Anti-Overfit Mode)")
    print(f"  Train: {len(train_prices)} days | Val: {len(val_prices)} days | Test: {len(test_prices)} days")
    print(f"  Episodes: {episodes}")
    print(f"{'='*60}\n")

    # Create environment and agent (fresh start - no loading old overfit model)
    env = TradingEnvV2(symbol=symbol, window_size=window_size)
    env.load_data(train_prices)

    agent = PPOAgentV2(env.state_size, env.action_space_n)
    model_path = get_model_path(symbol)

    best_val_accuracy = 0
    no_improve_count = 0
    early_stop_patience = 300  # Stop if no improvement for 300 episodes

    for episode in range(episodes):
        state = env.reset()
        done = False
        correct = 0
        total = 0

        while not done:
            action, log_prob, value = agent.select_action(state)
            next_state, reward, done, info = env.step(action)
            agent.store(state, action, reward, log_prob, value, done)

            if action in [1, 2]:
                total += 1
                if (action == 1 and info['price_change'] > 0) or \
                   (action == 2 and info['price_change'] < 0):
                    correct += 1

            state = next_state

        # Update agent
        with torch.no_grad():
            _, next_value = agent.network(torch.FloatTensor(state).unsqueeze(0))
        agent.update(next_value.item())

        train_accuracy = (correct / total * 100) if total > 0 else 0

        # Validate every 50 episodes - SAVE BASED ON VALIDATION, NOT TRAINING
        if episode % 50 == 0:
            val_accuracy = evaluate_on_validation(agent, val_prices, window_size, symbol)

            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                agent.save(model_path)
                no_improve_count = 0
            else:
                no_improve_count += 50

            print(f"Ep {episode:4d} | Train Acc: {train_accuracy:5.1f}% | "
                  f"Val Acc: {val_accuracy:5.1f}% | Best Val: {best_val_accuracy:5.1f}%")

            # Early stopping
            if no_improve_count >= early_stop_patience:
                print(f"\nEarly stopping at episode {episode} (no improvement for {early_stop_patience} episodes)")
                break

    # Final test
    print(f"\n{'='*60}")
    print("  TESTING ON UNSEEN DATA")
    print(f"{'='*60}")

    test_env = TradingEnvV2(symbol=symbol, window_size=window_size)
    test_env.load_data(test_prices)

    agent.load(model_path)
    agent.network.eval()  # Eval mode for testing

    state = test_env.reset()
    done = False
    correct = 0
    total = 0
    predictions = []

    while not done:
        action, _, _ = agent.select_action(state, deterministic=True)
        next_state, reward, done, info = test_env.step(action)

        if action in [1, 2]:
            total += 1
            actual_up = info['price_change'] > 0
            predicted_up = action == 1

            if predicted_up == actual_up:
                correct += 1

            predictions.append({
                'predicted': 'UP' if predicted_up else 'DOWN',
                'actual': 'UP' if actual_up else 'DOWN',
                'correct': predicted_up == actual_up,
                'change': info['price_change'] * 100
            })

        state = next_state

    test_accuracy = (correct / total * 100) if total > 0 else 0

    print(f"\n  Test Results:")
    print(f"  - Total Profit: ${info['total_profit']:.2f}")
    print(f"  - Directional Accuracy: {test_accuracy:.1f}% ({correct}/{total})")
    print(f"  - Predictions made: {total}")

    # Show last 10 predictions
    print(f"\n  Last 10 predictions:")
    for p in predictions[-10:]:
        status = "OK" if p['correct'] else "X"
        print(f"    [{status}] Predicted: {p['predicted']:4s} | Actual: {p['actual']:4s} | Change: {p['change']:+.2f}%")

    return agent, test_accuracy


def train_all():
    """Train all mega caps"""
    results = {}

    for symbol in get_mega_caps():
        try:
            agent, accuracy = train(symbol=symbol, episodes=2000)
            results[symbol] = {"accuracy": accuracy, "status": "SUCCESS"}
        except Exception as e:
            print(f"Failed {symbol}: {e}")
            results[symbol] = {"status": "FAILED", "error": str(e)}

    print("\n" + "="*60)
    print("  TRAINING SUMMARY")
    print("="*60)
    for symbol, data in results.items():
        if data["status"] == "SUCCESS":
            print(f"  {symbol}: Directional Accuracy {data['accuracy']:.1f}%")
        else:
            print(f"  {symbol}: FAILED")

    return results


# ============== Enhanced Training with VIX/SPY ==============
def evaluate_on_validation_v3(agent, val_prices, val_volumes, val_vix, val_spy, window_size=20, symbol="AAPL"):
    """Evaluate V3 model on validation set"""
    val_env = TradingEnvV3(symbol=symbol, window_size=window_size)
    val_env.load_data(val_prices, volumes=val_volumes, vix=val_vix, spy=val_spy)

    state = val_env.reset()
    done = False
    correct = 0
    total = 0

    agent.network.eval()
    while not done:
        action, _, _ = agent.select_action(state, deterministic=True)
        next_state, reward, done, info = val_env.step(action)

        if action in [1, 2]:
            total += 1
            actual_up = info['price_change'] > 0
            predicted_up = action == 1
            if predicted_up == actual_up:
                correct += 1
        state = next_state
    agent.network.train()

    return (correct / total * 100) if total > 0 else 0


def train_v3(symbol="AAPL", episodes=2000, window_size=20):
    """
    Enhanced training with VIX, SPY, and volume data.
    Uses TradingEnvV3 with 27 features (7 more than V2).
    """
    # Get full data with VIX and SPY
    prices, volumes, vix, spy = get_full_stock_data(symbol, period="5y")

    # Split 70/15/15 - train/val/test
    n = len(prices)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train_prices = prices[:train_end]
    train_volumes = volumes[:train_end]
    train_vix = vix[:train_end]
    train_spy = spy[:train_end]

    val_prices = prices[train_end:val_end]
    val_volumes = volumes[train_end:val_end]
    val_vix = vix[train_end:val_end]
    val_spy = spy[train_end:val_end]

    test_prices = prices[val_end:]
    test_volumes = volumes[val_end:]
    test_vix = vix[val_end:]
    test_spy = spy[val_end:]

    print(f"\n{'='*60}")
    print(f"  TRAINING V3: {symbol} (Enhanced with VIX/SPY)")
    print(f"  Features: 27 (base 20 + VIX + SPY + Volume + ATR + Stoch + SMA50)")
    print(f"  Train: {len(train_prices)} days | Val: {len(val_prices)} days | Test: {len(test_prices)} days")
    print(f"  Episodes: {episodes}")
    print(f"{'='*60}\n")

    # Create V3 environment and agent
    env = TradingEnvV3(symbol=symbol, window_size=window_size)
    env.load_data(train_prices, volumes=train_volumes, vix=train_vix, spy=train_spy)

    agent = PPOAgentV2(env.state_size, env.action_space_n)  # 27 features now
    model_path = get_model_path(f"{symbol}_v3")  # Save as separate model

    best_val_accuracy = 0
    no_improve_count = 0
    early_stop_patience = 300

    for episode in range(episodes):
        state = env.reset()
        done = False
        correct = 0
        total = 0

        while not done:
            action, log_prob, value = agent.select_action(state)
            next_state, reward, done, info = env.step(action)
            agent.store(state, action, reward, log_prob, value, done)

            if action in [1, 2]:
                total += 1
                if (action == 1 and info['price_change'] > 0) or \
                   (action == 2 and info['price_change'] < 0):
                    correct += 1

            state = next_state

        # Update agent
        with torch.no_grad():
            _, next_value = agent.network(torch.FloatTensor(state).unsqueeze(0))
        agent.update(next_value.item())

        train_accuracy = (correct / total * 100) if total > 0 else 0

        # Validate every 50 episodes
        if episode % 50 == 0:
            val_accuracy = evaluate_on_validation_v3(
                agent, val_prices, val_volumes, val_vix, val_spy, window_size, symbol
            )

            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                agent.save(model_path)
                no_improve_count = 0
            else:
                no_improve_count += 50

            print(f"Ep {episode:4d} | Train Acc: {train_accuracy:5.1f}% | "
                  f"Val Acc: {val_accuracy:5.1f}% | Best Val: {best_val_accuracy:5.1f}%")

            # Early stopping
            if no_improve_count >= early_stop_patience:
                print(f"\nEarly stopping at episode {episode} (no improvement for {early_stop_patience} episodes)")
                break

    # Final test
    print(f"\n{'='*60}")
    print("  TESTING V3 ON UNSEEN DATA")
    print(f"{'='*60}")

    test_env = TradingEnvV3(symbol=symbol, window_size=window_size)
    test_env.load_data(test_prices, volumes=test_volumes, vix=test_vix, spy=test_spy)

    agent.load(model_path)
    agent.network.eval()

    state = test_env.reset()
    done = False
    correct = 0
    total = 0
    predictions = []

    while not done:
        action, _, _ = agent.select_action(state, deterministic=True)
        next_state, reward, done, info = test_env.step(action)

        if action in [1, 2]:
            total += 1
            actual_up = info['price_change'] > 0
            predicted_up = action == 1

            if predicted_up == actual_up:
                correct += 1

            predictions.append({
                'predicted': 'UP' if predicted_up else 'DOWN',
                'actual': 'UP' if actual_up else 'DOWN',
                'correct': predicted_up == actual_up,
                'change': info['price_change'] * 100
            })

        state = next_state

    test_accuracy = (correct / total * 100) if total > 0 else 0

    print(f"\n  Test Results:")
    print(f"  - Total Profit: ${info['total_profit']:.2f}")
    print(f"  - Directional Accuracy: {test_accuracy:.1f}% ({correct}/{total})")
    print(f"  - Predictions made: {total}")

    # Show last 10 predictions
    print(f"\n  Last 10 predictions:")
    for p in predictions[-10:]:
        status = "OK" if p['correct'] else "X"
        print(f"    [{status}] Predicted: {p['predicted']:4s} | Actual: {p['actual']:4s} | Change: {p['change']:+.2f}%")

    return agent, test_accuracy


# ============== Prediction Logging ==============
PREDICTIONS_FILE = "predictions.csv"


def log_prediction(symbol, direction, price, score, momentum, rsi):
    """Log prediction to CSV for tracking accuracy over time"""
    file_exists = os.path.exists(PREDICTIONS_FILE)

    with open(PREDICTIONS_FILE, 'a') as f:
        if not file_exists:
            f.write("timestamp,symbol,direction,price,score,momentum,rsi,actual_direction,actual_change,correct\n")

        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{symbol},{direction},"
                f"{price:.2f},{score:.1f},{momentum:.2f},{rsi:.1f},,,\n")


def verify_predictions():
    """Verify yesterday's predictions against actual results"""
    if not os.path.exists(PREDICTIONS_FILE):
        print("No predictions to verify")
        return

    df = pd.read_csv(PREDICTIONS_FILE)

    # Find predictions without verification
    unverified = df[df['actual_direction'].isna()]

    if len(unverified) == 0:
        print("All predictions verified")
        return

    from dotenv import load_dotenv
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.rest import TimeFrame
    load_dotenv()

    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        os.getenv('ALPACA_BASE_URL')
    )

    updated = False
    for idx, row in unverified.iterrows():
        pred_date = datetime.strptime(row['timestamp'].split()[0], '%Y-%m-%d')
        next_day = pred_date + timedelta(days=1)

        # Skip if prediction is from today
        if pred_date.date() >= datetime.now().date():
            continue

        try:
            bars = api.get_bars(
                row['symbol'], TimeFrame.Day,
                start=pred_date.strftime('%Y-%m-%d'),
                end=(next_day + timedelta(days=1)).strftime('%Y-%m-%d'),
                feed='iex'
            )
            bar_list = list(bars)

            if len(bar_list) >= 2:
                pred_close = bar_list[0].c
                actual_close = bar_list[1].c
                actual_change = ((actual_close - pred_close) / pred_close) * 100
                actual_direction = "UP" if actual_change > 0 else "DOWN"
                correct = 1 if actual_direction == row['direction'] else 0

                df.at[idx, 'actual_direction'] = actual_direction
                df.at[idx, 'actual_change'] = round(actual_change, 2)
                df.at[idx, 'correct'] = correct
                updated = True

        except Exception as e:
            print(f"  Could not verify {row['symbol']}: {e}")

    if updated:
        df.to_csv(PREDICTIONS_FILE, index=False)

        # Show accuracy stats
        verified = df[df['correct'].notna()]
        if len(verified) > 0:
            accuracy = verified['correct'].mean() * 100
            print(f"\n  LIVE ACCURACY: {accuracy:.1f}% ({int(verified['correct'].sum())}/{len(verified)})")


# ============== Signal Generator ==============
def get_signal(symbols=None, auto_trade=False, top_n=3):
    """
    Smart signal generator - filters to show only actionable opportunities.

    Scoring system:
    - Model confidence (normalized)
    - Momentum alignment (signal matches momentum direction)
    - RSI extremes (oversold for UP, overbought for DOWN)

    Only shows top N opportunities worth your attention.
    """
    from dotenv import load_dotenv
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.rest import TimeFrame

    load_dotenv()

    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        os.getenv('ALPACA_BASE_URL')
    )

    if symbols is None:
        symbols = get_mega_caps()

    print("\n" + "="*60)
    print("  ACTIONABLE SIGNALS")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Scanning {len(symbols)} symbols...")
    print("="*60)

    # First verify any past predictions
    verify_predictions()

    results = []

    for symbol in symbols:
        try:
            env = TradingEnvV2(symbol=symbol, window_size=20)
            agent = PPOAgentV2(env.state_size, env.action_space_n)

            model_path = get_model_path(symbol)
            if not agent.load(model_path):
                continue

            agent.network.eval()

            # Get recent prices
            end = datetime.now()
            start = end - timedelta(days=60)

            bars = api.get_bars(
                symbol, TimeFrame.Day,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                feed='iex'
            )

            bar_list = list(bars)
            if len(bar_list) < 20:
                continue

            prices = np.array([bar.c for bar in bar_list])
            current_price = prices[-1]

            env.load_data(prices)
            state = env.reset()

            # Get prediction
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                action_probs, _ = agent.network(state_tensor)

            probs = action_probs.squeeze().numpy()
            buy_prob = probs[1]
            sell_prob = probs[2]

            if buy_prob > sell_prob:
                direction = "UP"
                confidence = buy_prob / (buy_prob + sell_prob) * 100
            else:
                direction = "DOWN"
                confidence = sell_prob / (buy_prob + sell_prob) * 100

            # Calculate indicators for scoring
            momentum_5d = ((prices[-1] / prices[-5]) - 1) * 100

            # RSI calculation
            deltas = np.diff(prices[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 1e-8)))

            # SCORING SYSTEM (0-100)
            score = 0

            # 1. Base confidence score (0-40 points)
            score += (confidence - 50) * 0.8  # 50% conf = 0, 75% = 20, 100% = 40

            # 2. Momentum alignment (0-30 points)
            if direction == "UP" and momentum_5d > 0:
                score += min(momentum_5d * 5, 30)  # Bullish + positive momentum
            elif direction == "DOWN" and momentum_5d < 0:
                score += min(abs(momentum_5d) * 5, 30)  # Bearish + negative momentum

            # 3. RSI extremes (0-30 points)
            if direction == "UP" and rsi < 40:
                score += (40 - rsi)  # Oversold = good for UP
            elif direction == "DOWN" and rsi > 60:
                score += (rsi - 60)  # Overbought = good for DOWN

            results.append({
                'symbol': symbol,
                'price': current_price,
                'direction': direction,
                'confidence': confidence,
                'momentum': momentum_5d,
                'rsi': rsi,
                'score': max(0, score)  # No negative scores
            })

        except Exception as e:
            pass  # Silent fail for symbols without data

    # Sort by SCORE (not just confidence)
    results.sort(key=lambda x: x['score'], reverse=True)

    # Filter to top N actionable signals
    actionable = [r for r in results if r['score'] > 15][:top_n]

    if not actionable:
        print("\n  No strong signals today. Stay cash.")
        return results

    print(f"\n  TOP {len(actionable)} OPPORTUNITIES (Score > 15):\n")
    print("-"*65)
    print(f"  {'SYMBOL':<6} {'PRICE':>9} {'SIGNAL':>6} {'SCORE':>6} {'MOM':>7} {'RSI':>5}")
    print("-"*65)

    for r in actionable:
        arrow = "^" if r['direction'] == 'UP' else "v"
        print(f"  {arrow} {r['symbol']:<5} ${r['price']:>8.2f}   {r['direction']:<4}  "
              f"{r['score']:>5.1f}  {r['momentum']:>+6.1f}%  {r['rsi']:>4.0f}")

        # Log each actionable prediction
        log_prediction(r['symbol'], r['direction'], r['price'],
                      r['score'], r['momentum'], r['rsi'])

    print("-"*65)

    # Auto paper trade if enabled
    if auto_trade and actionable:
        print("\n  AUTO PAPER TRADING:")
        for r in actionable:
            place_paper_trade(api, r['symbol'], r['direction'], r['price'])

    # Summary
    up_signals = [r for r in actionable if r['direction'] == 'UP']
    down_signals = [r for r in actionable if r['direction'] == 'DOWN']

    print(f"\n  SUMMARY: {len(up_signals)} CALLS, {len(down_signals)} PUTS")
    print("="*60 + "\n")

    return actionable


def place_paper_trade(api, symbol, direction, price):
    """Place a paper trade on Alpaca"""
    try:
        # Check if we already have a position
        try:
            position = api.get_position(symbol)
            print(f"    {symbol}: Already have position, skipping")
            return
        except:
            pass  # No position exists

        # Calculate shares (use $1000 per trade for paper)
        shares = int(1000 / price)
        if shares < 1:
            shares = 1

        side = 'buy' if direction == 'UP' else 'sell'

        # For DOWN prediction, we'd short (but paper trading may not support)
        # So we just log it for now
        if direction == 'DOWN':
            print(f"    {symbol}: PUT signal logged (short not supported in paper)")
            return

        order = api.submit_order(
            symbol=symbol,
            qty=shares,
            side=side,
            type='market',
            time_in_force='day'
        )
        print(f"    {symbol}: {side.upper()} {shares} shares @ ~${price:.2f}")

    except Exception as e:
        print(f"    {symbol}: Trade failed - {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "train":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
            episodes = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
            train(symbol=symbol, episodes=episodes)

        elif cmd == "trainall":
            train_all()

        elif cmd == "trainv3":
            # Enhanced training with VIX/SPY
            symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
            episodes = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
            train_v3(symbol=symbol, episodes=episodes)

        elif cmd == "signal":
            # Optional: specify how many top signals to show
            top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            get_signal(top_n=top_n)

        elif cmd == "auto":
            # Auto paper trading mode
            top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            get_signal(auto_trade=True, top_n=top_n)

        elif cmd == "verify":
            # Just verify past predictions
            verify_predictions()

        elif cmd == "update":
            for symbol in get_mega_caps():
                get_stock_data(symbol, period="5y", force_download=True)
            print("Data updated (5y)!")

    else:
        print("Trading AI - Next-Day Direction Predictor")
        print("=" * 50)
        print("\nUsage:")
        print("  python train.py train AAPL 2000    # Train V2 (20 features)")
        print("  python train.py trainv3 AAPL 2000  # Train V3 (27 features: +VIX/SPY)")
        print("  python train.py trainall           # Train all mega caps (V2)")
        print("  python train.py signal [N]         # Get top N actionable signals")
        print("  python train.py auto [N]           # Auto paper trade top N signals")
        print("  python train.py verify             # Verify past predictions accuracy")
        print("  python train.py update             # Update cached price data")
        print("\nSymbols: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA")
        print("\nV3 adds: VIX level, VIX change, SPY trend, Volume ratio, ATR, Stochastic, SMA50")
