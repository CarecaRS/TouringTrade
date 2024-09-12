import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
# import binance.enums  # responsável pelo trading
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
# - Fazer um loop para que o sistema busque as informações históricas de
#   toda a lista do touring_index
# - Utilizar indicadores de volatilidade (verificar parâmetros) para
#   sinais de compra e venda (subcomprado e supercomprado)
# - Bolar algum jeito de verificar há quanto tempo está caindo, para
#   evitar comprar em cenários de tendência primária de queda (de repente
#   os próprios indicadores de volatilidade já suprem isso)
# - Pega o histórico do desempenho de CDI e o IBOV para fins de comparação
#   no último gráfico também.
# - Fazer duas funções (para compra e para venda), também armazenar a
#   carteira em um objeto separado (tipo portfolio), assim dá para agilizar
#   o código (eu acho) e o controle das quantidades e preços médios deve
#   ficar melhor
# - De repente montar estratégia que a venda se dê por stpo loss (tipo mínima
#   anterior ou algo assim) e também por stop gain (tipo X vezes a diferença
#   entre as duas últimas máximas ou algo nesse sentido)

###
# JÁ FEITO
#
# - Pega a relação dos maiores market caps para negociação: coinmarketcap.com
#   > o CoinMarketCap retorna apenas as 20 maiores moedas em volume de mercado
#   > Não tem pq pegar mais moedas porque por enquanto não se trabalhará com
#     cestas de ativos, apenas com C/V de ativo isolado
# - Criadas funções carteira(), valores_historicos() e adiciona_indicadores()
# - Criar marcadores para saber qual o valor de referência de cada compra.
#   Pensei em uma coluna nova ('marcador' ou algo assim), registro-base é
#   zero, na primeira compra já é passado para 1. Na venda, acontece a
#   reversão do sinal e o marcador aumenta em uma unidade.

###
# IDEIA1: pelo menos cinco indicadores recebendo os dados/calculando
# a cada tempo X.
# - Quando pelo menos 4 indicadores derem sinal de compra,
#   comprar (fatias de 20% por exemplo).
# - Quando pelo menos 3 indicadores (2 para um viés mais conservador)
#   derem sinal de venda, sair da posição.
# - Necessário: saldo inicial (já calcula as fatias de compra), quantidade
#   inicial do ativo, quantidade atual do ativo


###
# OBTENÇÃO DOS TICKERS DO COINMARKETCAP (registro para quando for necessário)
###
# coinmarketcap = pd.read_html('https://coinmarketcap.com/all/views/all/')[2]
# coinmarketcap = coinmarketcap.iloc[:, : 10].dropna()
# touring_index = list(coinmarketcap['Symbol'])  # tickers que poderão ser negociados

###
# ACESSO AO SISTEMA DA BINANCE
###
def carteira_binance():
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
    print('       MACD (original, normalizado e sinal)')
    macd = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
    df['macd'] = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
    df['macd_norm'] = macd.sub(macd.mean()).div(macd.std())
    df['macd_s'] = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 2]
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


###
# BACKTEST
###
def backtest(df, max_ordens=10, saldo_inicial=1000, compra=0, venda=0, tx_comissao = 0.001, grafico=False):
    # Definição inicial dos componentes utilizados em backtesting
    marcador = 1
    carteira_full = max_ordens  # Máximo de ordens abertas ao mesmo tempo
    periodo = df.copy()
    periodo['sinal_est'] = 0  # Cria sinais neutros
    periodo['cv'] = 0  # Cria estados neutros, sem ordem de compra ou venda
    periodo['marcador'] = 0  # Cria marcador de compra neutro
    periodo['saldo_inicial'] = 0.0
    periodo['saldo_final'] = 0.0
    periodo['saldo_cart'] = 0.0
    periodo['patrimonio'] = 0.0
    periodo.loc[compra, 'sinal_est'] = 1  # Registro backtest compra
    periodo.loc[venda, 'sinal_est'] = -1  # Registro backtest venda
    inicio = periodo.index[0]
    periodo.loc[inicio, 'saldo_inicial'] = saldo_inicial
    # Verifica se tem algum sinal de ordem de compra
    if periodo[periodo['sinal_est'] == 1]['sinal_est'].sum() == 0:
        print('\n\n###################################################################################')
        print('###                                                                             ###')
        print('###        >>> Estratégia sem sinal de COMPRA no período informado! <<<         ###')
        print('###                                                                             ###')
        print('###    Vai dar erro com "periodo" pq eu deletei para quebrar a função mesmo:    ###')
        print('###                                                                             ###')
        print('###################################################################################\n\n')
        del periodo
    else:
        pass
    if periodo[periodo['sinal_est'] == -1]['sinal_est'].sum() == 0:
        print('\n\n###################################################################################')
        print('###                                                                             ###')
        print('###         >>> Estratégia sem sinal de VENDA no período informado! <<<         ###')
        print('###                                                                             ###')
        print('###    Vai dar erro com "periodo" pq eu deletei para quebrar a função mesmo:    ###')
        print('###                                                                             ###')
        print('###################################################################################\n\n')
        del periodo
    else:
        pass
#
    for idx in periodo.index:
        status = 0
    # Recupera o saldo final anterior, igual ao inicial se for a primeira observação
        if idx == inicio:
            periodo.loc[idx, 'saldo_inicial'] = saldo_inicial
            periodo.loc[idx, 'patrimonio'] = saldo_inicial
        else:
            periodo.loc[idx, 'saldo_inicial'] = periodo.loc[(idx - 1), 'saldo_final']
    # Se a carteira estiver vazia, não tem recurso para comprar,
    # nem verifica os sinais de compra
    # E se a carteira estiver cheia novamente, refaz o valor das fatias
        if carteira_full == 0:
            print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). Sem recursos para comprar mais nada')
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
                    periodo.loc[idx, 'saldo_cart'] = fatia*(1-tx_comissao)
                else:
                    periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - 1), 'saldo_cart'] + (fatia*(1-tx_comissao))
                carteira_full -= 1
                status = 1
                periodo.loc[idx, 'marcador'] = marcador
                periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
                print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). Compra realizada!')
    # PROCESSAMENTO DE VENDAS
        elif periodo.loc[idx, 'sinal_est'] == -1:  # SINAL DE VENDA
            if carteira_full == max_ordens:  # SE CARTEIRA CHEIA, NÃO TEM O QUE VENDER
                pass
            else:
                periodo.loc[idx, 'cv'] = -1
                if idx == periodo.index[-1]:  # SE FOR ÚLTIMO PERÍODO, VENDE TODO SALDO AO PREÇO DO FECHAMENTO DE AGORA
                    valor_medio = periodo[periodo['marcador'] == periodo['marcador'].max()]['close'].mean()
                    variacao = (periodo.loc[(idx), 'close'] - valor_medio)/valor_medio
                    venda = (fatia + (fatia * variacao))*(1-tx_comissao)
                    periodo.loc[idx, 'saldo_final'] = venda + periodo.loc[idx, 'saldo_inicial']
                    print(f'Backtesting {round(((idx+1)/periodo.shape[0])*100, 2)}% ({idx+1} de {periodo.shape[0]}). Venda realizada!')
                    periodo.loc[idx, 'saldo_cart'] = periodo.loc[(idx - 1), 'saldo_cart'] - fatia
                    periodo.loc[idx, 'marcador'] = marcador*-1
                    periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
                    carteira_full += 1
                    print(f'Backtesting finalizado! ***  Zerando posições em fim de período  ***')
                else:
                    valor_medio = periodo[periodo['marcador'] == periodo['marcador'].max()]['close'].mean()
                    variacao = (periodo.loc[(idx + 1), 'close'] - valor_medio)/valor_medio
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
    # PROCESSAMENTO DE MOMENTOS SEM NEGOCIAÇÃO
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
        if idx == periodo.index[-1]:  # SE FOR ÚLTIMO PERÍODO, VENDE TODO SALDO AO PREÇO DO FECHAMENTO DE AGORA
            valor_medio = periodo[periodo['marcador'] == periodo['marcador'].max()]['close'].mean()
            variacao = (periodo.loc[(idx), 'close'] - valor_medio)/valor_medio
            fatia = periodo.loc[(idx), 'saldo_cart']
            venda = (fatia + (fatia * variacao))*(1-tx_comissao)
            periodo.loc[idx, 'saldo_final'] = venda + periodo.loc[idx, 'saldo_inicial']
            periodo.loc[idx, 'saldo_cart'] = 0
            periodo.loc[idx, 'marcador'] = marcador*-1
            periodo.loc[idx, 'patrimonio'] = periodo.loc[idx, 'saldo_final'] + periodo.loc[idx, 'saldo_cart']
            print(f'Backtesting finalizado! ***  Zerando posições em fim de período  ***')
        else:
            pass
    periodo['rendimento'] = (periodo['patrimonio']/periodo['patrimonio'].iloc[0])-1
    periodo['ativo_acum'] = (periodo['close']/periodo['close'].iloc[0])-1
    saldo_final = round(periodo['saldo_final'].iloc[-1], 2) + round(periodo['saldo_cart'].iloc[-1], 2)
    saldo_maximo = round(periodo.patrimonio.max(), 2)
    rend_est = round(((saldo_final-saldo_inicial)/saldo_inicial)*100, 2)
    rend_at = round(((periodo.close.iloc[-1]/periodo.open.iloc[0])-1)*100, 2)
    rend_relat = round(((rend_est/rend_at)-1)*100, 2)
    print(f'\n\nSaldo inicial hipotético: R${saldo_inicial}')
    print(f'Saldo final: R${saldo_final}')
    print(f'Rendimento total da estratégia: {rend_est}%')
    print(f'Rendimento total do ativo: {rend_at}%')
    print(f'Beta do rendimento: {rend_relat}%')
    if rend_at > rend_est:
        print("\n\nRESULTADO: a estratégia NÃO SUPEROU o rendimento do ativo!")
    else:
        print("\n\nRESULTADO: Parabéns, a estratégia SUPEROU o rendimento do ativo!")
    print('\n\n   Características da estratégia:')
    print(f'Número de ordens simultâneas: {max_ordens}')
    print(f'Número de trades de compra realizados: {periodo[periodo['cv'] == 1]['cv'].sum()}')
    print(f'Número de trades de venda realizados: {abs(periodo[periodo['cv'] == -1]['cv'].sum())}')
    print(f'Intervalo das observações: ' + str(intervalo) + 'm')
    print(f'Patrimônio máximo no período: R${saldo_maximo}')
    print(f'Valor máximo do ativo no período: R${periodo.close.max()}')
    print(f'Valor mínimo do ativo no período: R${periodo.close.min()}')
    if grafico == True:
    # Cria as flags de entrada e saída
        df[['entrada', 'saida']] = 0
        mask = df['marcador'] != 0
        for i in df[mask]['marcador']:
            if i > 0:
                for idx1 in (df[df['marcador'] == i]).index:
                    df.loc[idx1, 'entrada'] = 1
            elif i < 0:
                for idxm1 in (df[df['marcador'] == i]).index:
                    df.loc[idxm1, 'saida'] = 1
            else:
                pass
        scatter_entrada = []
        scatter_saida = []
        for point in df[(df.entrada == 1)].index:
            scatter_entrada.append(df.loc[point, ['timestamp', 'ativo_acum']])
        for point in df[(df.saida == 1)].index:
            scatter_saida.append(df.loc[point, ['timestamp', 'ativo_acum']])
        # Gráfico com as flags criadas
        plt.plot(df.set_index(keys='timestamp')['ativo_acum'],
                 color='orange', label='Rendimento do Ativo',
                 zorder=5)
        plt.plot(df.set_index(keys='timestamp')['rendimento'],
                 color='magenta', label='Rendimento da Estratégia',
                 zorder=7)
        plt.xlabel("Tempo")
        plt.ylabel("Rentabilidade")
        plt.title('Gráfico comparativo da rentabilidade\nAtivo x Estratégia')
        plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
                    y=pd.DataFrame(scatter_entrada)['ativo_acum'],
                    color='green',
                    marker='^',
                    label='Ponto de entrada',
                    zorder=10)
        plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
                    y=pd.DataFrame(scatter_saida)['ativo_acum'],
                    color='red',
                    marker='v',
                    label='Ponto de saída',
                    zorder=10)
        plt.legend()
        plt.show()
    elif grafico == False:
        pass
    else:
        print('\n*Não foi possível desenhar o gráfico!*\nHiperparâmetro "grafico" deve ser True ou False, informado qualquer outra coisa.')
    return periodo


def backtest_summary(df, max_ordens=10, saldo_inicial=1000, grafico=False):
    saldo_final = round(df['saldo_final'].iloc[-1], 2) + round(df['saldo_cart'].iloc[-1], 2)
    saldo_maximo = round(df.patrimonio.max(), 2)
    rend_est = round(((saldo_final-saldo_inicial)/saldo_inicial)*100, 2)
    rend_at = round(((df.close.iloc[-1]/df.open.iloc[0])-1)*100, 2)
    rend_relat = round(((rend_est/rend_at)-1)*100, 2)
    print(f'\n\nSaldo inicial hipotético: R${saldo_inicial}')
    print(f'Saldo final: R${saldo_final}')
    print(f'Rendimento total da estratégia: {rend_est}%')
    print(f'Rendimento total do ativo: {rend_at}%')
    print(f'Beta do rendimento: {rend_relat}%')
    if rend_at > rend_est:
        print("\n\nRESULTADO: a estratégia NÃO SUPEROU o rendimento do ativo!")
    else:
        print("\n\nRESULTADO: Parabéns, a estratégia SUPEROU o rendimento do ativo!")
    print('\n\n   Características da estratégia:')
    print(f'Número de ordens simultâneas: {max_ordens}')
    print(f'Número de trades de compra realizados: {df[df['cv'] == 1]['cv'].sum()}')
    print(f'Número de trades de venda realizados: {abs(df[df['cv'] == -1]['cv'].sum())}')
    print(f'Intervalo das observações: ' + str(intervalo) + 'm')
    print(f'Patrimônio máximo no período: R${saldo_maximo}')
    print(f'Valor máximo do ativo no período: R${df.close.max()}')
    print(f'Valor mínimo do ativo no período: R${df.close.min()}')
    if grafico == True:
    # Cria as flags de entrada e saída
        df[['entrada', 'saida']] = 0
        mask = df['marcador'] != 0
        for i in df[mask]['marcador']:
            if i > 0:
                for idx1 in (df[df['marcador'] == i]).index:
                    df.loc[idx1, 'entrada'] = 1
            elif i < 0:
                for idxm1 in (df[df['marcador'] == i]).index:
                    df.loc[idxm1, 'saida'] = 1
            else:
                pass
        scatter_entrada = []
        scatter_saida = []
        for point in df[(df.entrada == 1)].index:
            scatter_entrada.append(df.loc[point, ['timestamp', 'ativo_acum']])
        for point in df[(df.saida == 1)].index:
            scatter_saida.append(df.loc[point, ['timestamp', 'ativo_acum']])
        # Gráfico com as flags criadas
        plt.plot(df.set_index(keys='timestamp')['ativo_acum'],
                 color='orange', label='Rendimento do Ativo',
                 zorder=5)
        plt.plot(df.set_index(keys='timestamp')['rendimento'],
                 color='magenta', label='Rendimento da Estratégia',
                 zorder=7)
        plt.xlabel("Tempo")
        plt.ylabel("Rentabilidade")
        plt.title('Gráfico comparativo da rentabilidade\nAtivo x Estratégia')
        plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
                    y=pd.DataFrame(scatter_entrada)['ativo_acum'],
                    color='green',
                    marker='^',
                    label='Ponto de entrada',
                    zorder=10)
        plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
                    y=pd.DataFrame(scatter_saida)['ativo_acum'],
                    color='red',
                    marker='v',
                    label='Ponto de saída',
                    zorder=10)
        plt.legend()
        plt.show()
    elif grafico == False:
        pass
    else:
        print('\n*Não foi possível desenhar o gráfico!*\nHiperparâmetro "grafico" deve ser True ou False, informado qualquer outra coisa.')


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


#########
# CRIAÇÃO DAS FLAGS DE ENTRADA E SAÍDA
# (uso de banco de dados aleatório)
#########

thiago[['entrada', 'saida']] = 0
mask = thiago['marcador'] != 0
for i in thiago[mask]['marcador']:
    if i > 0:
        for idx1 in (thiago[thiago['marcador'] == i]).index:
            thiago.loc[idx1, 'entrada'] = 1
    elif i < 0:
        for idxm1 in (thiago[thiago['marcador'] == i]).index:
            thiago.loc[idxm1, 'saida'] = 1
    else:
        pass

# Gráfico com as flags criadas
plt.plot(thiago.set_index(keys='timestamp')['ativo_acum'],
         color='orange', label='Rendimento do Ativo',
         zorder=5)
plt.plot(thiago.set_index(keys='timestamp')['rendimento'],
         color='magenta', label='Rendimento da Estratégia',
         zorder=7)
plt.xlabel("Tempo")
plt.ylabel("Rentabilidade")
plt.title('Gráfico comparativo da rentabilidade\nAtivo x Estratégia')
plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
            y=pd.DataFrame(scatter_entrada)['ativo_acum'],
            color='green',
            marker='^',
            label='Ponto de entrada',
            zorder=10)
plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
            y=pd.DataFrame(scatter_saida)['ativo_acum'],
            color='red',
            marker='v',
            label='Ponto de saída',
            zorder=10)
plt.legend()
plt.show()


scatter_entrada = []
scatter_saida = []
for point in thiago[(thiago.entrada == 1)].index:
    scatter_entrada.append(thiago.loc[point, ['timestamp', 'ativo_acum']])
for point in thiago[(thiago.saida == 1)].index:
    scatter_saida.append(thiago.loc[point, ['timestamp', 'ativo_acum']])

pd.DataFrame(scatter_entrada)
scatter_saida

thiago

###
# BACKTESTING
###

intervalo = 15
historico = valores_historicos(dias=(180), intervalo=str(str(intervalo)+'m'), ticker='BTCUSDT')
adiciona_indicadores(historico)
historico = historico.dropna()
historico = historico.reset_index()


# 6,78%
teste_compra = []
defasagem = 6  # cada unidade representa 15min, logo '24' representa 6h, x4 para fechar um dia e x7 para uma semana
for idx in historico.index:
    if idx >= defasagem:
        # Se o preço de fechamento estiver em baixa seguida na última hora não libera compra
        if ((historico.loc[idx-4, 'open'] > historico.loc[idx-3, 'open']) &
                (historico.loc[idx-3, 'open'] > historico.loc[idx-2, 'open']) &
                (historico.loc[idx-2, 'open'] > historico.loc[idx-1, 'open']) &
                (historico.loc[idx-1, 'open'] > historico.loc[idx, 'open']) &
                (historico.loc[idx, 'mm672'] > historico.loc[idx, 'mm24'])):
            teste_compra.append(False)
        else:
            if (historico.loc[idx-1, 'close'] <= historico.loc[idx-defasagem:idx-1, 'close'].min()):
                teste_compra.append(False)
            else:
                teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                    (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
    else:
        if idx >= 2:
            teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
        else:
            teste_compra.append(False)

teste_venda = historico['open'] < historico['mm672']  # Filtro backtest venda

ordens = 5
thiago = backtest(historico, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=True)

backtest_summary(thiago, max_ordens=ordens, grafico=True)


# 7,68%
teste_compra = []
defasagem = 6  # '24' representa 6h, x4 para fechar um dia e x7 para uma semana
for idx in historico.index:
    if idx >= defasagem:
        # Se o preço de fechamento estiver em baixa seguida na última hora não libera compra
        if ((historico.loc[idx-4, 'open'] > historico.loc[idx-3, 'open']) &
                (historico.loc[idx-3, 'open'] > historico.loc[idx-2, 'open']) &
                (historico.loc[idx-2, 'open'] > historico.loc[idx-1, 'open']) &
                (historico.loc[idx-1, 'open'] > historico.loc[idx, 'open']) &
                (historico.loc[idx, 'mm672'] > historico.loc[idx, 'mm24'])):
            teste_compra.append(False)
        else:
            if (historico.loc[idx-1, 'close'] <= historico.loc[idx-defasagem:idx-1, 'close'].min()):
                teste_compra.append(False)
            else:
                teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                    (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
    else:
        if idx >= 2:
            teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
        else:
            teste_compra.append(False)
teste_venda = historico['close'] < historico['mm672']  # Filtro backtest venda

ordens = 5
thiago = backtest(historico, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=True)

backtest_summary(thiago, max_ordens=ordens, grafico=True)


# 6,44%
teste_compra = []
defasagem = 24  # '24' representa 6h, x4 para fechar um dia e x7 para uma semana
for idx in historico.index:
    if idx >= defasagem:
        # Se o preço de fechamento estiver em baixa seguida na última hora não libera compra
        if ((historico.loc[idx-4, 'open'] > historico.loc[idx-3, 'open']) &
                (historico.loc[idx-3, 'open'] > historico.loc[idx-2, 'open']) &
                (historico.loc[idx-2, 'open'] > historico.loc[idx-1, 'open']) &
                (historico.loc[idx-1, 'open'] > historico.loc[idx, 'open']) &
                (historico.loc[idx, 'mm672'] > historico.loc[idx, 'mm24'])):
            teste_compra.append(False)
        else:
            if (historico.loc[idx-1, 'close'] <= historico.loc[idx-defasagem:idx-1, 'close'].min()):
                teste_compra.append(False)
            else:
                teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                    (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
    else:
        if idx >= 2:
            teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
        else:
            teste_compra.append(False)
teste_venda = historico['close'] < historico['mm672']  # Filtro backtest venda

ordens = 5
thiago = backtest(historico, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=True)

# 6,39%
teste_compra = []
for idx in historico.index:
    if idx >= 3:
        if ((historico.loc[idx-3, 'close'] > historico.loc[idx-2, 'close']) &
                (historico.loc[idx-2, 'close'] > historico.loc[idx-1, 'close']) &
                (historico.loc[idx-1, 'close'] > historico.loc[idx, 'close'])):
            teste_compra.append(False)
        else:
            teste_compra.append((historico.loc[(idx-2), 'high'] < historico.loc[idx, 'high']) &
                                (historico.loc[idx, 'mm24'] > historico.loc[idx, 'mm672']))
    else:
        teste_compra.append(False)
teste_venda = historico['close'] < historico['mm672']


# Gráfico das médias móveis
plt.plot(historico.set_index(keys='timestamp')['mm672'], color='green', label='Média Móvel Longa (1 semana)')
plt.plot(historico.set_index(keys='timestamp')['mm192'], color='blue', label='Média Móvel Média (2 dias)')
plt.plot(historico.set_index(keys='timestamp')['mm24'], color='red', label='Média Móvel Curta (6 horas)')
plt.plot(historico.set_index(keys='timestamp')['close'], color='gray', label='Preço de fechamento do ativo')
plt.xlabel("Tempo")
plt.ylabel("Valor do ativo")
plt.title('Gráfico do histórico do valor do ativo')
plt.legend()
plt.show()
