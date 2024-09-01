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
# - Transformar para função também a obtenção dos valores históricos
#   do ativo
# - Fazer um loop para que o sistema busque as informações históricas de
#   toda a lista do touring_index

###
# JÁ FEITO
#
# - Pega a relação dos maiores market caps para negociação: coinmarketcap.com
#   > o CoinMarketCap retorna apenas as 20 maiores moedas em volume de mercado
#   > Não tem pq pegar mais moedas porque por enquanto não se trabalhará com
#     cestas de ativos, apenas com C/V de ativo isolado
# - Criadas funções carteira(), valores_historicos() e adiciona_indicadores()

###
# IDEIA1: pelo menos cinco indicadores recebendo os dados/calculando a cada segundo.
# - Quando pelo menos 4 indicadores derem sinal de compra, comprar (fatias de 20%).
# - Quando pelo menos 3 indicadores (2 para um viés mais conservador) derem sinal de venda, sair da posição.
# - Necessário: saldo inicial (já calcula as fatias de compra), quantidade inicial do ativo, quantidade atual do ativo


###
# OBTENÇÃO DOS TICKERS DO COINMARKETCAP (registro para quando for necessário)
###
#coinmarketcap = pd.read_html('https://coinmarketcap.com/all/views/all/')[2]
#coinmarketcap = coinmarketcap.iloc[:, : 10].dropna()
#touring_index = list(coinmarketcap['Symbol'])  # tickers que poderão ser negociados

###
# ACESSO AO SISTEMA DA BINANCE
###
def carteira():
    cliente = Client(api_key, api_secret)
    print('Solicitando informações à Binance')
    infos = cliente.get_account()  # carrega as infos do usuário
    # Recupera as informações da carteira do usuário
    carteira = pd.DataFrame(infos['balances'])
    numeros = ['free', 'locked']
    carteira[numeros] = carteira[numeros].astype(float)  # transforma obj em float
    mask = carteira[numeros][carteira[numeros] > 0] \
            .dropna(how='all').index  # filtro dos ativos com saldo
    print('Limpeza geral da carteira')
    carteira = carteira.iloc[mask]  # mantem apenas os ativos com saldo
    black_list = ['NFT', 'SHIB', 'BTTC']  # blacklist de ativos
    mask = carteira[carteira['asset'].isin(black_list)].index  # registra o índice dos black
    carteira.drop(mask, axis=0, inplace=True)  # dropa ativos black
    print('Carteira obtida com sucesso. Ativos atuais e quantidades:')
    return carteira


###
# HISTÓRICO DOS ATIVOS
##
def valores_historicos(ticker='BTCUSDT', dias=30, fatia='15m'):
    '''valores_historicos(ticker, dias=30, fatia='15m')
    Recupera os valores históricos do ativo. Depende de três parâmetros:
        ticker: default='BTCUSDT', o ativo em questão (Binance usa par de ativos)
        dias: default=30, o tempo histórico desejado
        fatia: default='15m', o intervalo de mensuração
    '''
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
    interval = fatia  # outras amplitudes em https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Kline-Candlestick-Data
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
    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4]), float(kline[5]), float(kline[7]), float(kline[8])] for kline in dados]
    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close', 'volume_ativo', 'volume_financeiro', 'qtde_negocios'])
    timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in dados]
    historico['timestamp'] = timestamps
    historico.set_index('timestamp', inplace=True)
    historico['par'] = tickers
    print('Reduzindo magnitude do volume financeiro')
    historico['volume_financeiro'] = historico['volume_financeiro']/1e6
    print('Requisição do histórico concluída.')
    return historico


###
# CÁLCULO DOS INDICADORES
###
def adiciona_indicadores(df, periodo=20):
# Garman-Klass Volatility (VOLATILIDADE)
    print('Calculando indicadores de VOLATILIDADE:')
    print('       Volatilidade de Garman-Klass')
    df['garman_klauss_vol'] = (((np.log(df['high']) - np.log(df['low']))**2)/2) - (2*np.log(2)-1) * ((np.log(df['close']) - np.log(df['open']))**2)
# Bollinger Bands (VOLATILIDADE)
    print('       Bandas de Bollinger')
    df['bb_low'] = pandas_ta.bbands(close=np.log1p(df['close']),
                                    length=periodo).iloc[:, 0]
    df['bb_mid'] = pandas_ta.bbands(close=np.log1p(df['close']),
                                    length=periodo).iloc[:, 1]
    df['bb_high'] = pandas_ta.bbands(close=np.log1p(df['close']),
                                     length=periodo).iloc[:, 2]
# Average True Range (ATR) (VOLATILIDADE)
    print('       Average True Range (ATR)')
    atr = pandas_ta.atr(high=df['high'], low=df['low'],
                        close=df['close'], length=periodo)
    df['atr'] = atr.sub(atr.mean()).div(atr.std())
# ROC (VOLATILIDADE)
    print('       ROC')
    df['roc'] = pandas_ta.roc(df['close'], length=periodo)
# RSI (TENDENCIA)
    print('Calculando indicadores de TENDENCIA:')
    print('       RSI')
    df['rsi'] = pandas_ta.rsi(close=df['close'], length=periodo)
# MACD (TENDENCIA)
    print('       MACD')
    macd = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
    df['macd'] = macd.sub(macd.mean()).div(macd.std())
# Média Móvel curta (24 - 6 horas) (TENDENCIA)
    print('       Média móvel curta (6 horas)')
    df['mm24'] = pandas_ta.sma(df['close'], length=24)
# Média Móvel média (192 - 2 dias) (TENDENCIA)
    print('       Média móvel média (2 dias)')
    df['mm192'] = pandas_ta.sma(df['close'], length=192)
# Média Móvel longa (672 - 7 dias) (TENDENCIA)
    print('       Média móvel longa (1 semana)')
    df['mm672'] = pandas_ta.sma(df['close'], length=672)
# Supertrend (TENDENCIA)
    print('       Supertrend')
    df['supertrend'] = pandas_ta.supertrend(high=df['high'],
                                            low=df['low'],
                                            close=df['close'],
                                            offset=1)['SUPERTd_7_3.0']
#
    print('Informações adicionadas ao dataframe com sucesso. Remover NaNs manualmente.')


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


###
# BACKTESTING
###

# Definições dos indicadores:
# supertrend: sinal de compra (1) ou de venda (-1)
# médias móveis: se uma média móvel mais curta estiver abaixo de uma média móvel
#                mais longa, sinal de compra. O reverso é sinal de venda.
# volatilidade: maior volatilidade indica maior mudança de preços, menor
#               volatilidade indica maior estabilidade na tendência

# IDEIA1: usando cinco indicadores
# - Quando pelo menos 4 indicadores derem sinal de compra, comprar (fatias de 20%).
# - Quando pelo menos 3 indicadores (2 para um viés mais conservador) derem sinal de venda, sair da posição.
# - Necessário: saldo inicial (já calcula as fatias de compra), quantidade inicial do ativo, quantidade atual do ativo

historico = valores_historicos(dias=(365*4))
adiciona_indicadores(historico, (24*4))

historico = historico.dropna()

historico.tail(10)

plt.plot(historico.index, df['open'])
plt.plot(historico.index, df['close'])
plt.title('DJIA Open and Close Prices')
plt.xlabel('Date')
plt.ylabel('Price')


# Create a basic line plot for the Close prices
fig, ax1 = plt.subplots()
ax1.plot(historico['close'], color='blue', label='Preço de fechamento')
ax1.set_xlabel('Tempo')
ax1.set_ylabel('Preço de fechamento do ativo', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
# Create a twin axis for the High_minus_Low variable
ax2 = ax1.twinx()
ax2.plot(historico['mm672'], color='green', label='Média Móvel Longa (7 dias)')
ax2.set_ylabel('Média Móvel Longa', color='green')
ax2.tick_params(axis='y', labelcolor='green')
# Add a title and show the plot
plt.title('Gráfico Histórico do valor do ativo\ncom linha média móvel longa')
plt.show()

#
#
#
#
#
#
# Final do arquivo, só serve para testar coisas e não tem nada de importante
