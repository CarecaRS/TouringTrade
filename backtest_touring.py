#############################################################
#                                                           #
#      TouringTrade by CarecaRS (github.com/CarecaRS)       #
#                                                           #
#  -------------------------------------------------------  #
#                                                           #
#   This is the backtest script, it does not trade real mo- #
# ney.  I use NeoVIM to code,  so I made the code in such a #
# way that it works fine for me.  You are free to change it #
# for your liking and for whatever works for you.           #
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
#############################################################

###
# IMPORT NEEDED PACKAGES
###
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
import datetime
import requests
import math
import json
import time
import pandas_ta
from binance.client import Client
import smtplib
from keys import api_secret_backtest, api_key_backtest, email_sender, email_personal, email_pwd
%autoindent OFF # NeoVIM stuff, you can safely erase/comment it

###
# BINANCE ACCESS AND INFO FUNCTION
###
def carteira_binance():
    cliente = Client(api_key_backtest, api_secret_backtest)
    print('Requesting information from Binance')
    infos = cliente.get_account()  # load userr info
    # Fetch user's wallet info
    carteira = pd.DataFrame(infos['balances'])
    numeros = ['free', 'locked']
    carteira[numeros] = carteira[numeros].astype(float)  # transforms obj in float
    mask = carteira[numeros][carteira[numeros] > 0] \
            .dropna(how='all').index  # filter assets with balance
    print('Limpeza geral da carteira')
    carteira = carteira.iloc[mask]  # keeps only the assets with balance
    black_list = ['NFT', 'SHIB', 'BTTC']  # asset blacklist
    mask = carteira[carteira['asset'].isin(black_list)].index  # blacklist indexing
    carteira.drop(mask, axis=0, inplace=True)  # filters out blacklisted assets
    print('Wallet successfully obtained. Current assets and balances:')
    return carteira, cliente


###
# ASSETS HISTORIC DATA FUNCTION
###
def valores_historicos(ticker='BTCUSDT', dias=30, intervalo='15m'):  # the ticker in Binance works in pairs - here you'll want to know how much is BTC worth in USDT, for example
    if dias < 8:
        print('\n\n\n\n*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
        print('IMPORTANT! Days ammount has to be 8 or more! This history WILL NOT WORK!\n\n')
        print('*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
    else:
        pass
    # Defines data timespan
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=dias)
    # Converts time to Unix (because Binance) in miliseconds
    end_timestamp = int(end_time.timestamp()*1000)
    start_timestamp = int(start_time.timestamp()*1000)
    # Timewindow estabilished, requests historic data
    # Endpoint da Binance
    endpoint = 'https://api.binance.com/api/v3/klines'
    # Requisition parameters
    tickers = ticker 
    interval = intervalo  # other timeframes are possible, check in https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    limit = 1000
    params = {'symbol': tickers, 'interval': interval,
          'endTime': end_timestamp, 'limit': limit,
          'startTime': start_timestamp}
    print('Fazendo a requisição das informações à Binance...')
    # Make the request and records it in a list
    dados = []
    while True:
        response = requests.get(endpoint, params=params)
        klines = json.loads(response.text)
        dados += klines
        if len(klines) < limit:
            break
        params['startTime'] = int(klines[-1][0])+1
        time.sleep(0.1)
    print('Informações obtidas com sucesso. Configurando os dados do dataframe...')
    # Creates a dataframe with OHLC e timestamps
    # About kline[n] pos: https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])] for kline in dados]
    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close'])
    timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in dados]
    historico['timestamp'] = timestamps
    historico.set_index('timestamp', inplace=True)
    historico['par'] = tickers
    print('Data request done.')
    return historico


###
# INDICATORS FUNCTION
# - The commented ones are not in use per my last strategy
###
    def adiciona_indicadores(df, periodo=12):  # 'periodo' translates roughly as 'timeframe' here, so '12' equals one hour (5min periods)
# Garman-Klass Volatility
    print('Running VOLATILITY indicators:')
    print('       Garman-Klass Volatility not estimated')
#    df['garman_klauss_vol'] = (((np.log(df['high']) - np.log(df['low']))**2)/2) - (2*np.log(2)-1) * ((np.log(df['close']) - np.log(df['open']))**2)
# Bollinger Bands (VOLATILITY)
    print('       Bollinger Bands not estimated')
#    df['bb_low'] = pandas_ta.bbands(close=np.log1p(df['close']),
#                                    length=periodo).iloc[:, 0]
#    df['bb_mid'] = pandas_ta.bbands(close=np.log1p(df['close']),
#                                    length=periodo).iloc[:, 1]
#    df['bb_high'] = pandas_ta.bbands(close=np.log1p(df['close']),
#                                     length=periodo).iloc[:, 2]
# Average True Range (ATR) (VOLATILITY)
    print('       Average True Range (ATR) not estimated')
#    atr = pandas_ta.atr(high=df['high'], low=df['low'],
#                        close=df['close'], length=periodo)
#    df['atr'] = atr.sub(atr.mean()).div(atr.std())
# ROC (VOLATILITY)
    print('       ROC not estimated')
#    df['roc'] = pandas_ta.roc(df['close'], length=2)
# RSI (TENDENCY)
    print('Running TENDENCY indicators:')
    print('       RSI')
    df['rsi'] = pandas_ta.rsi(close=df['close'], length=periodo)
# MACD (TENDENCY)
    print('       MACD (original, normalized and signal) not estimated')
#    macd = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
#    df['macd'] = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
#    df['macd_norm'] = macd.sub(macd.mean()).div(macd.std())
#    df['macd_s'] = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 2]
# Moving Average SHORT (TENDENCY)
    print('       Moving Average (short)')
    df['mmCurta'] = pandas_ta.sma(df['close'], length=periodo/4)
# Moving Average INTERMEDIARY (TENDENCY)
    print('       Moving Average (intermediary)')
    df['mmMedia'] = pandas_ta.sma(df['close'], length=periodo*30)
# Moving Average LONG (TENDENCY)
    print('       Moving Average (long)')
    df['mmLonga'] = pandas_ta.sma(df['close'], length=periodo*60)
# Supertrend (TENDENCY)
    print('       Supertrend not estimated')
#    df['supertrend'] = pandas_ta.supertrend(high=df['high'],
#                                            low=df['low'],
#                                            close=df['close'],
#                                            offset=1)['SUPERTd_7_3.0']
#
    print('Successfully added information to dataframe. Manally remove NaNs.')


###
# BACKTEST FUNCTION
###

# This is the backbone of the whole script. I use a logic in which the bot uses 'slices' of capital
# to organize its process of buying and selling assets.
# Its parameters are as follows:
#   max_ordens  = indirectly defines the amount of capital to be bought or sold at a given time,
#                 just divide the total capital with this number and that's how much it will buy/sell
#   saldo_inicial = initial balance for the calculation
#   compra = vector of buying orders, calculated separately
#   venda = vector of selling orders, calculated separately
#   tx_comissao = ammount charged by the exchange in every order
#   grafico = whether the user want to see a graph (TRUE) or not (FALSE, default)
#
def backtest(df, max_ordens=10, saldo_inicial=1000, compra=0, venda=0, tx_comissao = 0.001, grafico=False):
    # Base parameters for backtesting
    carteira_full = max_ordens  # Maximum 'slices' of the whole balance (all USD + all crypto assets)
    periodo = df.copy()
    marcador = 1
    periodo['vender'] = 0
    periodo['comprar'] = 0
    periodo['sinal_est'] = 0  # Creates neutral signals throughout the df, marked by the trade strategy in use
    periodo['cv'] = 0  # Creates neutral states, no sell or buy order by default, used whether there's an actual trade order
    periodo['marcador'] = 0  # Creates neutral marker, used for the weekly reports in the real money script
    periodo['saldo_inicial'] = 0.0  # initial balance
    periodo['saldo_final'] = 0.0  # final balance
    periodo['saldo_cart'] = 0.0  # balance of crypto(s) in wallet
    periodo['patrimonio'] = 0.0  # whole balance (free USD + cryptos)
    periodo.loc[venda, 'vender'] = -1  # Selling backtest record
    periodo.loc[compra, 'comprar'] = 1  # Buying backtest record
    periodo['sinal_est'] = periodo['vender'] + periodo['comprar']  # marker used to avoid 'weak' trade signals
    inicio = periodo.index[0]  # beginnig of the timeframe
    periodo.loc[inicio, 'saldo_inicial'] = saldo_inicial
    # Check for any buying signal, returns error if there is none
    if periodo[periodo['sinal_est'] == 1]['sinal_est'].sum() == 0:
        print('\n\n###################################################################################')
        print('###                                                                             ###')
        print('###          >>> Strategy with NO BUYING signal in this timeframe! <<<          ###')
        print('###                                                                             ###')
        print('###    Backtest will return an error with "periodo", I broke it itentionally:   ###')
        print('###                                                                             ###')
        print('###################################################################################\n\n')
        del periodo
    else:
        pass
    if periodo[periodo['sinal_est'] == -1]['sinal_est'].sum() == 0:
        print('\n\n###################################################################################')
        print('###                                                                             ###')
        print('###          >>> Strategy with NO SELLING signal in this timeframe! <<<         ###')
        print('###                                                                             ###')
        print('###    Backtest will return an error with "periodo", I broke it itentionally:   ###')
        print('###                                                                             ###')
        print('###################################################################################\n\n')
        del periodo
    else:
        pass
#
    for idx in periodo.index:
        status = 0
    # Fetch previous initial balance, the same as initial balance if it's the first point of data
        if idx == inicio:
            periodo.loc[idx, 'saldo_inicial'] = saldo_inicial
            periodo.loc[idx, 'patrimonio'] = saldo_inicial
        else:
            periodo.loc[idx, 'saldo_inicial'] = periodo.loc[(idx - 1), 'saldo_final']
    # If you're out of balance to buy, the function don't bother checking buy signals
    # If the wallet is just free USD, Touring recalculates the slices values
        if carteira_full == 0:
            print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). No free resources to buy anything else')
            pass
        elif carteira_full == max_ordens:
            fatia = periodo.loc[idx, 'saldo_inicial']/carteira_full
        else:
            pass
    # BUY ORDERS PROCESSING
        if periodo.loc[idx, 'sinal_est'] == 1:  # Buy signal
            if carteira_full == 0:  # If there's no resources available to buy, there's no way to buy something
                pass
            else:
                periodo.loc[idx, 'cv'] = 1
                periodo.loc[idx, 'saldo_final'] = periodo.loc[idx, 'saldo_inicial'] - fatia
                if idx == periodo.index[0]:
                    periodo.loc[idx, 'saldo_cart'] = fatia*(1-tx_comissao)
                else:
                    periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - 1), 'saldo_cart'] + (fatia*(1-tx_comissao))
                carteira_full -= 1
                status = 1
                periodo.loc[idx, 'marcador'] = marcador
                periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
                print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). Buy order processed!')
    # SELL ORDERS PROCESSING
        elif periodo.loc[idx, 'sinal_est'] == -1:  # Sell signal
            if carteira_full == max_ordens:  # If there's only resources (so, no crypto in balance), there's nothing to sell
                pass
            else:
                periodo.loc[idx, 'cv'] = -1
                if idx < 3:
                    pass
                else:
                    if idx == periodo.index[-1]:  # If it is the last point of data, sells everything
                        valor = periodo[periodo['marcador'] == periodo['marcador'].max()]['close'].iloc[-1]
                        variacao = (periodo.loc[(idx), 'close'] - valor_atual)/valor_atual
                        venda = (fatia + (fatia * variacao))*(1-tx_comissao)
                        periodo.loc[idx, 'saldo_final'] = venda + periodo.loc[idx, 'saldo_inicial']
                        print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). Venda realizada!')
                        periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - 1), 'saldo_cart'] - fatia
                        periodo.loc[idx, 'marcador'] = marcador*-1
                        periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
                        carteira_full += 1
                        print(f'Backtesting finalizado! ***  Zerando posições em fim de período  ***')
                    else:
                        valor_atual = periodo[periodo['marcador'] == periodo['marcador'].max()]['close'].iloc[-1]
                        variacao = (periodo.loc[(idx + 1), 'close'] - valor_atual)/valor_atual
                        venda = (fatia + (fatia * variacao))*(1-tx_comissao)
                        periodo.loc[idx, 'saldo_final'] = venda + periodo.loc[idx, 'saldo_inicial']
                        print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). Venda realizada!')
                        periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - 1), 'saldo_cart'] - fatia
                        periodo.loc[idx, 'marcador'] = marcador*-1
                        periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
                        carteira_full += 1
                        if carteira_full == max_ordens:
                            print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). ***  Todas posições zeradas!  ***')
                            marcador += 1
                        else:
                            pass
                        status = -1
        else:
            pass
    # DATA WITH NO TRADE ORDERS PROCESSING
        if status == 0:
            if idx == periodo.index[0]:
                periodo.loc[idx, 'saldo_final'] = periodo.loc[idx, 'saldo_inicial']
            else:
                periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - 1), 'saldo_cart']
                periodo.loc[idx, 'saldo_inicial'] = periodo.loc[(idx - 1), 'saldo_final']
                periodo.loc[idx, 'saldo_final'] = periodo.loc[idx, 'saldo_inicial']
                periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
        else:
            pass
        if idx == periodo.index[-1]:  # If it is the last point of data, sells everything
            valor_atual = periodo[periodo['marcador'] == periodo['marcador'].max()]['close'].iloc[-1]
            variacao = (periodo.loc[(idx), 'close'] - valor_atual)/valor_atual
            fatia = periodo.loc[(idx), 'saldo_cart']
            venda = (fatia + (fatia * variacao))*(1-tx_comissao)
            periodo.loc[idx, 'saldo_final'] = venda + periodo.loc[idx, 'saldo_inicial']
            periodo.loc[idx, 'saldo_cart'] = 0
            periodo.loc[idx, 'marcador'] = marcador*-1
            periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
            print(f'Backtesting finished! ***  Clearing positions at the end of the period  ***')
        else:
            pass
    periodo['rendimento'] = (periodo['patrimonio']/periodo['patrimonio'].iloc[0])-1
    periodo['ativo_acum'] = (periodo['close']/periodo['close'].iloc[0])-1
    saldo_final = round(periodo['saldo_final'].iloc[-1], 2) + round(periodo['saldo_cart'].iloc[-1], 2)
    saldo_maximo = round(periodo.patrimonio.max(), 2)
    rend_est = round(((saldo_final-saldo_inicial)/saldo_inicial)*100, 2)
    rend_at = round(((periodo.close.iloc[-1]/periodo.open.iloc[0])-1)*100, 2)
    print(f'\n\nInitial hypothetical balance: US${saldo_inicial}')
    print(f'End balance: US${saldo_final}')
    print(f'Total earnings from the strategy: {rend_est}%')
    print(f'Total variation by the asset: {rend_at}%')
    if rend_at > rend_est:
        print("\n\nRESULT: this strategy DO NOT outperformed the asset in the considered timeframe!")
    else:
        print("\n\nRESULT: Congratulations! This strategy OUTPERFORMED the asset in the considered timeframe!")
    print('\n\n   Strategy characteristics:')
    print(f'# of slices: {max_ordens}')
    print(f'# of buying trades: {periodo[periodo['cv'] == 1]['cv'].sum()}')
    print(f'# of selling trades: {abs(periodo[periodo['cv'] == -1]['cv'].sum())}')
    print(f'Time horizon: {dias} days')
    print(f'Timeframe: ' + str(intervalo) + 'm')
    print(f'Max equity over time: US${saldo_maximo}')
    print(f'Asset max value over time: US${periodo.close.max()}')
    print(f'Asset min value overr time: US${periodo.close.min()}')
    if grafico == True:
        # Creates entry/exit flags
        periodo[['entrada', 'saida']] = 0
        mask = periodo['marcador'] != 0
        for i in periodo[mask]['marcador']:
            if i > 0:
                for idx1 in (periodo[periodo['marcador'] == i]).index:
                    periodo.loc[idx1, 'entrada'] = 1
            elif i < 0:
                for idxm1 in (periodo[periodo['marcador'] == i]).index:
                    periodo.loc[idxm1, 'saida'] = 1
            else:
                pass
        # Generates scatterplot
        scatter_entrada = []
        scatter_saida = []
        for point in periodo[(periodo.entrada == 1)].index:
            scatter_entrada.append(periodo.loc[point, ['timestamp', 'close']])
        for point in periodo[(periodo.saida == 1)].index:
            scatter_saida.append(periodo.loc[point, ['timestamp', 'close']])
        # Creates both charts
        plt.subplot(211)
        plt.plot(periodo.set_index(keys='timestamp')['mmLonga'],
                 color='green',
                 label='Long MA')  # MA = 'moving average'
        plt.plot(periodo.set_index(keys='timestamp')['mmMedia'],
                 color='blue',
                 label='Intermediary MA')
        plt.plot(periodo.set_index(keys='timestamp')['mmCurta'],
                 color='red',
                 label='Short MA')
        plt.plot(periodo.set_index(keys='timestamp')['close'],
                 color='gray',
                 label='Closing price')
        plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
                    y=pd.DataFrame(scatter_entrada)['close'],
                    color='green',
                    marker='^',
                    label='Entry point',
                    zorder=10)
        plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
                    y=pd.DataFrame(scatter_saida)['close'],
                    color='red',
                    marker='v',
                    label='Exit point',
                    zorder=10)
        plt.xlabel("Time")
        plt.ylabel("Asset price")
        plt.title('Asset value historic chart')
        plt.legend()
        plt.subplot(212)
        plt.plot(periodo.set_index(keys='timestamp')['ativo_acum'],
                 color='orange', label='Asset oscilation',
                 zorder=5)
        plt.plot(periodo.set_index(keys='timestamp')['rendimento'],
                 color='magenta', label='Strategy earnings',
                 zorder=7)
        plt.xlabel("Time")
        plt.ylabel("Profitability")
        plt.title('Comparative chart of profitability (Asset x Strategy)')
        plt.legend()
        plt.show()
    elif grafico == False:
        pass
    else:
        print('\n*Unable to draw the chart!*\nHyperparameter "grafico" must be either True ou False, informed anything else.')
    return periodo


###
# BACKTEST SUMMARY FUNCTION
#
# Just in case you don't wanna perform all the backtest calculations again just to see the summary or the chart
###

def backtest_summary(df, max_ordens=10, saldo_inicial=1000, grafico=False):
    saldo_final = round(df['saldo_final'].iloc[-1], 2) + round(df['saldo_cart'].iloc[-1], 2)
    saldo_maximo = round(df.patrimonio.max(), 2)
    rend_est = round(((saldo_final-saldo_inicial)/saldo_inicial)*100, 2)
    rend_at = round(((df.close.iloc[-1]/df.open.iloc[0])-1)*100, 2)
    print(f'\n\nInitial hypothetical balance: US${saldo_inicial}')
    print(f'End balance: US${saldo_final}')
    print(f'Total earnings from the strategy: {rend_est}%')
    print(f'Total variation by the asset: {rend_at}%')
    if rend_at > rend_est:
        print("\n\nRESULT: this strategy DO NOT outperformed the asset in the considered timeframe!")
    else:
        print("\n\nRESULT: Congratulations! This strategy OUTPERFORMED the asset in the considered timeframe!")
    print('\n\n   Strategy characteristics:')
    print(f'# of slices: {max_ordens}')
    print(f'# of buying trades: {periodo[periodo['cv'] == 1]['cv'].sum()}')
    print(f'# of selling trades: {abs(periodo[periodo['cv'] == -1]['cv'].sum())}')
    print(f'Time horizon: {dias} days')
    print(f'Timeframe: ' + str(intervalo) + 'm')
    print(f'Max equity over time: US${saldo_maximo}')
    print(f'Asset max value over time: US${periodo.close.max()}')
    print(f'Asset min value overr time: US${periodo.close.min()}')
    if grafico == True:
        # Creates entry/exit flags
        periodo[['entrada', 'saida']] = 0
        mask = periodo['marcador'] != 0
        for i in periodo[mask]['marcador']:
            if i > 0:
                for idx1 in (periodo[periodo['marcador'] == i]).index:
                    periodo.loc[idx1, 'entrada'] = 1
            elif i < 0:
                for idxm1 in (periodo[periodo['marcador'] == i]).index:
                    periodo.loc[idxm1, 'saida'] = 1
            else:
                pass
        # Generates scatterplot
        scatter_entrada = []
        scatter_saida = []
        for point in periodo[(periodo.entrada == 1)].index:
            scatter_entrada.append(periodo.loc[point, ['timestamp', 'close']])
        for point in periodo[(periodo.saida == 1)].index:
            scatter_saida.append(periodo.loc[point, ['timestamp', 'close']])
        # Creates both charts
        plt.subplot(211)
        plt.plot(periodo.set_index(keys='timestamp')['mmLonga'],
                 color='green',
                 label='Long MA')  # MA = 'moving average'
        plt.plot(periodo.set_index(keys='timestamp')['mmMedia'],
                 color='blue',
                 label='Intermediary MA')
        plt.plot(periodo.set_index(keys='timestamp')['mmCurta'],
                 color='red',
                 label='Short MA')
        plt.plot(periodo.set_index(keys='timestamp')['close'],
                 color='gray',
                 label='Closing price')
        plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
                    y=pd.DataFrame(scatter_entrada)['close'],
                    color='green',
                    marker='^',
                    label='Entry point',
                    zorder=10)
        plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
                    y=pd.DataFrame(scatter_saida)['close'],
                    color='red',
                    marker='v',
                    label='Exit point',
                    zorder=10)
        plt.xlabel("Time")
        plt.ylabel("Asset price")
        plt.title('Asset value historic chart')
        plt.legend()
        plt.subplot(212)
        plt.plot(periodo.set_index(keys='timestamp')['ativo_acum'],
                 color='orange', label='Asset oscilation',
                 zorder=5)
        plt.plot(periodo.set_index(keys='timestamp')['rendimento'],
                 color='magenta', label='Strategy earnings',
                 zorder=7)
        plt.xlabel("Time")
        plt.ylabel("Profitability")
        plt.title('Comparative chart of profitability (Asset x Strategy)')
        plt.legend()
        plt.show()
    elif grafico == False:
        pass
    else:
        print('\n*Unable to draw the chart!*\nHyperparameter "grafico" must be either True ou False, informed anything else.')


#############################################################
#                                                           #
#               Some strategies for you to try              #
#                                                           #
#  -------------------------------------------------------  #
#                                                           #
#   Down here  is where you'll  be  able to test  different #
# strategies that  come up in your mind.  I'll give you two #
# strategies for you to start on. One is based in moving a- #
# verages  (simple as that) and the other is based in a few #
# more indicators,  the  bot  then estimates to whether the #
# strategy   has  more  buying  strenght  or  more  selling #
# strength and act accordingly.                             #
#                                                           #
#############################################################

#######
#
# !!! FIRST STRATEGY STARTS HERE !!!
#
# Strategy based in moving averages, trading bitcoin
#
#######

# First, let's fetch historical data
days = 90  # fetch 90 days worth of data...
interval = 15  # ...for every 'N' minutes timeframe
historico = valores_historicos(dias=days,
                               intervalo=str(str(interval)+'m'),
                               ticker='BTCUSDT')
adiciona_indicadores(historico)
historico = historico.dropna()
historico = historico.reset_index()

# Then we create vectors with trade signals
teste_compra = []  # creates a vector with buying signals
teste_venda = []  # creates a vector with selling signals
defasagem = 4  # '4' means 1h (15min x 4 = 1 hour)
##########################################################
#                  BUYING parameters:                    #
##########################################################
for idx in historico.index:
    pm1h = ((historico.loc[idx-4:idx]['open'] + historico.loc[idx-4:idx]['close'])/2).mean()
    pm2h = ((historico.loc[idx-8:idx]['open'] + historico.loc[idx-8:idx]['close'])/2).mean()
    pm3h = ((historico.loc[idx-12:idx]['open'] + historico.loc[idx-12:idx]['close'])/2).mean()
    if idx >= defasagem:
        # If the average price is hourly going down in the last three hours, inhibits buying trades
        if (pm3h > pm2h) & (pm2h > pm1h) & (pm1h > historico.loc[idx, 'open']):
            teste_compra.append(False)
        else:
            if (historico.loc[idx-1, 'close'] <= historico.loc[idx-defasagem:idx-1, 'close'].min()):
                teste_compra.append(False)
            # Registers a buy order if the closing price is greater then the opening price from the last two consecutive periods
            else:
                teste_compra.append((historico.loc[(idx-1), 'close'] > historico.loc[idx-1, 'open']) &
                                    (historico.loc[idx-2, 'close'] > historico.loc[idx-2, 'open']))
    else:
        if idx >= 2:
            if historico.loc[idx, 'open'] < historico.loc[idx-1, 'mmCurta']:
                teste_compra.append(False)
            else:
                teste_compra.append((historico.loc[(idx-1), 'close'] > historico.loc[idx-1, 'open']) &
                                        (historico.loc[idx-2, 'close'] > historico.loc[idx-2, 'open']))
        else:
            teste_compra.append(False)
##########################################################
#                  SELLING parameters:                   #
##########################################################
    if idx >= defasagem:
        # If the closing price is going down for the last hour, registers a sell order
        if((historico.loc[idx-4, 'close'] > historico.loc[idx-3, 'close'])
                (historico.loc[idx-3, 'close'] > historico.loc[idx-2, 'close']) &
                (historico.loc[idx-2, 'close'] > historico.loc[idx-1, 'close']) &
                (historico.loc[idx, 'open'] > historico.loc[idx-1, 'mmCurta'])):
            teste_venda.append(True)
        else:
            teste_venda.append(False)
    elif idx < defasagem:
        if idx < 1:
            teste_venda.append(False)
        elif historico.loc[idx, 'open'] < historico.loc[idx-1, 'mmCurta']:
            teste_venda.append(True)
        else:
            teste_venda.append(False)
    else:
        print('Algo de muito bizarro aconteceu, essa print não estava prevista!')
#######
#
# !!! FIRST STRATEGY ENDS HERE !!!
#
# Just execute the code above to generate the buy/sell signals
#
#######




#######
#
# !!! SECOND STRATEGY STARTS HERE !!!
#
# Strategy based in buy/sell strenghts, trading bitcoin
#
#######

# Again, first we fetch historical data but then we go straight to the strategy
days = 90
interval = 15
historico = valores_historicos(dias=days,
                               intervalo=str(str(interval)+'m'),
                               ticker='BTCUSDT')
adiciona_indicadores(historico)
historico = historico.dropna()
historico = historico.reset_index()
#
##########################################################
#                 STRENGTH parameters:                   #
##########################################################
historico['forca_venda'] = 0
tempo = 4 # periods of 'interval' minutes, as stated above, meaning 4 here = 1 hour (4 periods of 15min)
pm1 = (historico.loc[idx-tempo:idx]['close']).mean()
pm2 = (historico.loc[idx-(tempo*2):idx-tempo]['close']).mean()
pm3 = (historico.loc[idx-(tempo*3):idx-(tempo*2)]['close']).mean()
for idx in historico.index:
    bear = 0
    if historico.loc[idx, 'mmCurta'] < historico.loc[idx, 'close']: # if the closing price is higher then the short MA, adds one point of strength to selling forces
        bear += 1
    else:
        pass
    if historico.loc[idx, 'mmMedia'] > historico.loc[idx, 'mmCurta']: # if the intermediary MA is higher then the short MA, adds one point of strength to selling forces
        bear += 1
    else:
        pass
    if historico.loc[idx, 'mmLonga'] > historico.loc[idx, 'mmMedia']:  # if the long MA is higher then the intermediary MA, adds one point of strength to selling forces
        bear += 1
    else:
        pass
    if historico.loc[idx, 'rsi'] >= 70:  # if the RSI parameter is over 70, adds two points of strength to selling forces
        bear += 2
    else:
        pass
    if idx < tempo:
        pass
    else:
        if (pm3 > pm2) & (pm2 > pm1) & (pm1 > historico.loc[idx, 'close']):  # if the average price is going down for the last three hours, in consecutive markings, adds six points of strength to selling forces
            bear += 6
        else:
            pass
    historico.loc[idx, 'bear'] = bear  # records the selling forces
#
historico['bull'] = 0
uma_hora = 4  # I created other object, has the same use of 'tempo' above
horas = uma_hora * 48
for idx in historico.index:
    bull = 0
    if historico.loc[idx, 'close'] > historico.loc[idx, 'mmCurta']:  # if the closing price is higher than the short MA, adds one point of strength to buying forces
        bull += 1
    else:
        pass
    if historico.loc[idx, 'mmCurta'] > historico.loc[idx, 'mmMedia']:  # if the short MA is higher then the intermediary MA, adds one point of strength to buying forces
        bull += 1
    else:
        pass
    if historico.loc[idx, 'mmMedia'] > historico.loc[idx, 'mmLonga']:  # if the intermediary MA is higher then the long MA, adds one point of strength to buying forces
        bull += 1
    else:
        pass
    if historico.loc[idx, 'rsi'] <= 30:  # if the RSI parameter is under (or equal to) 30, adds two points of strength to buying forces
        bull += 2
    else:
        pass
    if idx < horas:
        pass
    else:
        maxima = historico.loc[(idx-horas):idx, 'close'].max()
        minima = historico.loc[(idx-horas):idx, 'close'].min()
        amplitude = maxima - minima
        if (amplitude < historico.loc[idx, 'close']*0.00618) or (amplitude > historico.loc[idx, 'close']*0.1382):  # playing with Fibonacci numbers here: if the spread of the asset's price is out of these parameters, subtract three points of strength from the buying forces
            bull -= 3
        else:
            pass
historico.loc[idx, 'bull'] = bull  # records the buying forces
#
historico['acao'] = historico['bull'] - historico['bear']  # the forces confront here, generating buy signals, sell signals or just nothing to do
#
teste_compra = historico['acao'] > 0  # creates a vector with the buying signals
teste_venda = historico['acao'] < 0  # creates a vector with the selling signals
#######
#
# !!! SECOND STRATEGY ENDS HERE !!!
#
#######



#######
#
# Now, the backtest itself.
#
#######

ordens = 2  # number of slices of the whole equity available, in money power
strategy = backtest(historico, saldo_inicial=1000, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=False)

# You can call the summary function too, once the backtest had run
backtest_summary(strategy, max_ordens=ordens, grafico=True)
