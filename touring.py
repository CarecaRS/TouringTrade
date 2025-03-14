#############################################################
#                                                           #
#             TouringTrade by Thiago Werminghoff            #
#                   (github.com/CarecaRS)                   #
#                                                           #
#  -------------------------------------------------------  #
#                                                           #
#      This is the the actual trading script. THIS ONE HERE #
# USES REAL MONEY!  It's developed for educational purposes #
# and  *MUST NOT*  be considered  investment and/or trading #
# advice.  If you should use it with  real money you are at #
# your  own risk and I'm not  responsible for any profit or #
# losses that you might incur.                              #
#      Even if  you get  favorable results  with historical #
# data (e.g. profit) it does not mean that you will get the #
# same outcome with real-time data.                         #
#      I use NeoVIM to code, so I wrote the code in  such a #
# way that it works fine for me.  You are free to change it #
# to your liking and to whatever works for you.             #
#                                                           #
#  -------------------------------------------------------  #
#                                                           #
#   I'm a brazilian guy,  so  my  dataframes  and intrinsic #
# stuff are probably always in portuguese. The printed mes- #
# sages and the  e-mails are in english.  If you find some- #
# thing that needs translation  for the proper work of this #
# script please send me a message so I can change it in the #
# original too. Thanks and have fun tweaking strategies!    #
#                                                           #
#  -------------------------------------------------------  #
#                                                           #
#    If you haven't read the backtest script yet I strongly #
# suggest you do so first, things are better explained over #
# there and I won't rewrite everything. Therefore, I assume #
# that  you  already know  how most  of this  script  works # 
# (since it is based on that one).                          #
#                                                           #
#############################################################

###
# IMPORT NEEDED PACKAGES
###
import pandas as pd  # Needed for Binance portfolio
import binance.enums  # Responsible for trading
import datetime  # Needed for asset historical data
import requests  # This too
import json  # This also
import math  # Needed for Binance orders
import time  # Needed for the script to work (time.sleep())
import pandas_ta  # Calculates indicators
from binance.client import Client  # Binance
import smtplib  # Needed for the e-mail reports
from keys import api_secret_trade, api_key_trade, email_sender, email_personal, email_pwd  # These are your infos, read the README.md if you're lost here

###
# E-MAIL NOTIFICATIONS
###

# Buy orders
def email_compra(saldos_iniciais=None, saldo_usd=None, saldo_ticker=None, preco_ticker=None, patrimonio=None, qtde=None, fatia=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparing values to send the buy order message...')
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch USDT balance
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch BTC balance
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    subject = f'Touring: buy order of {ticker[:3]}s completed!'
    body = (f"I've just completed a buy order!\n\n\
            Asset traded: {ticker[:3]}\n\
            Current asset price: US${round(preco_ticker, 2)}\n\
            Ammount that I invested: US${round(fatia, 2)}\n\
            Quantity bought: {'{:.5f}'.format(qtde)} {ticker[:3]}\n\n\
            Total invested at the moment: US${round((saldo_ticker*preco_ticker), 2)}\n\
            Total {ticker[:3]} quantity in our wallet: {'{:.5f}'.format(saldo_ticker)} {ticker[:3]}s\n\
            Total equity estimated (balance + crypto): US${round(patrimonio, 2)}\n\n\
            You can rest assured that I'll coordinate other buy/sell orders according to my parameters ;)\n\
            See ya!")
    message = (f'Subject: {subject}\n\n{body}')
    print('Sending buy order e-mail now.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')


# Sell orders
def email_venda(saldos_iniciais=None, saldo_usd=None, saldo_ticker=None, preco_ticker=None, patrimonio=None, qtde=None, fatia=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparing values to send the sell order message...')
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch USDT balance
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch BTC balance
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    subject = f'Touring: sell order of {ticker[:3]}s completed!'
    body = (f"I've just completed a sell order!\n\n\
            Asset traded: {ticker[:3]}\n\
            Current asset price: US${round(preco_ticker, 2)}\n\
            Selling price: US${round(fatia, 2)}\n\
            Ammount sold: {'{:.5f}'.format(qtde)} {ticker[:3]}\n\n\
            Total that remains invested: US${round(saldo_ticker * preco_ticker, 2)}\n\
            Total quantity of {ticker[:3]} in our wallet: {'{:.5f}'.format(saldo_ticker)} {ticker[:3]}s\n\
            Total equity estimated (balance + crypto): US${round(patrimonio, 2)}\n\n\
            You can rest assured that I'll coordinate other buy/sell orders according to my parameters ;)\n\
            See ya!")
    message = (f'Subject: {subject}\n\n{body}')
    print('Sending sell order e-mail now.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')


# Sellout orders
def email_venda_zerado(saldos_iniciais=None, saldo_usd=None, saldo_ticker=None, preco_ticker=None, patrimonio=None, qtde=None, fatia=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparing values to send the sellout order message...')
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch USDT balance
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch BTC balance
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    subject = f'Touring: {ticker[:3]} positions cleared!'
    body = (f"I just placed the last sell order of the available {ticker[:3]} balance!\n\n\
            Asset traded: {ticker[:3]}\n\
            Current asset price: US${round(preco_ticker, 2)}\n\
            Selling price: US${round(fatia, 2)}\n\
            Ammount sold: {'{:.5f}'.format(qtde)} {ticker[:3]}\n\n\
            Total equity estimated (balance + crypto): US${round(patrimonio, 2)}\n\n\
            As soon as other purchases are made I'll coordinate the following sell orders, you can rest assured ;)\n\
            See ya!")
    message = (f'Subject: {subject}\n\n{body}')
    print('Sending sell order e-mail now.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')


# Week report
def email_relatorio(temp=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    subject = "Hey boss, here is Touring! I'm bringing your weekly report :D"
    print('Preparing values to send the message...')
    semana = temp['Semana'].max()
    mask = temp['Semana'] == semana
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch USDT quantity
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch crypto quantity
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    variacoes = temp[mask]
    var_estrategia = (patrimonio/variacoes.reset_index()['PatrimonioTotal'][0])-1
    var_ativo = (preco_ticker/variacoes.reset_index()['ValorUnitario'][0])-1
    body = (f"Here I bring your weekly performance summary!\n\n\
            Total equity now: US${round(patrimonio, 2)}\n\n\
            Asset in focus: {ticker[:3]}\n\
            Strategy performance: {round(var_estrategia*100, 4)}%\n\
            Asset performance: {round(var_ativo*100, 4)}%\n\
            Trades done through the last week: {(temp.loc[mask]['CV'] == 'compra').sum()} BUY ORDERS and {(temp.loc[mask]['CV'] == 'venda').sum()} SELL ORDERS.\n\n\
            That's all for today boss! I'll be back soon with another report :D")
    message = (f'Subject: {subject}\n\n{body}')
    print('Sending e-mail now.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')


# Error in Binance systems
def carteira_off():
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    subject = f'Touring: Binance wallet unavailable!'
    body = (f"For some reason I couldn't access our Binance wallet.\n\n\
            Maybe the network gone offline and our IP has changed?\n\
            Please verify, until this is solved I'm unable to trade =/\n\n\
            I'll wait.")
    message = (f'Subject: {subject}\n\n{body}')
    print('E-mailing about impossibility...')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')


# Buy trade error
def erro_compra(qtde=None, ticker='BTCUSDT'):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    subject = f'Touring: buy order error!'
    body = (f"For some reason I couldn't buy {qtde} {ticker[:3]}s.\n\n\
            You need to check this as soon as possible, we could lose the trend.\n\n\
            I'm keeping an eye on the trends, if it's just his e-mail received and I was able to process the buy order later, that's not bad.\n\
            But it's worth taking a look at my log and also at the ledger.\n\n\
            I'll wait.")
    message = (f'Subject: {subject}\n\n{body}')
    print('=== E-mailing about buy order error ===')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')

# Sell trade error
def erro_venda(qtde=None, ticker='BTCUSDT'):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    subject = f'Touring: sell order error!'
    body = (f"For some reason I couldn't sell {qtde} {ticker[:3]}s.\n\n\
            You need to check this as soon as possible, we could lose the trend.\n\n\
            I'm keeping an eye on the trends, if it's just his e-mail received and I was able to process the buy order later, that's not bad.\n\
            But it's worth taking a look at my log and also at the ledger.\n\n\
            I'll wait.")
    message = (f'Subject: {subject}\n\n{body}')
    print('=== E-mailing about sell order error ===')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail successfully sent.')


###
# BINANCE ACCESS
###
def carteira_binance():
    cliente = Client(api_key_trade, api_secret_trade)
    if cliente.get_system_status()['msg'] != 'normal':
        print('\n\n!!!! **** WARNING **** !!!!\n')
        print('!!!! BINANCE OFFLINE !!!!\n')
        print('Unable to fetch data\n\n')
    else:
        print('\nBinance on-line. Requesting data.')
        infos = cliente.get_account()  # fetch user infos
        if infos['canTrade'] == False:
            print('\n\nWARNING! User unable to trade, please check status with Binance!')
        else:
            # Requests user wallet infos
            carteira = pd.DataFrame(infos['balances'])
            numeros = ['free', 'locked']
            carteira[numeros] = carteira[numeros].astype(float)  # transforms obj in float
            mask = carteira[numeros][carteira[numeros] > 0] \
                   .dropna(how='all').index  # assets filter
            print('Cleaning wallet... All set.')
            carteira = carteira.iloc[mask]  # keep only assets with positive balance
            black_list = ['NFT', 'SHIB', 'BTTC']  # asset blacklist
            mask = carteira[carteira['asset'].isin(black_list)].index  # blacklist index
            carteira.drop(mask, axis=0, inplace=True)  # dropping blacklist
            return carteira, cliente, infos


###
# MATH ABOUT ASSETS QUANTITY AND USDT SLICES
###
def calcula_cotas_compra():
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch values of USDT
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch asset ammount in balance
    livro_compras = pd.DataFrame(cliente.get_order_book(symbol=ticker))
    preco_ticker = float(livro_compras.loc[0]['bids'][0])
    saldoBTCemUSD = saldo_ticker*preco_ticker  # Estimates asset price in USD
    patrimonio = saldo_usd + saldoBTCemUSD  # Calculates total balance
    filtros_btc = cliente.get_symbol_info(ticker)['filters']  # Fetch asset info
    step_btc = float(filtros_btc[1]['minQty'])  # Obtains minimum asset qty to a valid order
    fatia = patrimonio/max_ordens  # Estimates each slice value, based on max_ordens
    carteira_full = max_ordens - round(saldoBTCemUSD/fatia)  # Registers maximum positions number
    qtde_btc = fatia/preco_ticker  # Calculates asset ammount for each slice value
    if saldo_usd < fatia: # Pevention in buy orders, where the balance is lower then the slice
        fatia = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fecth USDT balance
        qtde_btc = fatia/preco_ticker  # Estimates asset qty for each slice
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Round down asset qty
        qtde_btc = qtde_btc*100000
        qtde_btc = round(qtde_btc)
        qtde_btc = qtde_btc/100000
    else:
        qtde_btc = fatia/preco_ticker  # Calculates asset ammount for each slice
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Round down asset qty
        qtde_btc = qtde_btc*100000  # The above rounding may have error in the 10th decimal...
        qtde_btc = round(qtde_btc)  # ...so it performs a new rounding
        qtde_btc = qtde_btc/100000
    return qtde_btc, fatia

def calcula_cotas_venda():
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch USDT values
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch asset ammount in balance
    livro_compras = pd.DataFrame(cliente.get_order_book(symbol=ticker))
    preco_ticker = float(livro_compras.loc[0]['bids'][0])
    saldoBTCemUSD = saldo_ticker*preco_ticker  # Asset pricing
    patrimonio = saldo_usd + saldoBTCemUSD  # Estimates whole balance
    filtros_btc = cliente.get_symbol_info(ticker)['filters']  # Fetch asset info
    step_btc = float(filtros_btc[1]['minQty'])  # Obtains minimum asset qty to a valid order
    fatia = patrimonio/max_ordens  # Estimates each slice value, based on max_ordens
    carteira_full = max_ordens - round(saldoBTCemUSD/fatia)  # Registers maximum positions possible
    qtde_btc = fatia/preco_ticker  # Estimates asset qty for each slice
    if carteira[carteira['asset'] == ticker[:3]]['free'].sum() < saldo_ticker: # Prevention in sell orders, where qtde_btc is lower then the balance
        qtde_btc = saldo_ticker
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Round down procedures again
        qtde_btc = qtde_btc*100000
        qtde_btc = round(qtde_btc)
        qtde_btc = qtde_btc/100000
    else:
        qtde_btc = fatia/preco_ticker  # Estimates each slice value
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Round down procedures once more
        qtde_btc = qtde_btc*100000
        qtde_btc = round(qtde_btc)
        qtde_btc = qtde_btc/100000
    return qtde_btc, fatia


###
# HISTORICAL DATA
###
def valores_historicos(ticker='BTCUSDT', dias=30, intervalo='5m'):
    if dias < 3:
        print('\n\n\n\n*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
        print('WARINNG! The time span in days must be >= 3! This data WILL NOT WORK!\n\n')
        print('*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
    else:
        pass
    # Defining time horizon for the historical data
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=dias)
    # Converts time to Unix (because Binance) in miliseconds
    end_timestamp = int(end_time.timestamp()*1000)
    start_timestamp = int(start_time.timestamp()*1000)
    # Time window ok, request data to Binance
    # Binance endpoint
    endpoint = 'https://api.binance.com/api/v3/klines'
    # Requisition parameters
    tickers = ticker
    interval = intervalo  # other time frames in https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    limit = 1000
    params = {'symbol': tickers, 'interval': interval,
              'endTime': end_timestamp, 'limit': limit,
              'startTime': start_timestamp}
    print('Requesting infos to Binance...')
    # Performs the request and saves in a list
    dados = []
    while True:
        response = requests.get(endpoint, params=params)
        klines = json.loads(response.text)
        dados += klines
        if len(klines) < limit:
            break
        params['startTime'] = int(klines[-1][0])+1
        time.sleep(0.1)
    print('Information request successfull. Processing dataframe data...')
    # Creates a dataframe with OHLC and timestamps
    # About kline[n] positions: https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])] for kline in dados]
    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close'])
    timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in dados]
    historico['timestamp'] = timestamps
    historico.set_index('timestamp', inplace=True)
    historico['par'] = tickers
    print('Data request completed.')
    return historico


###
# BUY ORDER
###
def ordem_compra(ticker=None, quantity=None):
    cliente.order_market_buy(symbol=ticker,
                             quantity=f'{quantity:.5f}')


###
# SELL ORDER
###
def ordem_venda(ticker=None, quantity=None):
    cliente.order_market_sell(symbol=ticker,
                             quantity=f'{quantity:.5f}')


###
# INDICATORS
###
def adiciona_indicadores(df, periodo=4):  # With 15min timeframes, 4 periods (periodo) of time equals 1 hour
# RSI
    df['rsi'] = pandas_ta.rsi(close=df['close'], length=periodo)
# Moving Average SHORT
    df['mmCurta'] = pandas_ta.sma(df['close'], length=periodo/4)
# Moving Average INTERMEDIATE 
    df['mmMedia'] = pandas_ta.sma(df['close'], length=periodo*30)
# Moving Average LONG
    df['mmLonga'] = pandas_ta.sma(df['close'], length=periodo*60)


###
# BUY/SELL STRATEGY
###
def estrategia_bitcoin(df=None, defasagem=6):
    # Defaults:
    # defasagem = 6 -- 15min timespans, '6' then equals to 1h30min
    compra = []
    venda = []
    # Generates buy signals
    for idx in df.index:
        pm1h = ((df.loc[idx-4:idx]['low'] + df.loc[idx-4:idx]['high'])/2).mean()
        pm2h = ((df.loc[idx-8:idx]['low'] + df.loc[idx-8:idx]['high'])/2).mean()
        pm3h = ((df.loc[idx-12:idx]['low'] + df.loc[idx-12:idx]['high'])/2).mean()
        if idx >= defasagem:
            # If closing price is going down for the last hour inhibits buy orders
            if ((df.loc[idx-4, 'open'] > df.loc[idx-3, 'open']) &
                    (df.loc[idx-3, 'open'] > df.loc[idx-2, 'open']) &
                    (df.loc[idx-2, 'open'] > df.loc[idx-1, 'open']) &
                    (df.loc[idx-1, 'open'] > df.loc[idx, 'open']) &
                    (df.loc[idx, 'mmLonga'] > df.loc[idx, 'mmCurta'])):
                compra.append(False)
            # If the average price is going down in the last three hours inhibits buy orders
            elif (pm3h > pm2h) & (pm2h > pm1h) & (pm1h > df.loc[idx, 'open']):
                compra.append(False)
            else:
                # If last closing price is lesser or iqual the lowest of the 'defasagem' periods
                # (meaning it keeps going down), inhibits buy orders
                if (df.loc[idx-1, 'close'] <= df.loc[idx-defasagem:idx-1, 'close'].min()):
                    compra.append(False)
                else:
                    # Once the checking above is ok, if the last high is lower then the current
                    # high AND ALSO the short MA is higher then the long MA, signals buy
                    compra.append((df.loc[(idx-1), 'high'] < df.loc[idx, 'high']) &
                                  (df.loc[idx, 'mmCurta'] > df.loc[idx, 'mmLonga']))
        else:
            if idx >= 2:
                # If the last high is lower then the current high AND ALSO the short MA is
                # higher then the long MA, signals buy
                compra.append((df.loc[(idx-1), 'high'] < df.loc[idx, 'high']) &
                              (df.loc[idx, 'mmCurta'] > df.loc[idx, 'mmLonga']))
            else:
                # Any other status, signals `non-buy`
                compra.append(False)
    # Generates sell signals
    for idx in df.index:
        if idx >= defasagem:
            # If closing price is going down for the last hour and also
            # the short MA is below open price, signals a sell
            if((df.loc[idx-4, 'close'] > df.loc[idx-3, 'close']) &
                    (df.loc[idx-3, 'close'] > df.loc[idx-2, 'close']) &
                    (df.loc[idx-2, 'close'] > df.loc[idx-1, 'close']) &
                    (df.loc[idx, 'open'] > df.loc[idx-1, 'mmCurta'])):
                venda.append(True)
            else:
                # Else, signals `non-sell`
                venda.append(False)
        elif idx < defasagem:
            if idx < 1:
                # The very start of the timeseries is negligible, signals 'non-sell'
                venda.append(False)
            elif df.loc[idx, 'open'] < df.loc[idx-1, 'mmCurta']:
                # If opening price is lower then the short MA from the previous period, signals a sell
                venda.append(True)
            else:
                # Any other status, doesn't decides over anything, so registers a 'non-sell'
                venda.append(False)
        else:
            # If perhaps something else comes up (which I think it's extremely unlikely), returns the error below
            print("Something very weird happened, this print isn't suppose to happen!")
    # Create and record neutral, buy and sell signals:
    df['sinal_est'] = 0  # Neutral signals througout the dataframe
    df.loc[compra, 'sinal_est'] = 1  # Records existing buy signals
    df.loc[venda, 'sinal_est'] = -1  # Records existing sell signals


###
# TOURING ITSELF
###
def touring(max_ordens=3, compra=None, venda=None, ticker=None):
    marcador = 1  # For ledger control, also helps balance clearing
    print('\nWaiting the right time for first iteration...\n')
    while cliente.get_system_status()['msg'] == 'normal':
        # Waits until time is multiple of 15min
        while (datetime.datetime.now().strftime('%M:%S') in ('15:00', '30:00', '45:00', '00:00')) == False:
            time.sleep(1)
        else:
            # Check the presence of a ledger file.
            # If a file 'livro_contabil.csv' does not exist in this scripts directory
            # then Touring will generate one at the first trade
            try:
                ledger = pd.read_csv('livro_contabil.csv')
                ledger = ledger.to_dict(orient='records')
            except:
                ledger = []
            # Checks Binance status
            print('Time checkpoint, verifying...')
            print('Binance online, performing new trading analysis.\n')
            historico = valores_historicos(dias=3)  # fetch historical data
            adiciona_indicadores(historico)  # adds indicators
            print('Removing NaNs e resetting index...')
            historico = historico.dropna()
            historico = historico.reset_index()  # cleans df and resets index
            estrategia_bitcoin(historico)  # generate buy/sell signals based on strategy
            # Fetch inicial balances and performs basic calculations for proper work of this function
            saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Fetch USDT balance
            saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Fetch asset balance
            livro_compras = pd.DataFrame(cliente.get_order_book(symbol=ticker))  # Reads order book
            preco_ticker = float(livro_compras.loc[0]['bids'][0])  # Uses order book pricing as reference
            saldoBTCemUSD = saldo_ticker * preco_ticker  # Asset pricing in USDT
            patrimonio = saldo_usd + saldoBTCemUSD  # Estimates total balance (asset + USDT)
            filtros_btc = cliente.get_symbol_info(ticker)['filters']  # Fetches asset infos
            step_btc = float(filtros_btc[1]['minQty'])  # Reads minimym asset qty for any given valid order
            fatia = patrimonio/max_ordens  # Estimates each slice value
            carteira_full = max_ordens - round(saldoBTCemUSD/fatia)  # Estimates how many slices is possible at the moment
            qtde = fatia/preco_ticker  # Estimates asset qty for each slice
            qtde = math.floor(qtde/step_btc)*step_btc  # Round down
            # If balance is full of asset, redo the slice calculation
            # or else goes straight to signal analysis
            if carteira_full == max_ordens:
                fatia = saldos_iniciais['USD']/carteira_full
            else:
                pass
            # Weekly report, if week has changed (sunday -> monday)
            ledger_temp = pd.DataFrame(ledger)
            if len(ledger_temp) <= 2:
                pass
            else:
                if (((datetime.datetime.now().isocalendar()[1] - ledger_temp.loc[ledger_temp.shape[0]-1, 'Semana']) != 0) & (ledger_temp.iloc[-1]['Mail'] == 0)):
                    try:
                        print('\nThe week has changed - emailing weekly report to the registered e-mail.\n')
                        ledger_temp = pd.DataFrame(ledger)
                        ledger_temp.loc[(len(ledger_temp)-1), 'Mail'] = 1
                        pd.DataFrame(data=ledger_temp).to_csv('livro_contabil.csv', index=False)
                        email_relatorio(temp=ledger_temp)
                    except:
                        print('ERROR: Unable to sent weekly report. Please verify.')
                else:
                    pass
            # BUY ORDERS PROCESSING
            if historico.loc[(historico.shape[0]-1), 'sinal_est'] == 1:  # Buy signals from the strategy
            # Check USDT balance. If it's empty, there's nothing to buy with, so doesn't bother to check buy signals.
            # If there's USDT balance in full again, redo slice values
                if carteira_full == 0:
                    print(f'\nLast check: {datetime.datetime.now().strftime('%H:%M:%S on %d/%m')}')
                    print(f'   --> Buy signal, but without resources to buy anything.\n\n')
                    pass
                else:
                    if carteira_full == max_ordens:
                        marcador += 1
                    else:
                        pass
                    # If USDT balance is equals or higher then the slice value, just follows the script
                    try:
                        qtde, fatia = calcula_cotas_compra()
                        cv = 'compra'
                        ordem_compra(ticker=ticker, quantity=qtde)
                        # Records in ledger
                        ledger.append({'Date': datetime.datetime.now(),
                                       'Week': datetime.datetime.now().isocalendar()[1],
                                       'Asset': ticker[:3],
                                       'CV(c=buy/v=sell)': cv,
                                       'Marker': marcador,
                                       'UnitValue': round(preco_ticker, 2),
                                       'Qty': '{:.5f}'.format(qtde),
                                       'TradePrice': round(fatia, 2),
                                       'TotalBalance': round(patrimonio, 2),
                                       'Mail': 0})
                            # Reports buy order to e-mail
                            email_compra(saldos_iniciais=saldos_iniciais,
                                         saldo_usd=saldo_usd,
                                         saldo_ticker=saldo_ticker,
                                         preco_ticker=preco_ticker,
                                         patrimonio=patrimonio,
                                         qtde=qtde,
                                         fatia=fatia)
                        print(f'\nLast check: {datetime.datetime.now().strftime("%H:%M:%S on %d/%m")}')
                        print(f'   --> Buy order of US${round(fatia, 2)} ammounting {'{:.5f}'.format(qtde)} {ticker[:3]+'s'} completed!\n\n')
                        # Records local ledger
                        pd.DataFrame(data=ledger).to_csv('livro_contabil.csv', index=False)
                        print(f'Waiting next cycle...\n\n')
                    except:
                        erro_compra(qtde=qtde, ticker=ticker)
            # SELL ORDERS PROCESSING
            elif historico.loc[(historico.shape[0]-1), 'sinal_est'] == -1:  # Sell signals from strategy
                if carteira_full == max_ordens:  # If balance is just USDT, there's nothing to sell
                    pass
                else:
                    # If asset qty is at least equal a slice, just follows along
                    try:
                        qtde, fatia = calcula_cotas_venda()
                        cv = 'venda'
                        ordem_venda(ticker=ticker, quantity=qtde)
                        print(f'\nLast check: {datetime.datetime.now().strftime("%H:%M:%S on %d/%m")}')
                        print(f'   --> Sell order of {'{:.5f}'.format(qtde)} {ticker[:3]+'s'} completed, ammounting US${round(fatia, 2)}.\n\n')
                        carteira_full += 1
                        # Records in ledger
                        ledger.append({'Date': datetime.datetime.now(),
                                       'Week': datetime.datetime.now().isocalendar()[1],
                                       'Asset': ticker[:3],
                                       'CV(c=buy/v=sell)': cv,
                                       'Marker': marcador,
                                       'UnitValue': round(preco_ticker, 2),
                                       'Qty': '{:.5f}'.format(qtde),
                                       'TradePrice': round(fatia, 2),
                                       'TotalBalance': round(patrimonio, 2),
                                       'Mail': 0})
                        # Reports sell order to e-mail
                        if carteira_full == 0:
                            print(f'\n\nLast check: {datetime.datetime.now().strftime("%H:%M:%S on %d/%m")}')
                            print('   --> ***  Positions cleared!  ***\n\n')
                            email_venda_zerado(saldos_iniciais=saldos_iniciais,
                                               saldo_usd=saldo_usd,
                                               saldo_ticker=saldo_ticker,
                                               preco_ticker=preco_ticker,
                                               patrimonio=patrimonio,
                                               qtde=qtde,
                                               fatia=fatia)
                        else:
                            email_venda(saldos_iniciais=saldos_iniciais,
                                        saldo_usd=saldo_usd,
                                        saldo_ticker=saldo_ticker,
                                        preco_ticker=preco_ticker,
                                        patrimonio=patrimonio,
                                        qtde=qtde,
                                        fatia=fatia)
                        # Records local ledger
                        pd.DataFrame(data=ledger).to_csv('livro_contabil.csv', index=False)
                        print(f'Waiting for next cycle...\n\n')
                    except:
                        erro_venda(qtde=qtde, ticker=ticker)
            else:
                print(f'\nLast check: {datetime.datetime.now().strftime("%H:%M:%S on %d/%m")}')
                print(f'   --> Strategy with no buy/sell signals, or with no resources to buy. Waiting.\n\n')
                pass
    # If Binance system returns anything but 'normal':
    else:
        # Prints warnings on console
        print('\n\n!!!! **** WARNING **** !!!!\n')
        print('!!!! BINANCE OFFLINE !!!!\n')
        print("I'm unable to keep working here, boss.\n\n")
        # Records status and reports to email
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        subject = '*Touring offline*'
        print('Preparing e-mail.')
        body = (f"Binance returned ABNORMAL status\n\n\
                As I'm unable to get back to my activities, I stopped working.\n\n\
                As soon as possible please reactivate me again, so I can keep my eye on those cryptos.\n\
                Remember: if I'm not working I can't even send your weekly reports.\n\n\
                Best wishes, and I hope to get back to work soon :D")
        message = (f'Subject: {subject}\n\n{body}')
        # Sends e-mail
        print('Sending e-mail now.')
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(email_personal, email_pwd)
            smtp.sendmail(email_sender, email_personal, message)
        print('E-mail successfully sent.')  # final do protocolo de envio de e-mail quando Binance der erro


######################################
#                                    #
#            Trading Area            #
#                                    #
######################################

# Checks the access to Binance wallet. Very important whenever it's running
# from some place other than your own PC/laptop. If something happens and
# Touring can't get access, it warns you through e-mail.
try:
    carteira, cliente, infos = carteira_binance()
except:
    print('ERROR: Unable to connect to Binance.')
    print('Please verify.\n')
    carteira_off()
    print('\n\nAborting.')

ticker = 'BTCUSDT'  # In here, BTC is bought using USDT. More info in this trading pairs over Binance.
max_ordens = 2
#
touring(max_ordens=max_ordens, ticker=ticker)
