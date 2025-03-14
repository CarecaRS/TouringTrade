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
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades do ativo
    livro_compras = pd.DataFrame(cliente.get_order_book(symbol=ticker))
    preco_ticker = float(livro_compras.loc[0]['bids'][0])
    saldoBTCemUSD = saldo_ticker*preco_ticker  # Estima o valor do ativo em USD
    patrimonio = saldo_usd + saldoBTCemUSD  # Calcula o patrimônio total vigente (ativo + USD)
    filtros_btc = cliente.get_symbol_info(ticker)['filters']  # Busca as informações pertinentes ao ativo na exchange
    step_btc = float(filtros_btc[1]['minQty'])  # Obtenção da quantidade mínima do ativo para uma ordem válida
    fatia = patrimonio/max_ordens  # Calcula o valor de cada 'fatia', baseado no número máximo de posições mantidas a cada tempo
    carteira_full = max_ordens - round(saldoBTCemUSD/fatia)  # Faz o registro do número de posições que pode-se entrar no momento do loop
    qtde_btc = fatia/preco_ticker  # Calcula a quantidade de ativo para cada valor (fatia) de investimento estabelecido acima
    if saldo_usd < fatia: # Prevenção na compra, onde o saldo é inferior à fatia
        fatia = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
        qtde_btc = fatia/preco_ticker  # Calcula a quantidade de ativo para cada valor (fatia) de investimento estabelecido acima
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Arredonda para baixo a quantidade de ativo em cada ordem
        qtde_btc = qtde_btc*100000
        qtde_btc = round(qtde_btc)
        qtde_btc = qtde_btc/100000
    else:
        qtde_btc = fatia/preco_ticker  # Calcula a quantidade de ativo para cada valor (fatia) de investimento estabelecido acima
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Arredonda para baixo a quantidade de ativo em cada ordem
        qtde_btc = qtde_btc*100000  # O arredondamento acima pode ter erro de cálculo na 10a casa decimal
        qtde_btc = round(qtde_btc)  # Procede com um novo arredondamento para evitar problemas
        qtde_btc = qtde_btc/100000
    return qtde_btc, fatia

def calcula_cotas_venda():
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades do ativo
    livro_compras = pd.DataFrame(cliente.get_order_book(symbol=ticker))
    preco_ticker = float(livro_compras.loc[0]['bids'][0])
    saldoBTCemUSD = saldo_ticker*preco_ticker  # Estima o valor do ativo em USD
    patrimonio = saldo_usd + saldoBTCemUSD  # Calcula o patrimônio total vigente (ativo + USD)
    filtros_btc = cliente.get_symbol_info(ticker)['filters']  # Busca as informações pertinentes ao ativo na exchange
    step_btc = float(filtros_btc[1]['minQty'])  # Obtenção da quantidade mínima do ativo para uma ordem válida
    fatia = patrimonio/max_ordens  # Calcula o valor de cada 'fatia', baseado no número máximo de posições mantidas a cada tempo
    carteira_full = max_ordens - round(saldoBTCemUSD/fatia)  # Faz o registro do número de posições que pode-se entrar no momento do loop
    qtde_btc = fatia/preco_ticker  # Calcula a quantidade de ativo para cada valor (fatia) de investimento estabelecido acima
    if carteira[carteira['asset'] == ticker[:3]]['free'].sum() < saldo_ticker: # Prevenção na venda, onde a qtde_btc é inferior ao saldo
        qtde_btc = saldo_ticker
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Arredonda para baixo a quantidade de ativo para venda
        qtde_btc = qtde_btc*100000  # O arredondamento acima pode ter erro de cálculo na 10a casa decimal
        qtde_btc = round(qtde_btc)  # Procede com um novo arredondamento para evitar problemas
        qtde_btc = qtde_btc/100000
    else:
        qtde_btc = fatia/preco_ticker  # Calcula a quantidade de ativo para cada valor (fatia) de investimento estabelecido acima
        qtde_btc = math.floor(qtde_btc/step_btc)*step_btc  # Arredonda para baixo a quantidade de ativo em cada ordem
        qtde_btc = qtde_btc*100000  # O arredondamento acima pode ter erro de cálculo na 10a casa decimal
        qtde_btc = round(qtde_btc)  # Procede com um novo arredondamento para evitar problemas
        qtde_btc = qtde_btc/100000
    return qtde_btc, fatia


###
# HISTORICAL DATA
###
def valores_historicos(ticker='BTCUSDT', dias=30, intervalo='5m'):
    if dias < 3:
        print('\n\n\n\n*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
        print('IMPORTANTE! A quantidade de dias deve ser 3 ou mais dias! Este histórico NÃO VAI FUNCIONAR!\n\n')
        print('*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
    else:
        pass
    # Definição do horizonte de tempo dos dados históricos
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=dias)
    # Converte o tempo para Unix (pq Binance) em milisegundos
    end_timestamp = int(end_time.timestamp()*1000)
    start_timestamp = int(start_time.timestamp()*1000)
    # Janela de tempo estabelecida, solicita à Binance o histórico
    # Endpoint da Binance
    endpoint = 'https://api.binance.com/api/v3/klines'
    # Definição dos parâmetros da requisição
    tickers = ticker  # compra a primeira usando a segunda
    interval = intervalo  # outras amplitudes em https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    limit = 1000
    params = {'symbol': tickers, 'interval': interval,
              'endTime': end_timestamp, 'limit': limit,
              'startTime': start_timestamp}
    print('Fazendo a requisição das informações à Binance...')
    # Realiza a requisição e salva numa lista
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
    # Cria um dataframe com OHLC e horários
    # Sobre as posições de kline[n]: https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])] for kline in dados]
    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close'])
    timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in dados]
    historico['timestamp'] = timestamps
    historico.set_index('timestamp', inplace=True)
    historico['par'] = tickers
    print('Requisição do histórico concluída.')
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
# INDICATORS CALC
###
def adiciona_indicadores(df, periodo=4):  # With 15min timeframes, 4 periods (periodo) of time equals 1 hour
# RSI
    df['rsi'] = pandas_ta.rsi(close=df['close'], length=periodo)
# Média Móvel curta (15min)
    df['mmCurta'] = pandas_ta.sma(df['close'], length=periodo/4)
# Média Móvel média 
    df['mmMedia'] = pandas_ta.sma(df['close'], length=periodo*30)
# Média Móvel longa
    df['mmLonga'] = pandas_ta.sma(df['close'], length=periodo*60)


###
# ESTRATÉGIA DE COMPRA/VENDA
###
def estrategia_bitcoin(df=None, defasagem=6):
    # Defaults:
    # defasagem = 6 -- fatias de 15min, '6' então equivale a 1h30min
    compra = []
    venda = []
    # Gera os sinais de compra
    for idx in df.index:
        pm1h = ((df.loc[idx-4:idx]['low'] + df.loc[idx-4:idx]['high'])/2).mean()
        pm2h = ((df.loc[idx-8:idx]['low'] + df.loc[idx-8:idx]['high'])/2).mean()
        pm3h = ((df.loc[idx-12:idx]['low'] + df.loc[idx-12:idx]['high'])/2).mean()
        if idx >= defasagem:
            # Se o preço de fechamento estiver em baixa seguida na última hora não libera compra
            if ((df.loc[idx-4, 'open'] > df.loc[idx-3, 'open']) &
                    (df.loc[idx-3, 'open'] > df.loc[idx-2, 'open']) &
                    (df.loc[idx-2, 'open'] > df.loc[idx-1, 'open']) &
                    (df.loc[idx-1, 'open'] > df.loc[idx, 'open']) &
                    (df.loc[idx, 'mmLonga'] > df.loc[idx, 'mmCurta'])):
                compra.append(False)
            # Se a média dos preços estiver caindo nas últimas três horas, inibe compra
            elif (pm3h > pm2h) & (pm2h > pm1h) & (pm1h > df.loc[idx, 'open']):
                compra.append(False)
            else:
                # Se o preço de fechamento anterior for menor ou igual ao mínimo dos últimos
                # 'defasagem' períodos (ou seja, preço segue baixando), não libera compra
                if (df.loc[idx-1, 'close'] <= df.loc[idx-defasagem:idx-1, 'close'].min()):
                    compra.append(False)
                else:
                    # Passada a verificação acima, se a máxima do período anterior
                    # estiver menor do que a máxima de agora E TAMBÉM a MM curta estiver
                    # maior que a MM longa, sinaliza compra
                    compra.append((df.loc[(idx-1), 'high'] < df.loc[idx, 'high']) &
                                  (df.loc[idx, 'mmCurta'] > df.loc[idx, 'mmLonga']))
        else:
            if idx >= 2:
                # Se a máxima do período anterior estiver menor do que a máxima
                # de agora (ou seja, preço está subindo) e também a MM curta esteja acima
                # da MM longa, sinaliza compra
                compra.append((df.loc[(idx-1), 'high'] < df.loc[idx, 'high']) &
                              (df.loc[idx, 'mmCurta'] > df.loc[idx, 'mmLonga']))
            else:
                # Outras situações diferentes do estabelecido, sinaliza 'não-compra'
                compra.append(False)
    # Gera os sinais de venda
    for idx in df.index:
        if idx >= defasagem:
            # Se o preço de fechamento estiver em baixa seguida na última hora e também
            # a MM curta estiver abaixo do preço de abertura, marca como venda
            if((df.loc[idx-4, 'close'] > df.loc[idx-3, 'close']) &
                    (df.loc[idx-3, 'close'] > df.loc[idx-2, 'close']) &
                    (df.loc[idx-2, 'close'] > df.loc[idx-1, 'close']) &
                    (df.loc[idx, 'open'] > df.loc[idx-1, 'mmCurta'])):
                venda.append(True)
            else:
                # Se não, registra 'não-venda'
                venda.append(False)
        elif idx < defasagem:
            if idx < 1:
                # Início da série temporal é desprezível na estratégia, registra sinal
                # de 'não-venda'
                venda.append(False)
            elif df.loc[idx, 'open'] < df.loc[idx-1, 'mmCurta']:
                # Se o preço de abertura for menor do que a MM curta do período anterior,
                # já registra sinal de venda
                venda.append(True)
            else:
                # Qualquer outro evento não estabelecido, não toma decisão alguma, então
                # registra como 'não-venda'
                venda.append(False)
        else:
            # Se eventualmente aparecer alguma coisa diferente do que o estabelecido
            # (o que eu acho *extremamente* improvável, retorna o erro abaixo
            print('Algo de muito bizarro aconteceu, essa print não estava prevista!')
    # Criação e registro dos sinais neutros, de compra e de venda:
    df['sinal_est'] = 0  # Gera sinais neutros ao longo de todo histórico
    df.loc[compra, 'sinal_est'] = 1  # Registro sinal de compra quando existente
    df.loc[venda, 'sinal_est'] = -1  # Registro sinal de venda quando existente


###
# TOURING ITSELF
###
def touring(max_ordens=3, compra=None, venda=None, ticker=None):
    marcador = 1  # Apenas para controle de ledger e zeramento de carteira
    print('\nAguardando o tempo certo para a primeira interação...\n')
    while cliente.get_system_status()['msg'] == 'normal':
        # A primeira interação estava ok, mas as próximas interações estavam
        # demorando mais tempo do que o código previa, então ao invés de esperar
        # por 60*15 segundos a cada ciclo, o ciclo só começa se for igual a um
        # destes momentos abaixo (min:seg).
        while (datetime.datetime.now().strftime('%M')[-1] in ('5', '0')) == False:
            time.sleep(1)
        else:
            # Verifica a existência do arquivo de registro das operações passadas.
            # Se o arquivo 'livro_contabil.csv' não existir na pasta deste script
            # ele vai gerar um novo no momento do primeiro trade.
            try:
                ledger = pd.read_csv('livro_contabil.csv')
                ledger = ledger.to_dict(orient='records')
            except:
                ledger = []
            # faz verificação do sinal da Binance, se não estiver normal retorna erro (depois do último 'else' lá embaixo)
            print('Atingido checkpoint de tempo, verificando...')
            print('Binance online, realizando nova análise de trading.\n')
            historico = valores_historicos(dias=3)  # busca o histórico do ativo
            adiciona_indicadores(historico)  # adiciona os indicadores utilizados
            print('Removendo NaNs e refazendo índice...')
            historico = historico.dropna()
            historico = historico.reset_index()  # limpa o df (acima) e faz o reset do índice
            estrategia_bitcoin(historico)  # gera os sinais de compra/venda da estratégia
            # Coleta dos saldos iniciais e cálculos básicos para dar continuidade no script
            saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
            saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades do ativo
            livro_compras = pd.DataFrame(cliente.get_order_book(symbol=ticker))  # Resgata as ordens em book
            preco_ticker = float(livro_compras.loc[0]['bids'][0])  # Utiliza o valor de compra do book como referência
            saldoBTCemUSD = saldo_ticker * preco_ticker  # Estima o valor do ativo em USD
            patrimonio = saldo_usd + saldoBTCemUSD  # Calcula o patrimônio total vigente (ativo + USD)
            filtros_btc = cliente.get_symbol_info(ticker)['filters']  # Busca as informações pertinentes ao ativo na exchange
            step_btc = float(filtros_btc[1]['minQty'])  # Obtenção da quantidade mínima do ativo para uma ordem válida
            fatia = patrimonio/max_ordens  # Calcula o valor de cada 'fatia', baseado no número máximo de posições mantidas a cada tempo
            carteira_full = max_ordens - round(saldoBTCemUSD/fatia)  # Faz o registro do número de posições que pode-se entrar no momento do loop
            qtde = fatia/preco_ticker  # Calcula a quantidade de ativo para cada valor (fatia) de investimento estabelecido acima
            qtde = math.floor(qtde/step_btc)*step_btc  # Arredonda para baixo a quantidade de ativo em cada ordem
            # Se a carteira estiver cheia novamente, refaz o valor das fatias,
            # senão só segue para a análise dos sinais
            if carteira_full == max_ordens:
                fatia = saldos_iniciais['USD']/carteira_full
            else:
                pass
            # ENVIO DO RELATÓRIO SEMANAL, SE MUDOU A SEMANA
            ledger_temp = pd.DataFrame(ledger)
            if len(ledger_temp) <= 2:
                pass
            else:
                if (((datetime.datetime.now().isocalendar()[1] - ledger_temp.loc[ledger_temp.shape[0]-1, 'Semana']) != 0) & (ledger_temp.iloc[-1]['Mail'] == 0)):
                    try:
                        print('\nMudança de semana. - enviando relatório semanal para o e-mail cadastrado.\n')
                        ledger_temp = pd.DataFrame(ledger)
                        ledger_temp.loc[(len(ledger_temp)-1), 'Mail'] = 1
                        pd.DataFrame(data=ledger_temp).to_csv('livro_contabil.csv', index=False)
                        email_relatorio(temp=ledger_temp)
                    except:
                        print('ERRO: Não foi possível o envio do e-mail de relatório semanal. Verificar.')
                else:
                    pass
            # PROCESSAMENTO DE COMPRAS
            if historico.loc[(historico.shape[0]-1), 'sinal_est'] == 1:  # Sinal de Compra da estratégia
            # Verifica saldo em carteira. Se a carteira estiver vazia,
            # não tem recurso para comprar, então nem verifica os sinais
            # de compra. Se a carteira estiver cheia novamente, refaz o
            # valor das fatias
                if carteira_full == 0:
                    print(f'\nÚltima verificação: {datetime.datetime.now().strftime('%H:%M:%S do dia %d/%m')}')
                    print(f'   --> Sinal de compra, mas sem recursos para comprar mais nada\n\n')
                    pass
                else:
                    if carteira_full == max_ordens:
                        marcador += 1
                    else:
                        pass
                    # Se o saldo para compra na carteira for maior ou igual que o necessário calculado na fatia, segue normal
#                    if saldo_usd >= fatia:
                    try:
                        qtde, fatia = calcula_cotas_compra()
                        cv = 'compra'
                        ordem_compra(ticker=ticker, quantity=qtde)
                        # Cria o registro em ledger
                        ledger.append({'Data': datetime.datetime.now(),
                                       'Semana': datetime.datetime.now().isocalendar()[1],
                                       'Ativo': ticker[:3],
                                       'CV': cv,
                                       'Marcador': marcador,
                                       'ValorUnitario': round(preco_ticker, 2),
                                       'Quantia': '{:.5f}'.format(qtde),
                                       'ValorNegociado': round(fatia, 2),
                                       'PatrimonioTotal': round(patrimonio, 2),
                                       'Mail': 0})
                            # Informa por e-mail da compra
#                            email_compra(saldos_iniciais=saldos_iniciais,
#                                         saldo_usd=saldo_usd,
#                                         saldo_ticker=saldo_ticker,
#                                         preco_ticker=preco_ticker,
#                                         patrimonio=patrimonio,
#                                         qtde=qtde,
#                                         fatia=fatia)
                        print(f'\nÚltima verificação: {datetime.datetime.now().strftime("%H:%M:%S do dia %d/%m")}')
                        print(f'   --> Compra de US${round(fatia, 2)} equivalente a {'{:.5f}'.format(qtde)} {ticker[:3]+'s'} realizada!\n\n')
                        # Faz o registro do ledger em arquivo local
                        pd.DataFrame(data=ledger).to_csv('livro_contabil.csv', index=False)
                        print(f'Aguardando novo ciclo...\n\n')
                    except:
                        erro_compra(qtde=qtde, ticker=ticker)
            # PROCESSAMENTO DE VENDAS
            elif historico.loc[(historico.shape[0]-1), 'sinal_est'] == -1:  # Sinal de Venda da estratégia
                if carteira_full == max_ordens:  # SE CARTEIRA 100% CHEIA DE GRANA, NÃO TEM O QUE VENDER
                    pass
                else:
                    # Se a quantia em carteira for maior ou igual que o mantante calculado na fatia, segue normal
#                    if carteira[carteira['asset'] == ticker[:3]]['free'].sum() >= qtde:
                    try:
                        qtde, fatia = calcula_cotas_venda()
                        cv = 'venda'
                        ordem_venda(ticker=ticker, quantity=qtde)
                        print(f'\nÚltima verificação: {datetime.datetime.now().strftime("%H:%M:%S do dia %d/%m")}')
                        print(f'   --> Venda de {'{:.5f}'.format(qtde)} {ticker[:3]+'s'} realizada, equivalente a US${round(fatia, 2)}.\n\n')
                        carteira_full += 1
                        # Cria o registro em ledger
                        ledger.append({'Data': datetime.datetime.now(),
                                       'Semana': datetime.datetime.now().isocalendar()[1],
                                       'Ativo': ticker[:3],
                                       'CV': cv,
                                       'Marcador': marcador,
                                       'ValorUnitario': round(preco_ticker, 2),
                                       'Quantia': '{:.5f}'.format(qtde),
                                       'ValorNegociado': round(fatia, 2),
                                       'PatrimonioTotal': round(patrimonio, 2),
                                       'Mail': 0})
                            # Informa a venda por e-mail, seja venda parcial ou de zeramento de todas posições
                        if carteira_full == 0:
                            print(f'\n\nÚltima verificação: {datetime.datetime.now().strftime("%H:%M:%S do dia %d/%m")}')
                            print('   --> ***  Todas posições zeradas!  ***\n\n')
                                # O email não muda praticamente nada, só a informação de ativo zerado
  #                              email_venda_zerado(saldos_iniciais=saldos_iniciais,
  #                                                 saldo_usd=saldo_usd,
  #                                                 saldo_ticker=saldo_ticker,
  #                                                 preco_ticker=preco_ticker,
  #                                                 patrimonio=patrimonio,
  #                                                 qtde=qtde,
  #                                                 fatia=fatia)
                        else:
                            pass
  #                              email_venda(saldos_iniciais=saldos_iniciais,
  #                                          saldo_usd=saldo_usd,
  #                                          saldo_ticker=saldo_ticker,
  #                                          preco_ticker=preco_ticker,
  #                                          patrimonio=patrimonio,
  #                                          qtde=qtde,
  #                                          fatia=fatia)
                        # Faz o registro do ledger em arquivo local
                        pd.DataFrame(data=ledger).to_csv('livro_contabil.csv', index=False)
                        print(f'Aguardando novo ciclo...\n\n')
                    except:
                        erro_venda(qtde=qtde, ticker=ticker)
            else:
                print(f'\nÚltima verificação: {datetime.datetime.now().strftime("%H:%M:%S do dia %d/%m")}')
                print(f'   --> Estratégia sem sinais de compra/venda ou sem saldo para venda no período, esperando.\n\n')
                pass
    # Se o sistema da Binance retornar qualquer coisa diferente de 'normal':
    else:
        # Imprime os avisos no console
        print('\n\n!!!! **** ATENÇÃO **** !!!!\n')
        print('!!!! BINANCE FORA DO AR !!!!\n')
        print('Não é possível seguir rodando.\n\n')
        # Registra os itens para envio de mensagem de aviso por e-mail ('cria' o e-mail)
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        subject = '*Touring offline*'
        print('Preparando corpo de texto para envio de e-mail.')
        body = (f'A Binance retornou status ANORMAL\n\n\
                Como nao consigo retomar as atividades, parei de trabalhar.\n\n\
                Assim que possivel por favor me reative para que eu siga monitorando as cryptos.\n\
                Lembrando que se eu nao estiver rodando eu nao consigo nem enviar os relatorios semanais.\n\n\
                Abracos e espero voltar a trabalhar logo :D')
        message = (f'Subject: {subject}\n\n{body}')
        # Faz o envio do e-mail
        print('Enviando e-mail agora.')
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(email_personal, email_pwd)
            smtp.sendmail(email_sender, email_personal, message)
        print('E-mail enviado com sucesso.')  # final do protocolo de envio de e-mail quando Binance der erro


######################################
#                                    #
#            Trading Area            #
#                                    #
######################################

# Verifica o acesso à carteira da Binance. Importante quando estiver
# rodando a partir de outro local que não o próprio PC. Se algo aconteceu
# e o Touring não conseguir acesso, ele avisa por e-mail.
try:
    carteira, cliente, infos = carteira_binance()
except:
    print('ERRO: Não foi possível contectar à carteira da Binance.')
    print('Favor verificar.\n')
    carteira_off()
    print('\n\nAbortando.')

ticker = 'BTCUSDT'  # Aqui, BTC adquirido/comprado com USDT
max_ordens = 2
#
touring(max_ordens=max_ordens, ticker=ticker)
