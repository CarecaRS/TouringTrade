import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
import binance.enums  # responsável pelo trading
import datetime
import requests
import json
import time
import pandas_ta
from binance.client import Client
from keys import api_secret, api_key  # Importa a api do arquivo local keys.py
%autoindent OFF

###
# TO-DO
# - Alterar os tickers para os pares aceitos na Binance (tipo BTCUSDT)
# - Fazer um loop para que o sistema busque as informações históricas de
#   toda a lista do touring_index

###
# JÁ FEITO
#
# - Pega a relação dos maiores market caps para negociação: coinmarketcap.com
#   > o CoinMarketCap retorna apenas as 20 maiores moedas em volume de mercado

###
# IDEIA1: pelo menos cinco indicadores recebendo os dados/calculando a cada segundo.
# - Quando pelo menos 4 indicadores derem sinal de compra, comprar (fatias de 20%).
# - Quando pelo menos 3 indicadores (2 para um viés mais conservador) derem sinal de venda, sair da posição.
# - Necessário: saldo inicial (já calcula as fatias de compra), quantidade inicial do ativo, quantidade atual do ativo


###
# OBTENÇÃO DOS TICKERS DO COINMARKETCAP
###
cryptos = pd.read_html('https://coinmarketcap.com/all/views/all/')[2]
cryptos = cryptos.iloc[:, : 10].dropna()
touring_index = list(cryptos['Symbol'])  # tickers que poderão ser negociados


###
# ACESSO AO SISTEMA DA BINANCE
###
cliente = Client(api_key, api_secret)
infos = cliente.get_account()  # carrega as infos do usuário

# Recupera as informações da carteira do usuário
carteira = pd.DataFrame(infos['balances'])
numeros = ['free', 'locked']
carteira[numeros] = carteira[numeros].astype(float)  # transforma obj em float
mask = carteira[numeros][carteira[numeros] > 0] \
        .dropna(how='all').index  # filtro dos ativos com saldo
carteira = carteira.iloc[mask]  # mantem apenas os ativos com saldo

###
# BLACKLIST DE ATIVOS
###
#
# Relação de ativos a se desconsiderar, que não serão negociados,
# seja por estratégia de buy and hold ou por qualquer outro motivo
black_list = ['NFT', 'SHIB', 'BTTC']
mask = carteira[carteira['asset'].isin(black_list)].index  # registra o índice dos black
carteira.drop(mask, axis=0, inplace=True)  # dropa ativos black


###
# HISTÓRICO DOS ATIVOS
##
# Definição do horizonte de tempo dos dados históricos
end_time = datetime.datetime.now()
start_time = end_time - datetime.timedelta(days=(365*5))

# Converte o tempo para Unix (pq Binance) em milisegundos
end_timestamp = int(end_time.timestamp()*1000)
start_timestamp = int(start_time.timestamp()*1000)

# Janela de tempo estabelecida, solicita à Binance o histórico
# Endpoint da Binance
endpoint = 'https://api.binance.com/api/v3/klines'

# Definição dos parâmetros da requisição
tickers = 'BTCUSDT'  # compra a primeira usando a segunda
interval = '30m'  # outras amplitudes em https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
limit = 1000
params = {'symbol': tickers, 'interval': interval,
          'endTime': end_timestamp, 'limit': limit,
          'startTime': start_timestamp}

# Realiza a requisição e salva numa lista
data = []
while True:
    response = requests.get(endpoint, params=params)
    klines = json.loads(response.text)
    data += klines
    if len(klines) < limit:
        break
    params['startTime'] = int(klines[-1][0])+1
    time.sleep(0.1)

# Cria um dataframe com OHLC e horários
# Sobre as posições de kline[n]: https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
ohlc_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4]), float(kline[5]), float(kline[7]), float(kline[8])] for kline in data]
historico = pd.DataFrame(ohlc_data, columns=['open', 'high', 'low', 'close', 'volume_ativo', 'volume_financeiro', 'qtde_negocios'])
timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in data]
historico['timestamp'] = timestamps
historico.set_index('timestamp', inplace=True)
historico['par'] = tickers


###
# CÁLCULO DE INDICADORES
###
# Com o historico já baixado, é hora de incluir o dataframe alguns indicadores
# necessários para a tomada de decisão. O pacote 'pandas_ta' faz a maior parte
# dos cálculos, se não todos.
periodo = 20

# Garman-Klauss Volatility
historico['garman_klauss_vol'] = (((np.log(historico['high']) - np.log(historico['low']))**2)/2) - (2*np.log(2)-1) * ((np.log(historico['close']) - np.log(historico['open']))**2)

# RSI
# O RSI não é normalizado pois no caso de se agregar cesta de ativos
# é necessário o valor bruto
historico['rsi'] = pandas_ta.rsi(close=historico['close'], length=periodo)

# Bollinger Bands
historico['bb_low'] = pandas_ta.bbands(close=np.log1p(historico['close']),
                                       length=periodo).iloc[:, 0]
historico['bb_mid'] = pandas_ta.bbands(close=np.log1p(historico['close']),
                                       length=periodo).iloc[:, 1]
historico['bb_high'] = pandas_ta.bbands(close=np.log1p(historico['close']),
                                        length=periodo).iloc[:, 2]

# Average True Range (ATR)
# Primeiro se armazena os valores 'brutos' em um objeto, para depois passar
# por processo de normalização (subtrai a média e divide pelo desvio padrão).
# NÃO seria necessário para apenas um ativo, mas seria fundamental na
# análise de 2+ ativos. Então, por questão de boas práticas, usa-se a
# normalização.
atr = pandas_ta.atr(high=historico['high'], low=historico['low'],
                    close=historico['close'], length=periodo)
historico['atr'] = atr.sub(atr.mean()).div(atr.std())


# MACD
# Mesmo processo do ATR acima, é necessário normalizar quando for analisar
# 2+ ativos em conjunto. O cálculo do pandas_ta.macd() retorna três features
# para cada observação: o próprio MACD, o histograma e um sinal. Aqui quero
# apenas o próprio MACD.
macd = pandas_ta.macd(close=historico['close'], length=periodo).iloc[:, 0]
historico['macd'] = macd.sub(macd.mean()).div(macd.std())


# VOLUME FINANCEIRO
# Pequeno ajuste apenas para exibir o valor em milhões
historico['volume_financeiro'] = historico['volume_financeiro']/1e6


###
# TRABALHANDO COM AS INFORMAÇÕES OBTIDAS (parei depois dos 35min do video do quant)
###

historico['volume_financeiro'].resample('2h').mean()

#
#
#
#
#
#


####
# VERIFICAÇÕES diversas na Binance, caso necessárias:
###
# Verifica a tabela de comissões compra/venda
infos['commissionRates']

# Verifica as autorizações do cliente (trade/saque/depósito)
infos['canTrade']
infos['canWithdraw']
infos['canDeposit']

# Verifica a conta pela qual são feitas as negociações (margin/spot)
infos['accountType']

# Retorna o user ID na corretora
infos['uid']


#
#
#
#
#
#
# Final do arquivo, só serve para testar coisas e não tem nada de importante

carteira

carteira.info()
