# Crypto Trading Bot Helper Functions

This repository contains helpful functions for implementing a crypto trading bot. These functions are designed to facilitate risk management, position monitoring, and indicator computation in your trading algorithm.

## Getting Started

These instructions will guide you on how to use the provided functions in your trading bot.

### Prerequisites

Before using the functions, make sure you have the following dependencies installed:

- Python 3.x
- pandas
- ccxt
- ta (Technical Analysis Library)

You can install the required packages using pip:

```
pip install pandas ccxt ta
```

### Installation

1. Clone this repository to your local machine
```
git clone <repository_url>
```


2. Ensure that you have your API keys for the relevant exchange ready.

3. Import the required functions into your trading bot script.

## Functions

### Risk Management Functions

- `open_positions(symbol)`: Retrieves information about open positions for a given symbol.
- `ask_bid(symbol)`: Retrieves the current ask and bid prices for a given symbol.
- `kill_switch(symbol)`: Implements a kill switch to exit a position.
- `pnl_close(symbol, target, max_loss)`: Checks if it is time to exit a position based on profit/loss percentages.
- `size_kill(symbol)`: Checks if new positions should be opened based on maximum risk limits.

### Indicators

#### SMA Indicator

- `df_sma(symbol, timeframe, limit, sma)`: Computes the Simple Moving Average (SMA) indicator for a given symbol.

#### RSI Indicator

- `df_rsi(symbol, timeframe, limit)`: Computes the Relative Strength Index (RSI) indicator for a given symbol.

#### VWAP Indicator

- `df_vwap(symbol, timeframe, limit)`: Computes the Volume Weighted Average Price (VWAP) indicator for a given symbol.

#### VWMA Indicator

- `vwma_indic(symbol, timeframe, limit)`: Computes the Volume Weighted Moving Average (VWMA) indicator for a given symbol.

## Usage

1. Import the required functions into your trading bot script.
2. Use these functions within your trading algorithm to manage risk, monitor positions, and compute indicators.

```python
import time
import pandas as pd
from ta.momentum import *
import ccxt
from dontshareconfig import API_KEY, SECRET_KEY

# Import functions from the provided code
from trading_functions import *
```
