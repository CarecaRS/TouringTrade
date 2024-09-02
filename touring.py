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
def valores_historicos(ticker='BTCUSDT', dias=30, intervalo='15m'):
    '''valores_historicos(ticker, dias=30, intervalo='15m')
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


# Definições dos indicadores:
# supertrend: sinal de compra (1) ou de venda (-1)
# médias móveis: se uma média móvel mais curta estiver abaixo de uma média móvel
#                mais longa, sinal de compra. O reverso é sinal de venda.
# volatilidade: maior volatilidade indica maior mudança de preços, menor
#               volatilidade indica maior estabilidade na tendência

historico = valores_historicos(dias=(365))
adiciona_indicadores(historico, (24*4))
historico = historico.dropna()

periodo = historico[-(672*4*12):]  # gráfico do último mês
plt.plot(periodo['mm672'], color='green', label='Média Móvel Longa (1 semana)')
plt.plot(periodo['mm192'], color='blue', label='Média Móvel Média (2 dias)')
plt.plot(periodo['mm24'], color='red', label='Média Móvel Curta (6 horas)')
plt.plot(periodo['close'], color='gray', label='Preço de fechamento do ativo')
plt.xlabel("Tempo")
plt.ylabel("Valor do ativo")
plt.title('Gráfico do histórico do valor do ativo')
plt.legend()
plt.show()


###
# BACKTESTING
###

# ESTRATÉGIA 1: utilizando sinais apenas com a média curta
# - Preço > média curta = sinal de compra
# - Preço < média curta = sinal de venda
historico['sinal_est1'] = 0  # Cria sinais neutros
mask_compra = historico['close'] > historico['mm24']  # Filtro backtest compra
mask_venda = historico['close'] < historico['mm24']  # Filtro backtest venda
historico.loc[mask_compra, 'sinal_est'] = 1  # Registro backtest compra
historico.loc[mask_venda, 'sinal_est'] = -1  # Registro backtest venda
saldo_inicial = 1000  # Define um saldo inicial hipotético, em R$
#
max_ordens = 20
carteira_full = max_ordens  # Máximo de ordens abertas ao mesmo tempo
historico['cv'] = 0  # Cria estados neutros, sem ordem de compra ou venda
historico['saldo_inicial'] = 0.0
historico['saldo_final'] = 0.0
historico['saldo_cart'] = 0.0
periodo = historico.copy()  # gráfico das últimas 4 semanas (672 períodos de 15m em uma semana)
inicio = periodo.index[0]
periodo.loc[inicio, 'saldo_inicial'] = saldo_inicial
#
fatia = periodo.loc[periodo.index[0], 'saldo_inicial']/carteira_full
#
for idx in periodo.index:
#    if carteira_full == 5:
#        fatia = periodo.loc[idx, 'saldo_inicial']/carteira_full
#    else:
#        pass
    status = 0
# Recupera o saldo final anterior, igual ao inicial se for a primeira observação
    if idx == periodo.index[0]:
        periodo.loc[idx, 'saldo_inicial'] = saldo_inicial
    else:
        periodo.loc[idx, 'saldo_inicial'] = periodo.loc[(idx - pd.to_timedelta(15, unit='m')), 'saldo_final']
# Se a carteira estiver vazia, não tem recurso para comprar, nem verifica os sinais de compra
# E se a carteira estiver cheia novamente, refaz o valor das fatias
    if carteira_full == 0:
        print('Sem recursos para comprar nada :(')
        pass
    elif carteira_full == max_ordens:
        fatia = periodo.loc[idx, 'saldo_inicial']/carteira_full
    else:
        pass
# PROCESSAMENTO DE COMPRAS
    if periodo.loc[idx, 'sinal_est'] == 1:  # SINAL DE COMPRA
        if carteira_full == 0:  # SE CARTEIRA VAZIA, NÃO TEM COMO COMPRAR
            pass
        else:
            periodo.loc[idx, 'cv'] = 1
            periodo.loc[idx, 'saldo_final'] = periodo.loc[idx, 'saldo_inicial'] - fatia
            if idx == periodo.index[0]:
                periodo.loc[idx, 'saldo_cart'] = fatia
            else:
                periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - pd.to_timedelta(15, unit='m')), 'saldo_cart'] + fatia
            carteira_full -= 1
            status = 1
            print('Compra realizada!')
# PROCESSAMENTO DE VENDAS
    elif periodo.loc[idx, 'sinal_est'] == -1:  # SINAL DE VENDA
        if carteira_full == max_ordens:  # SE CARTEIRA CHEIA, NÃO TEM O QUE VENDER
            pass
        else:
            periodo.loc[idx, 'cv'] = -1
            if idx == periodo.index[-1]:
                pass
            else:
                variacao = (periodo.loc[(idx + pd.to_timedelta(15, unit='m')), 'close'] - periodo.loc[idx, 'close'])/periodo.loc[idx, 'close']
                venda = fatia + (fatia * variacao)
                periodo.loc[idx, 'saldo_final'] = venda + periodo.loc[idx, 'saldo_inicial']
                print('Venda realizada!')
                periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - pd.to_timedelta(15, unit='m')), 'saldo_cart'] - fatia
                carteira_full += 1
                status = -1
    else:
        pass
# PROCESSAMENTO DE MOMENTOS SEM NEGOCIAÇÃO
    if status == 0:
        if idx == periodo.index[0]:
            periodo.loc[idx, 'saldo_final'] = periodo.loc[idx, 'saldo_inicial']
        else:
            periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - pd.to_timedelta(15, unit='m')), 'saldo_cart']
            periodo.loc[idx, 'saldo_inicial'] = periodo.loc[(idx - pd.to_timedelta(15, unit='m')), 'saldo_final']
            periodo.loc[idx, 'saldo_final'] = periodo.loc[idx, 'saldo_inicial']
    else:
        pass
saldo_final = round(periodo['saldo_final'][-1], 2) + round(periodo['saldo_cart'][-1], 2)
print(f'\nSaldo final: R${saldo_final}')
print(f'Rendimento total do período: {round(((saldo_final-saldo_inicial)/saldo_inicial)*100,2)}%')
print('\n   Características da estratégia:')
print(f'Número de ordens simultâneas: {max_ordens}')

#
#

round(periodo['saldo_final'][-1], 2)

periodo[['sinal_est', 'cv', 'saldo_inicial', 'saldo_final', 'saldo_cart']].tail(20)
fatia
status
carteira_full

periodo['saldo_cart'].max()
#
#
#
#
#
#
# Final do arquivo, só serve para testar coisas e não tem nada de importante
