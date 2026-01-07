# ⚡ Solana Sniper Terminal

A professional, real-time **Solana Memecoin Trading Bot** and **Market Scanner** built with Python and Streamlit. This application allows traders to paper-trade Solana tokens using advanced "Sniper" logic, visualizing market data and trade performance in a highly responsive terminal interface.

![Dashboard Preview](https://via.placeholder.com/1200x600.png?text=Solana+Sniper+Terminal+Dashboard)

---

## 📖 What is this?

The **Solana Sniper Terminal** is an automated trading tool designed to scan the Solana blockchain for newly launched tokens. It uses the DexScreener API to fetch real-time data and evaluates tokens based on strict criteria (Liquidity, Buy Pressure, Volume).

Unlike simple scripts, this project provides a **full GUI Dashboard** where you can:
- **Scan** the market live for high-potential tokens.
- **Visualize** active trades with real-time PnL (Profit and Loss) tracking.
- **Simulate** trading strategies without risking real capital (Paper Trading Mode).
- **Manage** your risk with configurable Stop Loss and Take Profit targets.

---

## 🚀 Key Features

*   **Real-Time Market Scanner**: continuously polls for new Solana pairs.
*   **Advanced Sniper Logic**:
    *   **Buy Ratio Scoring**: Prioritizes tokens with >60% buy pressure.
    *   **Rug Protection**: Filters out low liquidity (<$2k) and "dust" transactions.
    *   **Momentum Analysis**: Tracks 1-hour price changes and volume.
*   **Professional Terminal UI**:
    *   Dark/Light mode support (Configured for specialized White Theme).
    *   Live Token Feed with icons and strength scores.
    *   Dedicated "Active Positions" tab with real-time PnL coloring (Green/Red).
*   **Persistent Data**: Uses **SQLite** to save trade history, balances, and active positions, so you never lose data on restart.
*   **Manual Wallet Management**: Simulate depositing funds to test different scaling strategies.

---

## 🛠️ How to Install

### Prerequisites
- Python 3.10 or higher.
- Git.

### Step-by-Step Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Mohammad007/solana-sniper-terminal.git
    cd solana-sniper-terminal
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    streamlit run app.py
    ```
    The functionality will open automatically in your default browser at `http://localhost:8501`.

---

## 🎮 How to Use

### 1. Configuration (Sidebar)
*   **Trade Amount**: Set how much SOL to "invest" per trade (e.g., 0.5 SOL).
*   **Take Profit**: Percentage gain to trigger an automatic sell (e.g., +20%).
*   **Stop Loss**: Percentage loss to trigger an automatic exit (e.g., -10%).
*   **Min Liquidity**: Safety filter; bot ignores tokens below this USD liquidity.
*   **Min Score**: The specific threshold (0-100) for the bot to consider a token "STRONG".

### 2. Starting the Scanner
*   Click the **▶ Start** button in the sidebar.
*   The **"Market Scanner"** tab will begin populating with live tokens found on DexScreener.
*   If a token meets your **Min Score** criteria (and other logic), the bot will automatically "buy" it.

### 3. Monitoring Trades
*   Switch to the **"Active Positions"** tab.
*   Watch your **PnL (SOL)** and **PnL %** update in real-time.
*   **Green** indicates profit, **Red** indicates loss.
*   The bot will auto-sell when your Take Profit or Stop Loss targets are hit, moving the record to **"Trade History"**.

---

## ❓ Why use this?

*   **Strategy Validation**: Before risking real money on volatile memecoins, prove your strategy works.
*   **Automation**: Humans cannot scan hundreds of tokens per minute; this bot can.
*   **Discipline**: The bot strictly follows your Stop Loss and Profit Targets, removing emotional trading.
*   **Learning**: Great for developers wanting to learn about Solana, DeFi APIs, and building financial dashboards in Python.

---

## 🏗️ Tech Stack

*   **Frontend**: [Streamlit](https://streamlit.io/) (Python web framework)
*   **Backend Logic**: Python (Pandas for data analysis)
*   **Database**: SQLite (Zero-config, serverless SQL engine)
*   **Data Source**: [DexScreener API](https://dexscreener.com/)
*   **Visualization**: Plotly & Streamlit Metrics

---

## ⚠️ Disclaimer

This is a **Paper Trading Bot** for educational and simulation purposes. It currently simulates trades and does not interact with the real Solana mainnet wallet for actual transactions. **Use at your own risk** if you decide to fork this for real trading.
