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
import smtplib
# Importação da API da Binance e dados do e-mail
# Isso tudo do arquivo local keys.py
from keys import api_secret, api_key, email_sender, email_personal, email_pwd
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
# NOTIFICAÇÕES POR E-MAIL
###
# Notificação de compra
def email_compra(df):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparando valores para envio da mensagem de compra...')
    ativo = df.loc[idx, 'par']
    valor_ativo = df.loc[idx, 'open']
    valor_investido = df.loc[idx, 'saldo_cart'] - df.loc[idx-1, 'saldo_cart']
    qtde_comprada = valor_investido/valor_ativo
    patrimonio = df.loc[idx, 'patrimonio']
    subject = 'Touring: compra realizada!'
    body = (f'Acabei de realizar uma ordem de compra!\n\n\
            Ativo negociado: {ativo[:3]}\n\
            Valor atual do ativo: R${round(valor_ativo, 2)}\n\
            Valor atual investido: R${round(valor_investido, 2)}\n\
            Quantidade comprada: {round(qtde_comprada, 8)} {ativo[:3]}\n\n\
            Total investido atualmente: R${round(df.loc[idx, 'saldo_cart'], 2)}\n\
            Quantidade total de {ativo[:3]} em carteira: (algum fetch da Binance aqui)\n\
            Patrimonio atual (saldo+invest) calculado: R${round(patrimonio, 2)}\n\n\
            Pode ficar tranquilo que eu coordeno outras entradas e as saidas conforme meus parametros ;)\n\
            Ate mais!')
    message = (f'Subject: {subject}\n\n{body}')
    print('Enviando e-mail de compra agora.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail enviado com sucesso.')


# Notificação de venda
def email_venda(df):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparando valores para envio da mensagem de venda...')
    ativo = df.loc[idx, 'par']
    valor_ativo = df.loc[idx, 'open']
    valor_venda = abs(df.loc[idx, 'saldo_cart'] - df.loc[idx-1, 'saldo_cart'])
    qtde_vendida = valor_venda/valor_ativo
    patrimonio = df.loc[idx, 'patrimonio']
    subject = 'Touring: venda realizada!'
    body = (f'Acabei de realizar uma ordem de venda!\n\n\
            Ativo negociado: {ativo[:3]}\n\
            Valor do ativo: R${round(valor_ativo, 2)}\n\
            Valor de venda: R${round(valor_venda, 2)}\n\
            Quantidade vendida: {round(qtde_vendida, 8)} {ativo[:3]}\n\n\
            Total que permanece investido agora: R${round(df.loc[idx, 'saldo_cart'], 2)}\n\
            Quantidade total de {ativo[:3]} em carteira: (algum fetch da Binance aqui)\n\
            Patrimonio atual (saldo+invest) calculado: R${round(patrimonio, 2)}\n\n\
            Pode ficar tranquilo que eu coordeno outras saidas e as entradas conforme meus parametros ;)\n\
            Ate mais!')
    message = (f'Subject: {subject}\n\n{body}')
    print('Enviando e-mail de venda agora.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail enviado com sucesso.')


# Relatório semanal (precisa ajuste)
def email_relatorio(df):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    subject = 'Oi chefe, aqui eh o Touring'
    print('Preparando valores para envio da mensagem...')
    body = (f'Aqui eu trago seu resumo semanal de desempenho!\n\n\
            Patrimonio total hoje: R${round(df.loc[df.shape[0]-1]['patrimonio'], 2)}\n\
            Ativo negociado: {df.loc[df.shape[0]-1]['par']}\n\
            Rendimento da estrategia: {round(df.loc[df.shape[0]-1]['rendimento']*100, 4)}%\n\
            Oscilacao do ativo: {round(df.loc[df.shape[0]-1]['ativo_acum']*100, 4)}%\n\
            Quantidade de trades de referencia: {abs(df.loc[df.shape[0]-1]['marcador'])}\n\n\
            Por hoje eh soh chefe! Em breve eu retorno com mais um relatorio :D')
    message = (f'Subject: {subject}\n\n{body}')
    print('Enviando e-mail agora.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail enviado com sucesso.')


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
    if dias < 8:
        print('\n\n\n\n*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*\n\n')
        print('IMPORTANTE! A quantidade de dias deve ser 8 ou mais dias! Este histórico NÃO VAI FUNCIONAR!\n\n')
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
#    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4]), float(kline[5]), float(kline[7]), float(kline[8])] for kline in dados]
#    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close', 'volume_ativo', 'volume_financeiro', 'qtde_negocios'])
    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])] for kline in dados]
    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close'])
    timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in dados]
    historico['timestamp'] = timestamps
    historico.set_index('timestamp', inplace=True)
    historico['par'] = tickers
#    print('Reduzindo magnitude do volume financeiro')
#    historico['volume_financeiro'] = historico['volume_financeiro']/1e6
    print('Requisição do histórico concluída.')
    return historico


###
# CÁLCULO DOS INDICADORES
# - Os que estão comentados não são utilizados até o presente momento
###
def adiciona_indicadores(df, periodo=20):
# Garman-Klass Volatility (VOLATILIDADE)
    print('Calculando indicadores de VOLATILIDADE:')
    print('       Volatilidade de Garman-Klass não calculada')
#    df['garman_klauss_vol'] = (((np.log(df['high']) - np.log(df['low']))**2)/2) - (2*np.log(2)-1) * ((np.log(df['close']) - np.log(df['open']))**2)
# Bollinger Bands (VOLATILIDADE)
    print('       Bandas de Bollinger não calculadas')
#    df['bb_low'] = pandas_ta.bbands(close=np.log1p(df['close']),
#                                    length=periodo).iloc[:, 0]
#    df['bb_mid'] = pandas_ta.bbands(close=np.log1p(df['close']),
#                                    length=periodo).iloc[:, 1]
#    df['bb_high'] = pandas_ta.bbands(close=np.log1p(df['close']),
#                                     length=periodo).iloc[:, 2]
# Average True Range (ATR) (VOLATILIDADE)
    print('       Average True Range (ATR) não calculada')
#    atr = pandas_ta.atr(high=df['high'], low=df['low'],
#                        close=df['close'], length=periodo)
#    df['atr'] = atr.sub(atr.mean()).div(atr.std())
# ROC (VOLATILIDADE)
    print('       ROC não calculado')
#    df['roc'] = pandas_ta.roc(df['close'], length=periodo)
# RSI (TENDENCIA)
    print('Calculando indicadores de TENDENCIA:')
    print('       RSI não calculado')
#    df['rsi'] = pandas_ta.rsi(close=df['close'], length=periodo)
# MACD (TENDENCIA)
    print('       MACD (original, normalizado e sinal) não calculada')
#    macd = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
#    df['macd'] = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 0]
#    df['macd_norm'] = macd.sub(macd.mean()).div(macd.std())
#    df['macd_s'] = pandas_ta.macd(close=df['close'], length=periodo).iloc[:, 2]
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
    print('       Supertrend não calculado')
#    df['supertrend'] = pandas_ta.supertrend(high=df['high'],
#                                            low=df['low'],
#                                            close=df['close'],
#                                            offset=1)['SUPERTd_7_3.0']
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
                email_compra(periodo)
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
                    email_venda(periodo)
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
                    email_venda(periodo)
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
        print("\n\nRESULTADO: a estratégia NÃO SUPEROU o rendimento do ativo no período considerado!")
    else:
        print("\n\nRESULTADO: Parabéns, a estratégia SUPEROU o rendimento do ativo no período considerado!")
    print('\n\n   Características da estratégia:')
    print(f'Número de ordens simultâneas: {max_ordens}')
    print(f'Número de trades de compra realizados: {periodo[periodo['cv'] == 1]['cv'].sum()}')
    print(f'Número de trades de venda realizados: {abs(periodo[periodo['cv'] == -1]['cv'].sum())}')
    print(f'Intervalo das observações: ' + str(intervalo) + 'm')
    print(f'Patrimônio máximo no período: R${saldo_maximo}')
    print(f'Valor máximo do ativo no período: R${periodo.close.max()}')
    print(f'Valor mínimo do ativo no período: R${periodo.close.min()}')
    if grafico == True:
        # Criação das flags entrada/saída
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
        # Gera os pontos do scatter
        scatter_entrada = []
        scatter_saida = []
        for point in periodo[(periodo.entrada == 1)].index:
            scatter_entrada.append(periodo.loc[point, ['timestamp', 'close']])
        for point in periodo[(periodo.saida == 1)].index:
            scatter_saida.append(periodo.loc[point, ['timestamp', 'close']])
        # Cria os dois gráficos
        plt.subplot(211)
        plt.plot(periodo.set_index(keys='timestamp')['mm672'],
                 color='green',
                 label='MM Longa (1 semana)')
        plt.plot(periodo.set_index(keys='timestamp')['mm192'],
                 color='blue',
                 label='MM Média (2 dias)')
        plt.plot(periodo.set_index(keys='timestamp')['mm24'],
                 color='red',
                 label='MM Curta (6 horas)')
        plt.plot(periodo.set_index(keys='timestamp')['close'],
                 color='gray',
                 label='Preço de fechamento do ativo')
        plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
                    y=pd.DataFrame(scatter_entrada)['close'],
                    color='green',
                    marker='^',
                    label='Ponto de entrada',
                    zorder=10)
        plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
                    y=pd.DataFrame(scatter_saida)['close'],
                    color='red',
                    marker='v',
                    label='Ponto de saída',
                    zorder=10)
        plt.xlabel("Tempo")
        plt.ylabel("Valor do ativo")
        plt.title('Gráfico do histórico do valor do ativo')
        plt.legend()
        plt.subplot(212)
        plt.plot(periodo.set_index(keys='timestamp')['ativo_acum'],
                 color='orange', label='Rendimento do Ativo',
                 zorder=5)
        plt.plot(periodo.set_index(keys='timestamp')['rendimento'],
                 color='magenta', label='Rendimento da Estratégia',
                 zorder=7)
        plt.xlabel("Tempo")
        plt.ylabel("Rentabilidade")
        plt.title('Gráfico comparativo da rentabilidade (Ativo x Estratégia)')
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
        print("\n\nRESULTADO: a estratégia NÃO SUPEROU o rendimento do ativo no período considerado!")
    else:
        print("\n\nRESULTADO: Parabéns, a estratégia SUPEROU o rendimento do ativo no período considerado!")
    print('\n\n   Características da estratégia:')
    print(f'Número de ordens simultâneas: {max_ordens}')
    print(f'Número de trades de compra realizados: {df[df['cv'] == 1]['cv'].sum()}')
    print(f'Número de trades de venda realizados: {abs(df[df['cv'] == -1]['cv'].sum())}')
    print(f'Intervalo das observações: ' + str(intervalo) + 'm')
    print(f'Patrimônio máximo no período: R${saldo_maximo}')
    print(f'Valor máximo do ativo no período: R${df.close.max()}')
    print(f'Valor mínimo do ativo no período: R${df.close.min()}')
    if grafico == True:
        # Criação das flags entrada/saída
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
        # Gera os pontos do scatter
        scatter_entrada = []
        scatter_saida = []
        for point in df[(df.entrada == 1)].index:
            scatter_entrada.append(df.loc[point, ['timestamp', 'close']])
        for point in df[(df.saida == 1)].index:
            scatter_saida.append(df.loc[point, ['timestamp', 'close']])
        # Cria os dois gráficos
        plt.subplot(211)
        plt.plot(df.set_index(keys='timestamp')['mm672'],
                 color='green',
                 label='MM Longa (1 semana)')
        plt.plot(df.set_index(keys='timestamp')['mm192'],
                 color='blue',
                 label='MM Média (2 dias)')
        plt.plot(df.set_index(keys='timestamp')['mm24'],
                 color='red',
                 label='MM Curta (6 horas)')
        plt.plot(df.set_index(keys='timestamp')['close'],
                 color='gray',
                 label='Preço de fechamento do ativo')
        plt.scatter(x=pd.DataFrame(scatter_entrada)['timestamp'],
                    y=pd.DataFrame(scatter_entrada)['close'],
                    color='green',
                    marker='^',
                    label='Ponto de entrada',
                    zorder=10)
        plt.scatter(x=pd.DataFrame(scatter_saida)['timestamp'],
                    y=pd.DataFrame(scatter_saida)['close'],
                    color='red',
                    marker='v',
                    label='Ponto de saída',
                    zorder=10)
        plt.xlabel("Tempo")
        plt.ylabel("Valor do ativo")
        plt.title('Gráfico do histórico do valor do ativo')
        plt.legend()
        plt.subplot(212)
        plt.plot(df.set_index(keys='timestamp')['ativo_acum'],
                 color='orange', label='Rendimento do Ativo',
                 zorder=5)
        plt.plot(df.set_index(keys='timestamp')['rendimento'],
                 color='magenta', label='Rendimento da Estratégia',
                 zorder=7)
        plt.xlabel("Tempo")
        plt.ylabel("Rentabilidade")
        plt.title('Gráfico comparativo da rentabilidade (Ativo x Estratégia)')
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


###
# BACKTESTING
#
# Ativos de maior valor unitário Binance
# BTCUSDT - bitcoin
# ETHUSDT - ethereum
# YFIUSDT - yearn.finance (?)
#
# Ativos de maior valor unitário CoinMarketCap
# Bitcoin (BTC)
# Tether Gold (XAUt)
# Ethereum (ETH)
# Maker (MKR)
# BNB (BNB)
###

intervalo = 15
historico = valores_historicos(dias=(8),
                               intervalo=str(str(intervalo)+'m'),
                               ticker='BTCUSDT')
adiciona_indicadores(historico)
historico = historico.dropna()
historico = historico.reset_index()


###
# Estratégia 1 - Boa para ETH
###
# BACKTEST 365d:
# 275,17% sobre BTC, com 3 ordens
# 241,75% sobre ETH, com 3 ordens
# 58,79% sobre YIF, com 3 ordens
#
# BACKTEST 180d:
# 8,48% sobre BTC, com 3 ordens
# 7,83% sobre ETH, com 3 ordens
# -16,11%% sobre YIF, com 3 ordens
##########################################################
#                 Parâmetros de COMPRA:                  #
# - Se o ativo estiver em queda na última hora, não      #
#   libera a compra;                                     #
# - Se o preço de fechamento em t-1 for menor que o      #
#   mínimo dos últimos {defasagem} períodos, não libera  #
#   a compra;                                            #
# - Se a máxima atual for maior do que a máxima em t-2   #
#   e se a MM curta estiver acima da alta, compra;       #
# - Qualquer coisa diferente disso, não compra.          #
##########################################################
teste_compra = []
teste_venda = []
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
##########################################################
#                  Parâmetros de VENDA:                  #
# - 4 períodos consecutivos em queda;                    #
# - Preço de abertura em t menor do que a MM Curta em    #
#   t-1.                                                 #
##########################################################
for idx in historico.index:
    if idx >= defasagem:
        # Se o preço de fechamento estiver em baixa seguida na última hora marca como venda
        if ((historico.loc[idx-5, 'close'] > historico.loc[idx-4, 'close']) &
                (historico.loc[idx-4, 'close'] > historico.loc[idx-3, 'close']) &
                (historico.loc[idx-3, 'close'] > historico.loc[idx-2, 'close']) &
                (historico.loc[idx-2, 'close'] > historico.loc[idx-1, 'close']) &
                (historico.loc[idx, 'open'] > historico.loc[idx-1, 'mm24'])):
            teste_venda.append(True)
        elif (historico.loc[idx, 'mm192'] < historico.loc[idx-1, 'mm672']):
            teste_venda.append(True)
        else:
            teste_venda.append(False)
    elif idx < defasagem:
        if idx < 1:
            teste_venda.append(False)
        elif (historico.loc[idx, 'mm192'] < historico.loc[idx-1, 'mm672']):
            teste_venda.append(True)
        else:
            teste_venda.append(False)
    else:
        print('Algo de muito bizarro aconteceu, essa print não estava prevista!')


ordens = 3
thiago = backtest(historico, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=True)

backtest_summary(thiago, max_ordens=ordens, grafico=True)


#
#


#
#


#
#


#
#


#
#


#
#


#
#


#
#

###
# Estratégia 2 - Perfeita para Bitcoin
###
# BACKTEST 365d:
# 576,10% em BTC, com 3 ordens
# 237,24% em ETH, com 3 ordens
# 42,89% em YIF, com 3 ordens
#
# BACKTEST 180d:
# 23,15% sobre BTC, com 3 ordens
# 7,83% sobre ETH, com 3 ordens
# -40,28% em YIF

##########################################################
#                 Parâmetros de COMPRA:                  #
# - Se o ativo estiver em queda na última hora, não      #
#   libera a compra;                                     #
# - Se o preço de fechamento em t-1 for menor que o      #
#   mínimo dos últimos {defasagem} períodos, não libera  #
#   a compra;                                            #
# - Se a máxima atual for maior do que a máxima em t-2   #
#   e se a MM curta estiver acima da alta, compra;       #
# - Qualquer coisa diferente disso, não compra.          #
##########################################################
teste_compra = []
teste_venda = []
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
##########################################################
#                  Parâmetros de VENDA:                  #
# - 4 períodos consecutivos em queda;                    #
# - Preço de abertura em t menor do que a MM Curta em    #
#   t-1.                                                 #
##########################################################
for idx in historico.index:
    if idx >= defasagem:
        # Se o preço de fechamento estiver em baixa seguida na última hora marca como venda
        if ((historico.loc[idx-5, 'close'] > historico.loc[idx-4, 'close']) &
                (historico.loc[idx-4, 'close'] > historico.loc[idx-3, 'close']) &
                (historico.loc[idx-3, 'close'] > historico.loc[idx-2, 'close']) &
                (historico.loc[idx-2, 'close'] > historico.loc[idx-1, 'close']) &
                (historico.loc[idx, 'open'] > historico.loc[idx-1, 'mm24'])):
            teste_venda.append(True)
        else:
            teste_venda.append(False)
    elif idx < defasagem:
        if idx < 1:
            teste_venda.append(False)
        elif historico.loc[idx, 'open'] < historico.loc[idx-1, 'mm24']:
            teste_venda.append(True)
        else:
            teste_venda.append(False)
    else:
        print('Algo de muito bizarro aconteceu, essa print não estava prevista!')


ordens = 3
thiago = backtest(historico, saldo_inicial=2000, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=False)

historico

thiago

thiago.loc[3]

email_relatorio(thiago)

backtest_summary(thiago, max_ordens=ordens, grafico=True)
