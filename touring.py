import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
import binance.enums  # responsável pelo trading
import datetime
import requests
import math
import json
import time
import pandas_ta
from binance.client import Client
import smtplib
# Importação da API da Binance e dados do e-mail
# Isso tudo do arquivo local keys.py
from keys import api_secret_trade, api_key_trade, email_sender, email_personal, email_pwd
%autoindent OFF


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
    cliente = Client(api_key_trade, api_secret_trade)
    if cliente.get_system_status()['msg'] != 'normal':
        print('\n\n!!!! **** ATENÇÃO **** !!!!\n')
        print('!!!! BINANCE FORA DO AR !!!!\n')
        print('Não foi possível obter as informações\n\n')
    else:
        print('\nBinance on-line. Solicitando informações.')
        infos = cliente.get_account()  # carrega as infos do usuário
        if infos['canTrade'] == False:
            print('\n\nATENÇÃO! Usuário impedido de negociar, favor verificar status junto à Binance!')
        else:
            # Recupera as informações da carteira do usuário
            carteira = pd.DataFrame(infos['balances'])
            numeros = ['free', 'locked']
            carteira[numeros] = carteira[numeros].astype(float)  # transforma obj em float
            mask = carteira[numeros][carteira[numeros] > 0] \
                   .dropna(how='all').index  # filtro dos ativos com saldo
            print('Realizando limpeza geral da carteira... Tudo pronto.')
            carteira = carteira.iloc[mask]  # mantem apenas os ativos com saldo
            black_list = ['NFT', 'SHIB', 'BTTC']  # blacklist de ativos
            mask = carteira[carteira['asset'].isin(black_list)].index  # registra o índice dos black
            carteira.drop(mask, axis=0, inplace=True)  # dropa ativos black
            return carteira, cliente, infos


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
    print('Calculando indicadores de TENDENCIA:')
# Média Móvel curta (24 - 6 horas) (TENDENCIA)
    print('       Média móvel curta (6 horas)')
    df['mm24'] = pandas_ta.sma(df['close'], length=24)
# Média Móvel média (192 - 2 dias) (TENDENCIA)
    print('       Média móvel média (2 dias)')
    df['mm192'] = pandas_ta.sma(df['close'], length=192)
# Média Móvel longa (672 - 7 dias) (TENDENCIA)
    print('       Média móvel longa (1 semana)')
    df['mm672'] = pandas_ta.sma(df['close'], length=672)
    print('Informações adicionadas ao dataframe com sucesso.')


###
# TOURING
###
def touring(max_ordens=None, saldo_inicial=None, compra=None, venda=None, ticker=None):
    while cliente.get_system_status()['msg'] == 'normal':
        if cliente.get_system_status()['msg'] != 'normal':
            print('\n\n!!!! **** ATENÇÃO **** !!!!\n')
            print('!!!! BINANCE FORA DO AR !!!!\n')
            print('Não é possível seguir rodando.\n\n')
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
            print('Enviando e-mail agora.')
            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                smtp.starttls()
                smtp.login(email_personal, email_pwd)
                smtp.sendmail(email_sender, email_personal, message)
            print('E-mail enviado com sucesso.')
            break
        else:
            print('Binance online.')
            historico = valores_historicos(dias=9)  # busca o histórico do ativo
            adiciona_indicadores(historico)  # adiciona os indicadores utilizados
            print('Removendo NaNs e refazendo índice...')
            historico = historico.dropna()
            historico = historico.reset_index()
            estrategia_bitcoin(historico) # gera os sinais de compra/venda da estratégia
            return historico
            max_ordens += 9
            time.sleep(5)  # Medida em segundos
            if max_ordens >= 20:
                break


tx_comissao = float(infos['commissionRates']['maker'])
ticker = 'BTCUSDT'
ordens = 3
touring(max_ordens=ordens)

#

#

#


status = 0
carteira_full = max_ordens  # Número máximo de posições abertas ao mesmo tempo
saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])
saldo_btc = float(cliente.get_asset_balance(asset=ticker[:3])['free'])
saldo_inicial = {'USD': saldo_usd, 'BTC': saldo_btc}
# Verifica saldo em carteira. Se a carteira estiver vazia,
# não tem recurso para comprar, então nem verifica os sinais
# de compra. Se a carteira estiver cheia novamente, refaz o
# valor das fatias
if carteira_full == 0:
    print(f'Sem recursos para comprar mais nada')
    pass
elif carteira_full == max_ordens:
    fatia = saldo_inicial['USD']/carteira_full
else:
    pass
    # PROCESSAMENTO DE COMPRAS HUEHUEHUE
        if thiago.loc[(thiago.shape[0]-1), 'sinal_est'] == 0:  # tem que ser feito nesse sentido aqui
        if historico.loc[-1:]['sinal_est'] == 1:  # SINAL DE COMPRA
            if carteira_full == 0:  # SE CARTEIRA VAZIA, NÃO TEM COMO COMPRAR
                pass
            else:
                historico.loc[idx, 'cv'] = 1
                historico.loc[idx, 'saldo_final'] = historico.loc[idx, 'saldo_inicial'] - fatia
                if idx == historico.index[0]:
                    historico.loc[idx, 'saldo_cart'] = fatia*(1-tx_comissao)
                else:
                    historico.loc[idx, 'saldo_cart'] = historico.loc[(idx - 1), 'saldo_cart'] + (fatia*(1-tx_comissao))
                carteira_full -= 1
                status = 1
                historico.loc[idx, 'marcador'] = marcador
                historico.loc[idx, 'patrimonio'] = historico.loc[idx, 'saldo_final'] + historico.loc[idx, 'saldo_cart']
                email_compra(historico)
                print(f'Backtesting {round(((idx+1)/historico.shape[0])*100, 2)}% ({idx+1} de {historico.shape[0]}). Compra realizada!')
    # PROCESSAMENTO DE VENDAS
        elif historico.loc[idx, 'sinal_est'] == -1:  # SINAL DE VENDA
            if carteira_full == max_ordens:  # SE CARTEIRA CHEIA, NÃO TEM O QUE VENDER
                pass
            else:
                historico.loc[idx, 'cv'] = -1
                if idx == historico.index[-1]:  # SE FOR ÚLTIMO PERÍODO, VENDE TODO SALDO AO PREÇO DO FECHAMENTO DE AGORA
                    valor_medio = historico[historico['marcador'] == historico['marcador'].max()]['close'].mean()
                    variacao = (historico.loc[(idx), 'close'] - valor_medio)/valor_medio
                    venda = (fatia + (fatia * variacao))*(1-tx_comissao)
                    historico.loc[idx, 'saldo_final'] = venda + historico.loc[idx, 'saldo_inicial']
                    print(f'Backtesting {round(((idx+1)/historico.shape[0])*100, 2)}% ({idx+1} de {historico.shape[0]}). Venda realizada!')
                    historico.loc[idx, 'saldo_cart'] = historico.loc[(idx - 1), 'saldo_cart'] - fatia
                    historico.loc[idx, 'marcador'] = marcador*-1
                    historico.loc[idx, 'patrimonio'] = historico.loc[idx, 'saldo_final'] + historico.loc[idx, 'saldo_cart']
                    carteira_full += 1
                    print(f'Backtesting finalizado! ***  Zerando posições em fim de período  ***')
                    email_venda(historico)
                else:
                    valor_medio = historico[historico['marcador'] == historico['marcador'].max()]['close'].mean()
                    variacao = (historico.loc[(idx + 1), 'close'] - valor_medio)/valor_medio
                    venda = (fatia + (fatia * variacao))*(1-tx_comissao)
                    historico.loc[idx, 'saldo_final'] = venda + historico.loc[idx, 'saldo_inicial']
                    print(f'Backtesting {round(((idx+1)/historico.shape[0])*100, 2)}% ({idx+1} de {historico.shape[0]}). Venda realizada!')
                    historico.loc[idx, 'saldo_cart'] = historico.loc[(idx - 1), 'saldo_cart'] - fatia
                    historico.loc[idx, 'marcador'] = marcador*-1
                    historico.loc[idx, 'patrimonio'] = historico.loc[idx, 'saldo_final'] + historico.loc[idx, 'saldo_cart']
                    carteira_full += 1
                    email_venda(historico)
                    if carteira_full == max_ordens:
                        print(f'Backtesting {round(((idx+1)/historico.shape[0])*100, 2)}% ({idx+1} de {historico.shape[0]}). ***  Todas posições zeradas!  ***')
                        marcador += 1
                    else:
                        pass
                    status = -1
        else:
            pass
    # PROCESSAMENTO DE MOMENTOS SEM NEGOCIAÇÃO
        if status == 0:
            print('Sem movimentações por enquanto.')
        else:
            pass
       # AQUI É O FINAL DO WHILE HUEHUEHUE


###
# Extraído do código, de repente se utiliza ainda
###
'''
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
'''

###
# Touring
###
touring(df, max_ordens=0, saldo_inicial=0, compra=0, venda=0)

df = ['busca o histórico']
saldo_inicial = ['pega saldo USDTC da Binance']
compra = ['mask de compra aqui']
venda = ['mask de venda aqui']


#
#


#


#


# Capta as informações da Binance
carteira, cliente, infos = carteira_binance()

tx_comissao = float(infos['commissionRates']['maker'])
conta_tipo = infos['accountType']
user_uid = infos['uid']
ticker = 'BTCUSDT'
max_ordens = 3

carteira

saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])
saldo_btc = float(cliente.get_asset_balance(asset=ticker[:3])['free'])
saldo_usd
saldo_btc

###
# Criação de ordens efetivas
###
ordem_compra = client.order_market_buy(
        symbol=ticker,
        quantity=100)

ordem_venda = client.order_market_sell(
        symbol=ticker,
        quantity=100)


###
# Criação de ordens de teste
###
preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
filtros_btc = cliente.get_symbol_info(ticker)['filters']
step_btc = float(filtros_btc[1]['minQty'])
valor_invest = (2000/6)/3
qtde = valor_invest/preco_ticker
qtde = math.floor(qtde/step_btc)*step_btc

ordem_teste = cliente.create_test_order(
        symbol=ticker,
        side='BUY',
        type='MARKET',
        quantity=qtde)


thiago = valores_historicos(dias=8, intervalo='15m')
adiciona_indicadores(thiago)
thiago = thiago.dropna()
thiago = thiago.reset_index()
estrategia_bitcoin(thiago)

thiago.loc[(thiago.shape[0]-1), 'sinal_est']



def estrategia_bitcoin(df, defasagem=6):
    # Defaults:
    # defasagem = 6 -- fatias de 15min, '6' então equivale a 1h30min
    compra = []
    venda = []
    # Gera os sinais de compra
    for idx in df.index:
if idx >= defasagem:
            # Se o preço de fechamento estiver em baixa seguida na última hora não libera compra
            if ((df.loc[idx-4, 'open'] > df.loc[idx-3, 'open']) &
                    (df.loc[idx-3, 'open'] > df.loc[idx-2, 'open']) &
                    (df.loc[idx-2, 'open'] > df.loc[idx-1, 'open']) &
                    (df.loc[idx-1, 'open'] > df.loc[idx, 'open']) &
                    (df.loc[idx, 'mm672'] > df.loc[idx, 'mm24'])):
                compra.append(False)
            else:
                if (df.loc[idx-1, 'close'] <= df.loc[idx-defasagem:idx-1, 'close'].min()):
                    compra.append(False)
                else:
                    compra.append((df.loc[(idx-2), 'high'] < df.loc[idx, 'high']) &
                                        (df.loc[idx, 'mm24'] > df.loc[idx, 'mm672']))
        else:
            if idx >= 2:
                compra.append((df.loc[(idx-2), 'high'] < df.loc[idx, 'high']) &
                                    (df.loc[idx, 'mm24'] > df.loc[idx, 'mm672']))
            else:
                compra.append(False)
    # Gera os sinais de venda
    for idx in df.index:
        if idx >= defasagem:
            # Se o preço de fechamento estiver em baixa seguida na última hora marca como venda
            if ((df.loc[idx-5, 'close'] > df.loc[idx-4, 'close']) &
                    (df.loc[idx-4, 'close'] > df.loc[idx-3, 'close']) &
                    (df.loc[idx-3, 'close'] > df.loc[idx-2, 'close']) &
                    (df.loc[idx-2, 'close'] > df.loc[idx-1, 'close']) &
                    (df.loc[idx, 'open'] > df.loc[idx-1, 'mm24'])):
                venda.append(True)
            else:
                venda.append(False)
        elif idx < defasagem:
            if idx < 1:
                venda.append(False)
            elif df.loc[idx, 'open'] < df.loc[idx-1, 'mm24']:
                venda.append(True)
            else:
                venda.append(False)
        else:
            print('Algo de muito bizarro aconteceu, essa print não estava prevista!')
    df['sinal_est'] = 0  # Cria sinais neutros
    df.loc[compra, 'sinal_est'] = 1  # Registro backtest compra
    df.loc[venda, 'sinal_est'] = -1  # Registro backtest venda


#


ordens = 3
thiago = backtest(historico, saldo_inicial=2000, max_ordens=ordens, compra=teste_compra, venda=teste_venda, grafico=False)
#backtest_summary(thiago, max_ordens=ordens, grafico=True)



####
# VERIFICAÇÕES diversas na Binance, caso necessárias:
###
# Verifica as autorizações do cliente (trade/saque/depósito)
infos['canTrade']
infos['canWithdraw']
infos['canDeposit']

# Verifica a conta pela qual são feitas as negociações (margin/spot)
infos['accountType']

# Retorna o user ID na corretora
infos['uid']



