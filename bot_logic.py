import requests
import pandas as pd
import time
from datetime import datetime
from database import Database

class TradingBot:
    def __init__(self):
        self.api_url = "https://api.dexscreener.com/token-profiles/latest/v1"
        self.dex_url = "https://api.dexscreener.com/latest/dex/tokens"
        self.db = Database()
        self.seen_tokens = set() # Keep in memory for session deduplication or load from DB if persistent dedup needed
        
        # Configuration
        self.min_liquidity = 1000
        self.profit_target = 0.20
        self.stop_loss = -0.10
        self.trade_amount = 0.5
        self.min_score = 70

    @property
    def balance(self):
        return self.db.get_balance()

    @property
    def positions(self):
        return self.db.get_positions()

    @property
    def history(self):
        return self.db.get_history()

    def deposit_sol(self, amount):
        self.db.update_balance(amount)

    def fetch_new_tokens(self):
        """Fetches latest token profiles."""
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [t for t in data if t.get('chainId') == 'solana']
        except Exception as e:
            print(f"Error fetching tokens: {e}")
        return []

    def get_token_details(self, token_address):
        """Fetches detailed pair info for a token."""
        try:
            url = f"{self.dex_url}/{token_address}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('pairs'):
                    sorted_pairs = sorted(data['pairs'], key=lambda x: float(x.get('liquidity', {}).get('usd', 0)), reverse=True)
                    return sorted_pairs[0]
        except Exception as e:
            print(f"Error details for {token_address}: {e}")
        return None

    def analyze_token(self, pair_data):
        """Analyze a token with strict 'Sniper' criteria."""
        if not pair_data:
            return 'IGNORE', 0

        liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
        vol_data = pair_data.get('volume', {})
        volume_h1 = float(vol_data.get('h1', 0))
        txns = pair_data.get('txns', {}).get('h1', {})
        buys = int(txns.get('buys', 0))
        sells = int(txns.get('sells', 0))
        price_change = pair_data.get('priceChange', {})
        change_h1 = float(price_change.get('h1', 0))
        
        total_txns = buys + sells
        if total_txns == 0:
            return 'IGNORE', 0

        avg_tx_value = volume_h1 / total_txns if total_txns > 0 else 0
        buy_ratio = buys / total_txns

        # ---------------- SCORING LOGIC ----------------
        score = 0
        
        if liquidity < 2000:
            return 'WEAK', 0
        elif liquidity > 10000:
            score += 20
        elif liquidity > 5000:
            score += 10
        
        if buy_ratio > 0.60:
            score += 50
        
        if volume_h1 > 10000:
            score += 10
        elif volume_h1 > 5000:
            score += 5
            
        if change_h1 > 10:
            score += 10
        elif change_h1 < -10:
            score -= 20
            
        if avg_tx_value > 50:
            score += 10
            
        strength = 'WEAK'
        if score >= self.min_score:
            strength = 'STRONG'
        elif score >= (self.min_score - 30):
            strength = 'MEDIUM'
            
        return strength, score

    def enter_position(self, token_data, pair_data):
        address = token_data['tokenAddress']
        # Check against DB positions
        current_positions = [p['address'] for p in self.positions]
        if address in current_positions:
            return False

        price = float(pair_data['priceNative'])
        symbol = pair_data['baseToken']['symbol']
        current_balance = self.balance
        
        if current_balance >= self.trade_amount:
            # Deduct Balance
            self.db.update_balance(-self.trade_amount)
            
            amount_tokens = self.trade_amount / price
            
            position = {
                'address': address,
                'symbol': symbol,
                'entry_price': price,
                'amount': amount_tokens,
                'current_price': price,
                'entry_time': datetime.now().isoformat()
            }
            self.db.add_position(position)
            return True
        return False

    def update_positions(self):
        """Updates price and PnL for active positions from DB."""
        positions = self.positions # Get latest from DB
        for pos in positions:
            pair = self.get_token_details(pos['address'])
            if pair:
                current_price = float(pair['priceNative'])
                
                # Calculate PnL
                value_now = pos['quantity'] * current_price
                value_entry = pos['quantity'] * pos['avg_entry_price']
                pnl = value_now - value_entry
                pnl_pct = (pnl / value_entry)
                
                # Update stats in DB
                self.db.update_position_stats(pos['address'], current_price, pnl, pnl_pct*100)
                
                # Check Exit Conditions
                reason = None
                if pnl_pct >= self.profit_target:
                    reason = "TAKE PROFIT"
                elif pnl_pct <= self.stop_loss:
                    reason = "STOP LOSS"
                
                if reason:
                    # Add back to balance
                    self.db.update_balance(value_now)
                    
                    # Log Trade
                    trade_data = {
                        'symbol': pos['symbol'],
                        'address': pos['address'],
                        'entry_price': pos['avg_entry_price'],
                        'exit_price': current_price,
                        'amount': pos['quantity'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'reason': reason,
                        'entry_time': pos['entry_time'],
                        'exit_time': datetime.now().isoformat()
                    }
                    self.db.add_trade_history(trade_data)
                    self.db.remove_position(pos['address'])

