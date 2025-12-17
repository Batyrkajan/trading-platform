"""
Professional Stock Screener with Fundamentals
- Robust market regime detection
- Advanced chart pattern detection (TA-Lib + custom)
- Fundamental analysis (earnings, analysts, insiders, financial health)
- Regime-adaptive strategy
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.market_regime_detector import RobustMarketRegimeDetector
from src.advanced_pattern_detector import AdvancedPatternDetector


class ProfessionalStockScreener:
    """
    Professional-grade screener with:
    - Robust regime detection
    - Advanced pattern recognition
    - Fundamental analysis
    - Adaptive scoring based on market conditions
    """

    def __init__(self, min_market_cap=10e9):
        self.min_market_cap = min_market_cap
        self.pattern_detector = AdvancedPatternDetector()
        self.regime_detector = RobustMarketRegimeDetector()

    # === FUNDAMENTAL ANALYSIS METHODS ===

    def get_earnings_data(self, ticker):
        """Get earnings quality metrics"""
        try:
            info = ticker.info

            earnings_data = {
                'eps_growth': info.get('earningsGrowth'),
                'revenue_growth': info.get('revenueGrowth'),
                'profit_margin': info.get('profitMargins'),
                'roe': info.get('returnOnEquity'),
            }

            # Get earnings history for surprises
            try:
                earnings_hist = ticker.earnings_history
                if earnings_hist is not None and not earnings_hist.empty:
                    recent_surprises = earnings_hist.head(4)
                    if 'Surprise(%)' in recent_surprises.columns:
                        earnings_data['beat_rate'] = (recent_surprises['Surprise(%)'] > 0).sum() / len(recent_surprises)
                    else:
                        earnings_data['beat_rate'] = None
            except:
                earnings_data['beat_rate'] = None

            return earnings_data
        except:
            return None

    def get_analyst_data(self, ticker):
        """Get analyst ratings and price targets"""
        try:
            info = ticker.info

            analyst_data = {
                'target_mean': info.get('targetMeanPrice'),
                'recommendation': info.get('recommendationKey'),
                'num_analysts': info.get('numberOfAnalystOpinions')
            }

            # Calculate upside potential
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if current_price and analyst_data['target_mean']:
                analyst_data['upside_pct'] = ((analyst_data['target_mean'] - current_price) / current_price) * 100
            else:
                analyst_data['upside_pct'] = None

            return analyst_data
        except:
            return None

    def get_insider_activity(self, ticker):
        """Get insider trading activity"""
        try:
            insider_purchases = ticker.insider_purchases
            if insider_purchases is not None and not insider_purchases.empty:
                return {'insider_buys_count': len(insider_purchases.head(10))}
            return {'insider_buys_count': 0}
        except:
            return {'insider_buys_count': 0}

    def get_institutional_data(self, ticker):
        """Get institutional ownership data"""
        try:
            info = ticker.info
            return {
                'short_pct_float': info.get('shortPercentOfFloat'),
                'institutional_pct': info.get('heldPercentInstitutions')
            }
        except:
            return None

    def get_financial_health(self, ticker):
        """Get financial health metrics"""
        try:
            info = ticker.info

            health_data = {
                'current_ratio': info.get('currentRatio'),
                'debt_to_equity': info.get('debtToEquity'),
                'free_cashflow': info.get('freeCashflow'),
                'operating_cashflow': info.get('operatingCashflow')
            }

            # Calculate health score (0-100)
            score = 0
            if health_data['current_ratio']:
                score += min(health_data['current_ratio'] * 10, 25)
            if health_data['debt_to_equity']:
                score += max(25 - health_data['debt_to_equity'] / 4, 0)
            if health_data['free_cashflow'] and health_data['free_cashflow'] > 0:
                score += 25
            if health_data['operating_cashflow'] and health_data['operating_cashflow'] > 0:
                score += 25

            health_data['health_score'] = min(score, 100)
            return health_data
        except:
            return None

    def get_valuation_metrics(self, ticker):
        """Get valuation metrics"""
        try:
            info = ticker.info

            valuation = {
                'pe_ratio': info.get('trailingPE'),
                'peg_ratio': info.get('pegRatio'),
                'market_cap': info.get('marketCap')
            }

            # Calculate value score
            score = 50
            if valuation['pe_ratio']:
                if valuation['pe_ratio'] < 15:
                    score += 20
                elif valuation['pe_ratio'] < 25:
                    score += 10
                elif valuation['pe_ratio'] > 40:
                    score -= 20

            if valuation['peg_ratio']:
                if valuation['peg_ratio'] < 1:
                    score += 20
                elif valuation['peg_ratio'] < 2:
                    score += 10

            valuation['value_score'] = max(min(score, 100), 0)
            return valuation
        except:
            return None

    def get_sp500_tickers(self):
        """Get S&P 500 tickers from Wikipedia"""
        try:
            import pandas as pd
            # Fetch S&P 500 list from Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()

            # Clean tickers (some have dots that need to be dashes for yfinance)
            tickers = [ticker.replace('.', '-') for ticker in tickers]

            print(f"[OK] Loaded {len(tickers)} S&P 500 tickers from Wikipedia")
            return tickers

        except Exception as e:
            print(f"[WARNING] Could not fetch S&P 500 list: {e}")
            print("   Falling back to curated list...")
            # Fallback to curated list
            return [
                # Tech
                'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'QCOM', 'AVGO', 'ORCL',
                # Finance
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW',
                # Healthcare
                'UNH', 'JNJ', 'PFE', 'ABBV', 'TMO', 'DHR', 'BMY', 'AMGN', 'GILD',
                # Consumer
                'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'DIS', 'NFLX',
                # Industrials
                'BA', 'CAT', 'GE', 'UPS', 'HON', 'RTX', 'LMT', 'DE',
                # Energy
                'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC',
                # Others
                'PYPL', 'SHOP', 'COIN', 'UBER', 'ABNB'
            ]

    def analyze_stock(self, ticker, regime_result):
        """Analyze stock with advanced pattern detection"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="3mo")

            if len(hist) < 60:
                return None

            # Basic filters
            market_cap = info.get('marketCap', 0)
            if market_cap < self.min_market_cap:
                return None

            # Price metrics
            current_price = hist['Close'].iloc[-1]
            high_52w = hist['High'].max()
            drawdown = (current_price - high_52w) / high_52w * 100

            # Momentum
            weekly_change = (current_price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5] * 100
            monthly_change = (current_price - hist['Close'].iloc[-20]) / hist['Close'].iloc[-20] * 100

            # Volume
            avg_volume = hist['Volume'].tail(20).mean()
            recent_volume = hist['Volume'].tail(5).mean()
            volume_surge = (recent_volume / avg_volume - 1) * 100

            # Options check
            options_dates = stock.options if hasattr(stock, 'options') else []
            if not options_dates:
                return None

            # === DETECT ALL PATTERNS ===
            patterns = self.pattern_detector.detect_all_patterns(hist, current_price)

            if not patterns:
                return None  # No patterns = skip

            # === GET FUNDAMENTAL DATA ===
            earnings = self.get_earnings_data(stock)
            analysts = self.get_analyst_data(stock)
            insiders = self.get_insider_activity(stock)
            institutional = self.get_institutional_data(stock)
            health = self.get_financial_health(stock)
            valuation = self.get_valuation_metrics(stock)

            # === REGIME-ADAPTIVE SCORING ===
            score = 0
            setup_types = []
            confidence = "LOW"
            regime = regime_result['regime']
            fundamental_flags = []

            # Pattern scoring based on type and confidence
            high_conf_patterns = [p for p in patterns if p.get('confidence', 0) >= 80]
            med_conf_patterns = [p for p in patterns if 70 <= p.get('confidence', 0) < 80]

            pattern_names = [p['pattern'] for p in patterns]

            # === STRONG_UPTREND Regime ===
            if regime == 'STRONG_UPTREND':
                # Aggressive: Look for breakouts and continuations
                if 'CUP_AND_HANDLE' in pattern_names:
                    score += 15
                    setup_types.append("🏆CUP_AND_HANDLE")
                    confidence = "VERY_HIGH"

                if 'BULL_FLAG' in pattern_names:
                    score += 12
                    setup_types.append("🚀BULL_FLAG")
                    confidence = "HIGH"

                if 'RESISTANCE_BREAK' in pattern_names and 'VOLUME_BREAKOUT' in pattern_names:
                    score += 10
                    setup_types.append("BREAKOUT_WITH_VOLUME")
                    confidence = "HIGH"

                if 'DOUBLE_BOTTOM' in pattern_names:
                    score += 11
                    setup_types.append("DOUBLE_BOTTOM_REVERSAL")
                    confidence = "HIGH"

                # Candlestick confirmation
                if 'BULLISH_ENGULFING' in pattern_names or 'MORNING_STAR' in pattern_names:
                    score += 3

            # === UPTREND Regime ===
            elif regime == 'UPTREND':
                # Moderate: Support bounces and breakouts
                if 'SUPPORT_BOUNCE' in pattern_names and volume_surge > 20:
                    score += 9
                    setup_types.append("SUPPORT_BOUNCE_VOLUME")
                    confidence = "HIGH"

                if 'CONSOLIDATION_BREAKOUT' in pattern_names:
                    score += 8
                    setup_types.append("CONSOLIDATION_BREAKOUT")
                    confidence = "MEDIUM"

                if 'BULL_FLAG' in pattern_names:
                    score += 10
                    setup_types.append("BULL_FLAG")
                    confidence = "HIGH"

            # === LATE_STAGE_ROTATION Regime ===
            elif regime == 'LATE_STAGE_ROTATION':
                # Very selective: Only highest conviction setups
                if 'CUP_AND_HANDLE' in pattern_names:
                    score += 10
                    setup_types.append("🏆CUP_AND_HANDLE")
                    confidence = "HIGH"

                if 'BULL_FLAG' in pattern_names and volume_surge > 30:
                    score += 9
                    setup_types.append("BULL_FLAG_STRONG_VOLUME")
                    confidence = "MEDIUM"

                if 'DOUBLE_BOTTOM' in pattern_names:
                    score += 8
                    setup_types.append("DOUBLE_BOTTOM")
                    confidence = "MEDIUM"

                # Require volume confirmation in late stage
                if 'VOLUME_BREAKOUT' not in pattern_names and 'ACCUMULATION' not in pattern_names:
                    score -= 3

            # === CHOPPY Regime ===
            elif regime == 'CHOPPY':
                # Range-bound plays only
                if 'RANGE_BOUND' in pattern_names:
                    score += 7
                    setup_types.append("💰RANGE_PREMIUM_SELLING")
                    confidence = "MEDIUM"

                if 'SUPPORT_BOUNCE' in pattern_names and drawdown < -20:
                    score += 6
                    setup_types.append("SUPPORT_BOUNCE")
                    confidence = "LOW"

            # === DOWNTREND/VOLATILE Regime ===
            else:
                # Very defensive
                if 'DOUBLE_BOTTOM' in pattern_names and volume_surge > 40:
                    score += 5
                    setup_types.append("COUNTER_TREND_REVERSAL")
                    confidence = "LOW"

            # Volume confirmation bonus
            if 'ACCUMULATION' in pattern_names:
                score += 2
                setup_types.append("ACCUMULATION")

            if 'VOLUME_BREAKOUT' in pattern_names:
                score += 2

            # High-confidence pattern bonus
            if len(high_conf_patterns) >= 2:
                score += 3
                confidence = "HIGH" if confidence == "MEDIUM" else confidence

            # Liquidity bonus
            if avg_volume > 2_000_000:
                score += 1

            # === FUNDAMENTAL SCORING ===
            # Analyst upside potential (0-5 points)
            if analysts and analysts.get('upside_pct'):
                upside = analysts['upside_pct']
                if upside > 20:
                    score += 5
                    fundamental_flags.append('HIGH_ANALYST_UPSIDE')
                elif upside > 10:
                    score += 3
                elif upside > 5:
                    score += 1

            # Earnings quality (0-3 points)
            if earnings:
                if earnings.get('eps_growth') and earnings['eps_growth'] > 0.15:  # 15%+ growth
                    score += 2
                    fundamental_flags.append('STRONG_EPS_GROWTH')
                if earnings.get('beat_rate') and earnings['beat_rate'] > 0.75:  # 75%+ beat rate
                    score += 1
                    fundamental_flags.append('EARNINGS_BEATER')

            # Financial health (0-2 points)
            if health and health.get('health_score'):
                if health['health_score'] > 75:
                    score += 2
                    fundamental_flags.append('STRONG_FINANCIALS')
                elif health['health_score'] > 50:
                    score += 1

            # Insider buying (0-2 points)
            if insiders and insiders.get('insider_buys_count', 0) > 3:
                score += 2
                fundamental_flags.append('INSIDER_BUYING')

            # Low short interest is bullish (0-1 point)
            if institutional and institutional.get('short_pct_float'):
                if institutional['short_pct_float'] < 0.05:  # Less than 5%
                    score += 1
                    fundamental_flags.append('LOW_SHORT_INTEREST')
                elif institutional['short_pct_float'] > 0.20:  # More than 20%
                    fundamental_flags.append('HIGH_SHORT_INTEREST')

            # Valuation check (penalty for expensive stocks)
            if valuation and valuation.get('pe_ratio') and valuation['pe_ratio'] > 50:
                score -= 2
                fundamental_flags.append('EXPENSIVE_VALUATION')

            # Filter low scores
            min_score = {
                'STRONG_UPTREND': 8,
                'UPTREND': 7,
                'LATE_STAGE_ROTATION': 8,  # Higher threshold for late stage
                'CHOPPY': 6,
                'DOWNTREND': 5,
                'VOLATILE': 5
            }.get(regime, 5)

            if score < min_score:
                return None

            result = {
                'ticker': ticker,
                'score': score,
                'confidence': confidence,
                'setup_types': ','.join(setup_types) if setup_types else 'NONE',
                'patterns': [p['pattern'] for p in patterns],
                'pattern_details': patterns,
                'current_price': current_price,
                'market_cap': market_cap / 1e9,
                'drawdown_pct': drawdown,
                'weekly_change': weekly_change,
                'monthly_change': monthly_change,
                'volume_surge': volume_surge,
                'avg_volume': avg_volume / 1e6,
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                # Fundamental data
                'earnings': earnings,
                'analysts': analysts,
                'health': health,
                'valuation': valuation,
                'institutional': institutional,
                'fundamental_flags': ','.join(fundamental_flags) if fundamental_flags else 'None'
            }

            # Add trading recommendations
            trading_rec = self.generate_trading_recommendations(
                result, patterns, regime_result, hist, current_price
            )
            result.update(trading_rec)

            return result

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return None

    def generate_trading_recommendations(self, analysis, patterns, regime, hist, current_price):
        """
        Generate comprehensive trading recommendations including:
        - Direction (LONG/SHORT/NEUTRAL)
        - Risk management (stop loss, take profit)
        - Entry/exit timing
        - Hold duration
        """
        recommendations = {}

        # 1. DETERMINE DIRECTION
        direction, direction_confidence = self.determine_direction(analysis, patterns, regime)
        recommendations['direction'] = direction
        recommendations['direction_confidence'] = direction_confidence

        # 2. CALCULATE RISK PARAMETERS
        risk_params = self.calculate_risk_parameters(patterns, hist, current_price, direction)
        recommendations.update(risk_params)

        # 3. DETERMINE TIMING
        timing = self.determine_timing(analysis, patterns, regime, hist, current_price)
        recommendations.update(timing)

        # 4. ESTIMATE HOLD DURATION
        hold_duration = self.estimate_hold_duration(analysis, patterns, regime)
        recommendations['hold_duration'] = hold_duration

        return recommendations

    def determine_direction(self, analysis, patterns, regime):
        """
        Determine trade direction: LONG, SHORT, or NEUTRAL
        Returns: (direction, confidence)
        """
        bullish_score = 0
        bearish_score = 0

        # Pattern signals
        for pattern in patterns:
            if pattern['signal'] == 'BULLISH':
                bullish_score += pattern['confidence'] / 100
            elif pattern['signal'] == 'BEARISH':
                bearish_score += pattern['confidence'] / 100

        # Fundamental signals
        fundamental_flags = analysis.get('fundamental_flags', '').split(',')

        if 'HIGH_ANALYST_UPSIDE' in fundamental_flags:
            bullish_score += 1.5
        if 'STRONG_EPS_GROWTH' in fundamental_flags:
            bullish_score += 1.0
        if 'EARNINGS_BEATS' in fundamental_flags:
            bullish_score += 0.5
        if 'STRONG_FINANCIALS' in fundamental_flags:
            bullish_score += 1.0
        if 'INSIDER_BUYING' in fundamental_flags:
            bullish_score += 0.75
        if 'LOW_SHORT_INTEREST' in fundamental_flags:
            bullish_score += 0.5

        if 'EXPENSIVE_VALUATION' in fundamental_flags:
            bearish_score += 0.5

        # Market regime bias
        regime_name = regime['regime']

        if regime_name in ['STRONG_UPTREND', 'UPTREND']:
            bullish_score += 1.5
        elif regime_name == 'LATE_STAGE_ROTATION':
            bullish_score += 0.5
        elif regime_name in ['DOWNTREND', 'VOLATILE']:
            bearish_score += 1.5
            bullish_score -= 1.0  # Reduce bullish conviction
        elif regime_name == 'CHOPPY':
            # Reduce both
            bullish_score *= 0.7
            bearish_score *= 0.7

        # Determine direction
        if bullish_score > bearish_score * 1.5:
            direction = 'LONG'
            confidence = min(95, int((bullish_score / (bullish_score + bearish_score)) * 100))
        elif bearish_score > bullish_score * 1.5:
            direction = 'SHORT'
            confidence = min(95, int((bearish_score / (bullish_score + bearish_score)) * 100))
        else:
            direction = 'NEUTRAL'
            confidence = 50

        return direction, confidence

    def calculate_risk_parameters(self, patterns, hist, current_price, direction):
        """
        Calculate stop loss and take profit levels based on patterns
        """
        params = {}

        if direction == 'NEUTRAL':
            params['stop_loss'] = None
            params['take_profit_1'] = None
            params['take_profit_2'] = None
            params['risk_reward_ratio'] = None
            return params

        # Find key levels from patterns
        support_levels = []
        resistance_levels = []
        targets = []

        for pattern in patterns:
            if 'support_level' in pattern:
                support_levels.append(pattern['support_level'])
            if 'resistance_level' in pattern:
                resistance_levels.append(pattern['resistance_level'])
            if 'breakout_level' in pattern:
                resistance_levels.append(pattern['breakout_level'])
            if 'target' in pattern:
                targets.append(pattern['target'])
            if 'neckline' in pattern:
                resistance_levels.append(pattern['neckline'])
            if 'bottom_level' in pattern:
                support_levels.append(pattern['bottom_level'])

        # Calculate stop loss
        if direction == 'LONG':
            # Stop below recent support or 2-3% below entry
            if support_levels:
                stop_loss = max(support_levels) * 0.98  # Just below strongest support
            else:
                # Use recent low
                recent_low = hist['Low'].tail(20).min()
                stop_loss = recent_low * 0.99

            # Ensure stop is reasonable (2-5% max)
            max_stop = current_price * 0.95  # Max 5% stop
            min_stop = current_price * 0.98  # Min 2% stop
            stop_loss = max(min(stop_loss, current_price * 0.99), max_stop)

        else:  # SHORT
            # Stop above recent resistance or 2-3% above entry
            if resistance_levels:
                stop_loss = min(resistance_levels) * 1.02  # Just above weakest resistance
            else:
                # Use recent high
                recent_high = hist['High'].tail(20).max()
                stop_loss = recent_high * 1.01

            # Ensure stop is reasonable
            min_stop = current_price * 1.05  # Max 5% stop
            max_stop = current_price * 1.02  # Min 2% stop
            stop_loss = min(max(stop_loss, current_price * 1.01), min_stop)

        # Calculate take profit targets
        if direction == 'LONG':
            if targets:
                tp1 = min(targets)  # Conservative target
                tp2 = max(targets) if len(targets) > 1 else tp1 * 1.5
            else:
                # Use risk multiple
                risk = current_price - stop_loss
                tp1 = current_price + (risk * 2)  # 2R
                tp2 = current_price + (risk * 3)  # 3R
        else:  # SHORT
            if targets:
                tp1 = max(targets)
                tp2 = min(targets) if len(targets) > 1 else tp1 * 0.5
            else:
                risk = stop_loss - current_price
                tp1 = current_price - (risk * 2)
                tp2 = current_price - (risk * 3)

        # Calculate risk/reward
        risk_amount = abs(current_price - stop_loss)
        reward_amount = abs(tp1 - current_price)
        risk_reward = reward_amount / risk_amount if risk_amount > 0 else 0

        params['stop_loss'] = round(stop_loss, 2)
        params['stop_loss_pct'] = round(((stop_loss - current_price) / current_price) * 100, 2)
        params['take_profit_1'] = round(tp1, 2)
        params['take_profit_1_pct'] = round(((tp1 - current_price) / current_price) * 100, 2)
        params['take_profit_2'] = round(tp2, 2)
        params['take_profit_2_pct'] = round(((tp2 - current_price) / current_price) * 100, 2)
        params['risk_reward_ratio'] = round(risk_reward, 2)

        return params

    def determine_timing(self, analysis, patterns, regime, hist, current_price):
        """
        Determine entry and exit timing
        """
        timing = {}

        # Check for breakout patterns
        breakout_patterns = ['CUP_AND_HANDLE', 'BULL_FLAG', 'RESISTANCE_BREAK',
                            'CONSOLIDATION_BREAKOUT', 'DOUBLE_BOTTOM']

        has_breakout = any(p['pattern'] in breakout_patterns for p in patterns)

        # Check for reversal patterns
        reversal_patterns = ['DOUBLE_BOTTOM', 'SUPPORT_BOUNCE', 'HAMMER',
                            'BULLISH_ENGULFING', 'MORNING_STAR']

        has_reversal = any(p['pattern'] in reversal_patterns for p in patterns)

        # Check price momentum
        closes = hist['Close'].values
        sma_20 = closes[-20:].mean()
        sma_5 = closes[-5:].mean()

        above_ma = current_price > sma_20
        momentum_up = sma_5 > sma_20

        # Check volume
        volumes = hist['Volume'].values
        avg_volume = volumes[-20:].mean()
        recent_volume = volumes[-1]
        volume_surge = recent_volume > avg_volume * 1.2

        # Determine entry timing
        if has_breakout and volume_surge:
            entry_timing = 'IMMEDIATE'
            entry_rationale = 'Breakout confirmed with volume - enter now'
        elif has_reversal and above_ma:
            entry_timing = 'IMMEDIATE'
            entry_rationale = 'Reversal at support - enter on strength'
        elif momentum_up and not has_breakout:
            entry_timing = 'WAIT_FOR_DIP'
            entry_rationale = 'Strong momentum but extended - wait for pullback to 20 SMA'
        elif not above_ma:
            entry_timing = 'WAIT_FOR_BREAKOUT'
            entry_rationale = f'Wait for price to break above ${sma_20:.2f} (20 SMA)'
        else:
            entry_timing = 'WAIT_FOR_CONFIRMATION'
            entry_rationale = 'Wait for clearer signal or higher volume'

        # Regime adjustment
        if regime['regime'] in ['DOWNTREND', 'VOLATILE']:
            if entry_timing == 'IMMEDIATE':
                entry_timing = 'WAIT_FOR_CONFIRMATION'
                entry_rationale += ' (but market regime is weak - use caution)'

        timing['entry_timing'] = entry_timing
        timing['entry_rationale'] = entry_rationale
        timing['sma_20'] = round(sma_20, 2)

        return timing

    def estimate_hold_duration(self, analysis, patterns, regime):
        """
        Estimate recommended hold duration based on setup type
        """
        score = analysis['score']

        # Pattern time horizons
        swing_patterns = ['BULL_FLAG', 'CONSOLIDATION_BREAKOUT', 'HAMMER',
                         'BULLISH_ENGULFING', 'VOLUME_BREAKOUT']

        position_patterns = ['CUP_AND_HANDLE', 'DOUBLE_BOTTOM', 'RESISTANCE_BREAK',
                            'HIGHER_LOWS']

        has_swing = any(p['pattern'] in swing_patterns for p in patterns)
        has_position = any(p['pattern'] in position_patterns for p in patterns)

        # Fundamental strength
        fundamental_flags = analysis.get('fundamental_flags', '').split(',')
        strong_fundamentals = len([f for f in fundamental_flags if f not in ['None', 'EXPENSIVE_VALUATION']]) >= 3

        # Determine duration
        if score >= 20 and strong_fundamentals:
            duration = 'LONG_TERM'
            timeframe = '3-12 months'
            rationale = 'High score + strong fundamentals = hold for major move'
        elif score >= 15 and (has_position or strong_fundamentals):
            duration = 'POSITION'
            timeframe = '2-8 weeks'
            rationale = 'Good technical + fundamental alignment'
        elif has_swing or score >= 10:
            duration = 'SWING'
            timeframe = '3-10 days'
            rationale = 'Technical setup for quick move'
        else:
            duration = 'DAY_TRADE'
            timeframe = 'Intraday'
            rationale = 'Low conviction - quick in/out only'

        # Regime adjustment
        if regime['regime'] in ['VOLATILE', 'CHOPPY']:
            if duration == 'LONG_TERM':
                duration = 'POSITION'
                timeframe = '2-8 weeks'
                rationale += ' (reduced due to market volatility)'
            elif duration == 'POSITION':
                duration = 'SWING'
                timeframe = '3-10 days'
                rationale += ' (reduced due to choppy market)'

        return {
            'duration': duration,
            'timeframe': timeframe,
            'rationale': rationale
        }

    def analyze_single_stock_quick(self, ticker):
        """
        Quick analysis of a single stock with technical scoring
        Used for single stock analysis in web app
        """
        try:
            # Get current market regime
            regime_result = self.regime_detector.determine_regime()

            # Analyze the stock
            result = self.analyze_stock(ticker, regime_result)

            return result
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return None

    def screen(self):
        """Run complete screening process"""
        print("Professional Stock Screening...")
        print()

        # 1. Detect market regime
        print("Analyzing market regime...")
        regime_result = self.regime_detector.determine_regime()
        strategy = self.regime_detector.get_strategy_recommendation(regime_result)

        print(f"\nREGIME: {regime_result['regime']}")
        print(f"   Confidence: {regime_result['confidence']}%")
        print(f"\nSTRATEGY: {strategy['strategy']}")
        print(f"   {strategy['description']}")
        print()

        # 2. Screen stocks
        tickers = self.get_sp500_tickers()
        results = []

        for i, ticker in enumerate(tickers):
            print(f"Analyzing {ticker} ({i+1}/{len(tickers)})...", end='\r')
            result = self.analyze_stock(ticker, regime_result)
            if result:
                results.append(result)

        print("\n[OK] Screening complete!")
        print()

        return pd.DataFrame(results).sort_values('score', ascending=False), regime_result, strategy


def main():
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("="*80)
    print("PROFESSIONAL STOCK SCREENER")
    print("="*80)
    print()

    screener = ProfessionalStockScreener()
    results, regime, strategy = screener.screen()

    if len(results) == 0:
        print("[X] No high-quality setups found")
        print("   Market regime doesn't favor current screening criteria")
        print("   Consider waiting for better conditions or adjusting strategy")
        return

    # Display top picks
    print(f"TOP OPPORTUNITIES ({len(results)} found):\n")
    top_picks = results.head(10)

    for idx, row in top_picks.iterrows():
        print(f"{'='*80}")
        print(f"#{idx+1}. {row['ticker']} - {row['sector']}")
        print(f"{'='*80}")
        print(f"   Score:      {row['score']} | Confidence: {row['confidence']}")
        print(f"   Setup:      {row['setup_types']}")
        print(f"   Price:      ${row['current_price']:.2f}")
        print(f"   Drawdown:   {row['drawdown_pct']:.1f}%")
        print(f"   Weekly:     {row['weekly_change']:+.1f}%")
        print(f"   Monthly:    {row['monthly_change']:+.1f}%")
        print(f"   Volume:     {row['volume_surge']:+.1f}% surge")

        # Trading recommendations
        print(f"\n   [TRADE RECOMMENDATION]")
        print(f"   Direction:  {row['direction']} ({row['direction_confidence']}% confidence)")

        if row['direction'] != 'NEUTRAL':
            print(f"   Entry:      {row['entry_timing']}")
            print(f"               {row['entry_rationale']}")
            print(f"\n   Risk/Reward: {row['risk_reward_ratio']}:1")
            print(f"   Stop Loss:   ${row['stop_loss']:.2f} ({row['stop_loss_pct']:+.1f}%)")
            print(f"   Target 1:    ${row['take_profit_1']:.2f} ({row['take_profit_1_pct']:+.1f}%)")
            print(f"   Target 2:    ${row['take_profit_2']:.2f} ({row['take_profit_2_pct']:+.1f}%)")

            hold_dur = row['hold_duration']
            print(f"\n   Hold Duration: {hold_dur['duration']} ({hold_dur['timeframe']})")
            print(f"                  {hold_dur['rationale']}")

        print(f"\n   PATTERNS DETECTED:")

        # Show pattern details
        for pattern in row['pattern_details']:
            icon = "[CHART]" if pattern['type'] == 'CHART' else "[CANDLE]" if pattern['type'] == 'CANDLESTICK' else "[VOL]"
            print(f"      {icon} {pattern['pattern']} ({pattern['confidence']}%) - {pattern['description']}")

        # Fundamental highlights
        if row.get('fundamental_flags') and row['fundamental_flags'] != 'None':
            print(f"\n   FUNDAMENTAL HIGHLIGHTS:")
            print(f"      {row['fundamental_flags']}")

        print()

    # Export
    filename = f"professional_screener_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results.to_csv(filename, index=False)
    print(f"[SAVE] Full results saved to: {filename}")
    print("="*80)


if __name__ == "__main__":
    main()
