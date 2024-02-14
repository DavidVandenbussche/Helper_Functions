import time
import pandas as pd
from ta.momentum import *
import ccxt
from dontshareconfig import API_KEY, SECRET_KEY


if __name__ == "__main__":
    phemex = ccxt.phemex({
        'enableRateLimit': True,
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
    })
    phemex.set_sandbox_mode(True)
symbol = "ETHUSD"
size = 1
# bid = 50000
params = {'timeInForce' : 'PostOnly'} # to create limit orders only


###################### Risk management functions

# open_positions[0], openpos_bool[1], openpos_size[2], long[3], index_pos[4]
def open_positions(symbol = symbol):
    # look for the index position of that symbol:
    if symbol == 'BTCUSDT':
        index_pos = 4
    # elif ...
    else:
        index_pos = None
    
    params = {'type': 'swap', 'code': 'USD'} # specific to phemex exchange because we use the contract and it trades USD
    phe_bal = phemex.fetch_balance(params=params)
    open_positions = phe_bal['info']['data']['positions'] # check my positions

    # everything is in dictionaries
    openpos_side = open_positions[index_pos]['side']
    openpos_size = open_positions[index_pos]['size'] # e.g., btc is 4

    if openpos_side == ('Buy'):
        openpos_bool = True
        long = True
    elif openpos_side == ('Sell'):
        openpos_bool = True
        long = False
    else:
        openpos_bool = False
        long = None

    print(f'open_positions {open_positions} |  openpos_bool {openpos_bool}  | openpos_size {openpos_size}  |  long {long}  |  index_pos {index_pos}' )
    
    return open_positions, openpos_bool, openpos_size, long, index_pos

# ask_bid[0] = ask, [1] = bid
def ask_bid(symbol=symbol):

    ob = phemex.fetch_order_book(symbol)

    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    return ask, bid

# the kill switch, takes me out of the position
def kill_switch(symbol = symbol):

    print(f"starting the kill switch for {symbol}")
    openposi = open_positions(symbol)[1] # true or false
    long = open_positions(symbol)[3] # boolean
    kill_size = open_positions(symbol)[2]
    
    print(f'openposi {openposi} | long {long} | kill_size {kill_size}')

    while openposi == True:

        print('starting kill switch loop until limit filled')
        temp_df = pd.DataFrame()
        print('made a temp df')

        phemex.cancel_all_orders(symbol)
        openposi = open_positions(symbol)[1] # true or false
        long = open_positions(symbol)[3] # boolean
        kill_size = open_positions(symbol)[2] # set kill size to actual open size
        kill_size = int(kill_size) # making sure we closed the right number of positions that was filled

        # want to get out quickly but not paying too much, ie set orders at the ask/bid orders
        ask = ask_bid(symbol)[0]
        bid = ask_bid(symbol)[1]

        if long == False:
            phemex.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f'just made a BUY to CLOSE order of {kill_size} {symbol}')
            print('sleeping for 30s to see if it fills')
            time.sleep(30)
        elif long == False:
            phemex.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f'just made a SELL to CLOSE order of {kill_size} {symbol}')
            print('sleeping for 30s to see if it fills')
            time.sleep(30)
        else:
            print('++++++++++++++++++++++++++++ something I did not expect in kill switch')

        openposi = open_positions(symbol)[1]

# TEST VALUES
target = 3 # in %
max_loss = -5 # in %

# the pnlclose function, executed at each loop to know if we're in a losing or winning position
def pnl_close(symbol=symbol, target = target, max_loss = max_loss):

    print(f'checking to see if it is time to exit for {symbol}')
    params = {'type': 'swap', 'code': 'USD'} 
    pos_dict = phemex.fetch_positions(params = params)

    index_pos = open_positions(symbol)[4]
    pos_dict = pos_dict(index_pos)
    side = pos_dict['side']
    size = pos_dict['contracts']
    entry_price = float(pos_dict['entryPrice'])
    leverage = float(pos_dict['leverage'])

    current_price = ask_bid(symbol)[1]

    print(f'side: {side} | entry_price {entry_price} | leverage {leverage}')
    # compute difference based on position

    if side == 'long':
        diff = current_price - entry_price
        long = True
    else:
        diff = entry_price - current_price
        long = False

    try:
        perc = round(((diff/entry_price) * leverage), 10) * 100
    except:
        perc = 0

    print(f'for {symbol} this is our PnL percentage: {perc}%')

    pnlclose = False
    in_pos = False

    if perc > 0:
        in_pos = True
        print(f' for {symbol} we are in a winning position')
        if perc >= target:
            print(' we made a profit!')
            pnlclose = True
            kill_switch(symbol)
        else:
            print(f'we have not hit the target')

    elif perc < 0:

        in_pos = True
        if perc <= max_loss:
            print(f'we are exiting now because losing position of {perc}%')
            kill_switch(symbol)
        else:
            print(f'we are in a losing position of {perc}% but still under max_loss')

    else:
        print('we are not in position')

    # can use in_pos in certain algos
        
    print(f' for {symbol} just finished checking PnL close')

    return pnlclose, in_pos, size, long

# the size kill function to check if we're still entering positions under the max_risk value
def size_kill(symbol=symbol):



    max_risk = 10 # dollars

    params = {'type': 'swap', 'code': 'USD'} 
    phem_bal = phemex.fetch_balance(params = params)
    open_positions = phem_bal['info']['data']['positions']

    try:
        pos_cost = float(open_positions[0]('posCost'))
        openpos_side = open_positions[0]['side']
        openpos_size = open_positions[0]['size']
    except:
        pos_cost = 0
        openpos_side = 0
        openpos_size = 0
    print(f'positioncost: {pos_cost}')
    print(f'openpos_side {openpos_side}')

    if pos_cost > max_risk:
        print(f'EXIT KILL SWITCH we reached the maximum risk allowed due to current pos at {pos_cost}')
        kill_switch(symbol)
        time.sleep(30000)

    else:
        print(f'size kill check: current position is {pos_cost} still ok compared to {max_risk}')


############ Now coding Indicators

##### SMA INDICATOR
# RANDOM VALUES
timeframe = '15m'
limit = 100 # number of bars
sma = 20 # last 20 periods
def df_sma(symbol=symbol, timeframe=timeframe, limit=limit, sma = sma):

    print('starting indicator')
    bars = phemex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    # getting data
    df_sma = pd.DataFrame(bars, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma['timestamp'] = pd.to_datetime(df_sma['timestamp'], unit='ms')

    # computing SMA
    df_sma[(f'sma{sma}_{timeframe}')] = df_sma.close.rolling(sma).mean()

    # simple way to use it
    # if bid is < sma20 then bearish ie we want to sell, else bullish we want to buy
    bid = ask_bid(symbol)[1]
    df_sma.loc[df_sma[f'sma{sma}_{timeframe}'] > bid, 'sig'] = 'SELL'
    df_sma.loc[df_sma[f'sma{sma}_{timeframe}'] < bid, 'sig'] = 'BUY'

    # print(df_sma)
    return df_sma

##### RSI INDICATOR
'''Compares the magnitude of recent gains and losses over a specified 
time period to measure speed and change of price movements of a security. 
It is primarily used to attempt to identify overbought or oversold conditions 
in the trading of an asset.'''
def df_rsi(symbol=symbol, timeframe=timeframe, limit=limit):
    print('starting rsi indicator')
    bars = phemex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df_rsi = pd.DataFrame(bars, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_rsi['timestamp'] = pd.to_datetime(df_rsi['timestamp'], unit='ms')

    bid = ask_bid(symbol)[1]

    #RSI
    rsi = RSIIndicator(df_rsi['close'])
    df_rsi['rsi'] = rsi.rsi()

    # print(df_rsi)

    return df_rsi

##### VWAP INDICATOR
'''useful to determine where the price "should" be.
VWAP serves as a reference point for prices for one day.As such, it is best suited for 
intraday analysis. Volume-Weighted Average Price (VWAP) is exactly what it sounds like: 
the average price weighted by volume. VWAP equals the dollar
value of all trading periods divided by the total trading volume for the current day. The 
calculation starts when trading opens and ends when it closes. Because it is good for the 
current trading day only, intraday periods and data are used in the calculation.'''
# get dataframe function, really useful?
def get_df_vwap():
    bars = phemex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df_vwap = pd.DataFrame(bars, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_vwap['timestamp'] = pd.to_datetime(df_vwap['timestamp'], unit='ms')

    low = df_vwap['low'].min()
    high = df_vwap['high'].max()
    diff = high-low
    avg = (high + low)/2

    return df_vwap

def df_vwap():
    print('starting the vwap indicator')
    df_vwap = get_df_vwap()

    df_vwap['volXclose'] = df_vwap['volume'] * df_vwap['close']
    df_vwap['cum_volume'] = df_vwap['volume'].cumsum()
    # cum sum with typical price
    df_vwap['cumsum_volXclose'] = (df_vwap['volume'] * (df_vwap['high'] + df_vwap['low']
                                                         + df_vwap['close'])/3).cumsum()
    df_vwap['VWAP'] = df_vwap['cumsum_volXclose'] / df_vwap['cum_volume']
    df_vwap = df_vwap.fillna(0)

    # print(df_vwap)
    return df_vwap

##### VWMA INDICATOR
def get_df_vwma():
    bars = phemex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df_vwma = pd.DataFrame(bars, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_vwma['timestamp'] = pd.to_datetime(df_vwma['timestamp'], unit='ms')
    return df_vwma

def vwma_indic():
    df_vwma = get_df_vwma()

    # Calculate SMAs
    df_vwma['SMA(41)'] = df_vwma.close.rolling(41).mean()
    df_vwma['SMA(20)'] = df_vwma.close.rolling(20).mean()
    df_vwma['SMA(75)'] = df_vwma.close.rolling(75).mean()

    vwmas = [20, 41, 75]
    for vwma in vwmas:
        sum_vol_column = f'sum_vol{vwma}'
        vXc_column = f'vXc{vwma}'
        vwma_column = f'VWMA({vwma})'

        # Calculate volume sums and volume*close sums for VWMA
        df_vwma[sum_vol_column] = df_vwma['volume'].rolling(window=vwma).sum()
        df_vwma['volXclose'] = df_vwma['volume'] * df_vwma['close']
        df_vwma[vXc_column] = df_vwma['volXclose'].rolling(window=vwma).sum()
        df_vwma[vwma_column] = df_vwma[vXc_column] / df_vwma[sum_vol_column]

        # Generate signals based on VWMA and SMA comparison
        for sma_period in [20, 41, 75]:
            sma_column = f'SMA({sma_period})'
            signal_buy_column = f'{sma_period}sig{vwma}_BUY'
            signal_sell_column = f'{sma_period}sig{vwma}_SELL'

            df_vwma.loc[df_vwma[vwma_column] > df_vwma[sma_column], signal_buy_column] = 'BUY'
            df_vwma.loc[df_vwma[vwma_column] < df_vwma[sma_column], signal_sell_column] = 'SELL'

    print(df_vwma)
    return df_vwma


# vwma_indic()