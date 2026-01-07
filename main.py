import time
import requests
import json
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configuration
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex"
TOKEN_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
CHECK_INTERVAL = 10  # Seconds between checks
PROFIT_TARGET = 0.20  # 20% profit
STOP_LOSS = -0.10  # 10% loss
MIN_LIQUIDITY_USD = 1000  # Minimum liquidity to buy
INITIAL_BALANCE_SOL = 10.0  # Paper trading balance

class PaperTrader:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.portfolio = {}  # {token_address: {'amount': float, 'entry_price': float, 'symbol': str}}
        self.trade_history = []
        self.seen_tokens = set()

    def current_value(self, current_prices):
        total_value = self.balance
        for token, data in self.portfolio.items():
            price = current_prices.get(token, data['entry_price'])
            total_value += data['amount'] * price
        return total_value

    def buy(self, token_data, amount_sol):
        token_address = token_data['baseToken']['address']
        price_native = float(token_data['priceNative'])
        symbol = token_data['baseToken']['symbol']

        if self.balance >= amount_sol:
            token_amount = amount_sol / price_native
            self.balance -= amount_sol
            self.portfolio[token_address] = {
                'amount': token_amount,
                'entry_price': price_native,
                'symbol': symbol,
                'max_price': price_native # Track max price for potentially trailing stop (not implemented yet but good to have)
            }
            print(f"{Fore.GREEN}[BUY] {symbol} ({token_address}) at {price_native:.9f} SOL | Amt: {token_amount:.2f}")
            return True
        else:
            print(f"{Fore.RED}[FAIL] Insufficient balance to buy {symbol}")
            return False

    def sell(self, token_address, current_price, reason="Exit"):
        if token_address in self.portfolio:
            data = self.portfolio[token_address]
            amount = data['amount']
            entry_price = data['entry_price']
            symbol = data['symbol']
            
            revenue = amount * current_price
            profit_sol = revenue - (amount * entry_price)
            profit_pct = (profit_sol / (amount * entry_price)) * 100

            self.balance += revenue
            del self.portfolio[token_address]
            self.trade_history.append({
                'token': token_address,
                'symbol': symbol,
                'entry': entry_price,
                'exit': current_price,
                'profit_sol': profit_sol,
                'profit_pct': profit_pct
            })
            
            color = Fore.GREEN if profit_sol > 0 else Fore.RED
            print(f"{color}[SELL] {symbol} at {current_price:.9f} SOL | PnL: {profit_sol:.4f} SOL ({profit_pct:.2f}%) | Reason: {reason}")
            return True
        return False

def fetch_new_tokens():
    try:
        response = requests.get(TOKEN_PROFILES_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"{Fore.RED}Error fetching profiles: {e}")
    return []

def get_token_pair(token_address):
    url = f"{DEXSCREENER_API_URL}/tokens/{token_address}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs'):
                # Sort by liquidity or return the main one (usually first is best liquid)
                # But filter for Solana pairs only
                sol_pairs = [p for p in data['pairs'] if p['chainId'] == 'solana' and p['quoteToken']['symbol'] == 'SOL']
                if sol_pairs:
                    return sol_pairs[0] # Return the best pair
    except Exception as e:
        print(f"{Fore.RED}Error fetching pair for {token_address}: {e}")
    return None

def main():
    trader = PaperTrader(INITIAL_BALANCE_SOL)
    print(f"{Fore.CYAN}Starting DexScreener Solana Paper Trading Bot...")
    print(f"{Fore.CYAN}Initial Balance: {trader.balance} SOL")
    print(f"{Fore.CYAN}Target Profit: {PROFIT_TARGET*100}% | Stop Loss: {STOP_LOSS*100}%")

    try:
        while True:
            # 1. Fetch new tokens
            profiles = fetch_new_tokens()
            # Filter for Solana and New
            new_solana = [p for p in profiles if p['chainId'] == 'solana']

            for profile in new_solana:
                addr = profile['tokenAddress']
                if addr not in trader.seen_tokens and addr not in trader.portfolio:
                    trader.seen_tokens.add(addr)
                    # Check pair data
                    pair = get_token_pair(addr)
                    if pair:
                        liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                        
                        if liquidity > MIN_LIQUIDITY_USD:
                            # Simple logic: Buy new finding
                            print(f"{Fore.YELLOW}Found candidate: {pair['baseToken']['symbol']} | Liq: ${liquidity:.2f}")
                            # Buy with small amount (e.g., 0.5 SOL fixed)
                            trader.buy(pair, 0.5)
                        else:
                            # print(f"Skipping {pair['baseToken']['symbol']} due to low liquidity (${liquidity})")
                            pass
            
            # 2. Monitor Portfolio
            if trader.portfolio:
                # print(f"Monitoring {len(trader.portfolio)} positions...")
                # We need to refresh prices. 
                # Ideally we batch fetch, but DexScreener takes one by one or pairs. 
                # `tokens/address` returns pairs.
                
                # To avoid rate limits, we should be careful. 
                # Let's iterate.
                for addr in list(trader.portfolio.keys()): # List to allow modification during iteration
                    pair = get_token_pair(addr)
                    if pair:
                        curr_price = float(pair['priceNative'])
                        data = trader.portfolio[addr]
                        entry_price = data['entry_price']
                        
                        pct_change = (curr_price - entry_price) / entry_price

                        # Print status periodically? Maybe too noisy.
                        # print(f"  {data['symbol']}: {pct_change*100:.2f}%")

                        if pct_change >= PROFIT_TARGET:
                            trader.sell(addr, curr_price, "Take Profit")
                        elif pct_change <= STOP_LOSS:
                            trader.sell(addr, curr_price, "Stop Loss")
                    else:
                        print(f"{Fore.RED}Could not fetch update for {addr}")
            
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n{Fore.CYAN}Stopping bot...")
        print(f"Final Balance: {trader.balance:.4f} SOL")

if __name__ == "__main__":
    main()
