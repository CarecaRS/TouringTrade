import pandas as pd  # Necessário para a carteira da Binance
import binance.enums  # Responsável pelo trading
import datetime  # Necessário para o histórico dos ativos
import requests  # Histórico dos ativos
import math  # necessário para as ordens da Binance
import json  # Histórico dos ativos
import time  # Necessário para o Touring (time.sleep())
import pandas_ta  # Calcula os indicadores de tendência
from binance.client import Client  # Binance
import smtplib  # necessário para o e-mail
# Abaixo: importação da API da Binance e dados do e-mail
# Isso tudo do arquivo local keys.py
from keys import api_secret_trade, api_key_trade, email_sender, email_personal, email_pwd
%autoindent OFF  # Uso pessoal, em função da minha IDE (NeoVIM)

# TO-DO LIST
#
# Vamos imaginar que esse algoritmo funcione *muito* bem. Eventualmente pode-se chegar a um ponto
# em que cada ordem registrada tenha um peso significativo na dinâmica do mercado (imaginemos,
# por exemplo, ordens de US$100mil). Para tentar solucionar isso, programar uma verificação do
# histórico das últimas N ordens processadas pelo agente (N sendo a quantidade de ordens das últimas
# 24h, por exemplo), de modo a poder mensurar um montante ótimo de negociação que tenha o menor
# impacto possível.

####################################################
#                                                  #
#   Definição das funçõs utilizadas pelo Touring   #
#                                                  #
####################################################

###
# NOTIFICAÇÕES POR E-MAIL
###
# Notificação de compra
def email_compra(saldos_iniciais=None, saldo_usd=None, saldo_ticker=None, preco_ticker=None, patrimonio=None, qtde=None, fatia=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparando valores para envio da mensagem de compra...')
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades BTC
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    subject = f'Touring: compra de {ticker[:3]}s realizada!'
    body = (f'Acabei de realizar uma ordem de compra!\n\n\
            Ativo negociado: {ticker[:3]}\n\
            Valor atual do ativo: US${round(preco_ticker, 2)}\n\
            Valor que eu investi: US${round(fatia, 2)}\n\
            Quantidade comprada: {'{:.5f}'.format(qtde)} {ticker[:3]}\n\n\
            Total investido atualmente: US${round((saldo_ticker*preco_ticker), 2)}\n\
            Quantidade total de {ticker[:3]} em carteira: {'{:.5f}'.format(saldo_ticker)} {ticker[:3]}s\n\
            Patrimonio atual (saldo+invest) calculado: US${round(patrimonio, 2)}\n\n\
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
def email_venda(saldos_iniciais=None, saldo_usd=None, saldo_ticker=None, preco_ticker=None, patrimonio=None, qtde=None, fatia=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparando valores para envio da mensagem de venda...')
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades BTC
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    subject = f'Touring: venda de {ticker[:3]}s realizada!'
    body = (f'Acabei de realizar uma ordem de venda!\n\n\
            Ativo negociado: {ticker[:3]}\n\
            Valor atual do ativo: US${round(preco_ticker, 2)}\n\
            Valor de venda: US${round(fatia, 2)}\n\
            Quantidade vendida: {'{:.5f}'.format(qtde)} {ticker[:3]}\n\n\
            Total que permanece investido: US${round(saldo_ticker * preco_ticker, 2)}\n\
            Quantidade total de {ticker[:3]} em carteira: {'{:.5f}'.format(saldo_ticker)} {ticker[:3]}s\n\
            Patrimonio atual (saldo+invest) calculado: US${round(patrimonio, 2)}\n\n\
            Pode ficar tranquilo que eu coordeno outras saidas e as entradas conforme meus parametros ;)\n\
            Ate mais!')
    message = (f'Subject: {subject}\n\n{body}')
    print('Enviando e-mail de venda agora.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail enviado com sucesso.')


# Notificação de venda quando é zerado o estoque do ativo negociado
def email_venda_zerado(saldos_iniciais=None, saldo_usd=None, saldo_ticker=None, preco_ticker=None, patrimonio=None, qtde=None, fatia=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    print('Preparando valores para envio da mensagem de venda...')
    saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
    saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades BTC
    preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
    patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
    subject = f'Touring: posicoes de {ticker[:3]}s zeradas!'
    body = (f'Acabei de realizar a ultima ordem de venda do saldo disponivel de {ticker[:3]}s!\n\n\
            Ativo negociado: {ticker[:3]}\n\
            Valor atual do ativo: US${round(preco_ticker, 2)}\n\
            Valor de venda: US${round(fatia, 2)}\n\
            Quantidade vendida: {'{:.5f}'.format(qtde)} {ticker[:3]}\n\n\
            Total que permanece investido: US${round(saldo_ticker * preco_ticker, 2)}\n\
            Quantidade total de {ticker[:3]} em carteira: {'{:.5f}'.format(saldo_ticker)} {ticker[:3]}s\n\
            Patrimonio atual (saldo+invest) calculado: US${round(patrimonio, 2)}\n\n\
            Assim que forem realizadas outras compras eu volto a coordenar as saidas seguintes, pode ficar sossegado ;)\n\
            Ate mais!')
    message = (f'Subject: {subject}\n\n{body}')
    print('Enviando e-mail de venda agora.')
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_personal, email_pwd)
        smtp.sendmail(email_sender, email_personal, message)
    print('E-mail enviado com sucesso.')


# Relatório semanal
def email_relatorio(temp=None, patrimonio=None):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    subject = 'Oi chefe, aqui eh o Touring! Estou trazendo teu relatorio semanal :D'
    print('Preparando valores para envio da mensagem...')
    semana = temp['Semana'].max()-1
    mask = temp['Semana'] == semana
    var_estrategia = (temp.loc[mask, 'PatrimonioTotal'][0]/temp.loc[mask, 'PatrimonioTotal'].iloc[-1])-1
    var_ativo = (temp.loc[mask, 'ValorUnitario'][0]/temp.loc[mask, 'ValorUnitario'].iloc[-1])-1
    mask_compra = temp.loc[mask, 'CV'] == 'compra'
    mask_venda = temp.loc[mask, 'CV'] == 'venda'
    body = (f'Aqui eu trago seu resumo semanal de desempenho!\n\n\
            Patrimonio total hoje: US${round(patrimonio, 2)}\n\n\
            Ativo negociado: {ticker[:3]}\n\
            Rendimento da estrategia: {round(var_estrategia*100, 4)}%\n\
            Oscilacao do ativo: {round(var_ativo*100, 4)}%\n\
            Quantidade de trades de referencia: {len(temp.loc[mask_compra])} COMPRAS e {len(temp.loc[mask_venda])} VENDAS.\n\n\
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
    loose_data = [[float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])] for kline in dados]
    historico = pd.DataFrame(loose_data, columns=['open', 'high', 'low', 'close'])
    timestamps = [datetime.datetime.fromtimestamp(int(kline[0])/1000) for kline in dados]
    historico['timestamp'] = timestamps
    historico.set_index('timestamp', inplace=True)
    historico['par'] = tickers
    print('Requisição do histórico concluída.')
    return historico


###
# ORDEM DE COMPRA
###
def ordem_compra(ticker=None, quantity=None):
    cliente.order_market_buy(symbol=ticker,
                             quantity=f'{quantity:.5f}')


###
# ORDEM DE VENDA
###
def ordem_venda(ticker=None, quantity=None):
    cliente.order_market_sell(symbol=ticker,
                             quantity=f'{quantity:.5f}')


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
# ESTRATÉGIA DE COMPRA/VENDA
###
def estrategia_bitcoin(df=None, defasagem=6):
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
                # Se o preço de fechamento anterior for menor ou igual ao mínimo dos últimos
                # 'defasagem' períodos (ou seja, preço segue baixando), não libera compra
                if (df.loc[idx-1, 'close'] <= df.loc[idx-defasagem:idx-1, 'close'].min()):
                    compra.append(False)
                else:
                    # Passada a verificação acima, se a máxima de dois períodos anteriores
                    # estiver menor do que a máxima de agora E TAMBÉM a MM curta estiver
                    # maior que a MM longa, sinaliza compra
                    compra.append((df.loc[(idx-2), 'high'] < df.loc[idx, 'high']) &
                                  (df.loc[idx, 'mm24'] > df.loc[idx, 'mm672']))
        else:
            if idx >= 2:
                # Se a máxima de dois períodos anteriores estiver menor do que a máxima
                # de agora (ou seja, preço está subindo) e também a MM curta esteja acima
                # da MM longa, sinaliza compra
                compra.append((df.loc[(idx-2), 'high'] < df.loc[idx, 'high']) &
                              (df.loc[idx, 'mm24'] > df.loc[idx, 'mm672']))
            else:
                # Outras situações diferentes do estabelecido, sinaliza 'não-compra'
                compra.append(False)
    # Gera os sinais de venda
    for idx in df.index:
        if idx >= defasagem:
            # Se o preço de fechamento estiver em baixa seguida na última hora e também
            # a MM curta estiver abaixo do preço de abertura, marca como venda
            if ((df.loc[idx-5, 'close'] > df.loc[idx-4, 'close']) &
                    (df.loc[idx-4, 'close'] > df.loc[idx-3, 'close']) &
                    (df.loc[idx-3, 'close'] > df.loc[idx-2, 'close']) &
                    (df.loc[idx-2, 'close'] > df.loc[idx-1, 'close']) &
                    (df.loc[idx, 'open'] > df.loc[idx-1, 'mm24'])):
                venda.append(True)
            else:
                # Se não, registra 'não-venda'
                venda.append(False)
        elif idx < defasagem:
            if idx < 1:
                # Início da série temporal é desprezível na estratégia, registra sinal
                # de 'não-venda'
                venda.append(False)
            elif df.loc[idx, 'open'] < df.loc[idx-1, 'mm24']:
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
# TOURING
###
def touring(max_ordens=3, compra=None, venda=None, ticker=None):
    try:
        ledger = pd.read_csv('livro_contabil.csv')
        ledger = ledger.to_dict(orient='records')
    except:
        ledger = []
#    status = 0
    marcador = 1
    while cliente.get_system_status()['msg'] == 'normal':
        # faz verificação do sinal da Binance, se não estiver normal retorna erro (depois do 'else' lá embaixo)
        print('Binance online.\n')
        historico = valores_historicos(dias=8)  # busca o histórico do ativo
        adiciona_indicadores(historico)  # adiciona os indicadores utilizados
        print('Removendo NaNs e refazendo índice...')
        historico = historico.dropna()
        historico = historico.reset_index()  # limpa o df (acima) e faz o reset do índice
        estrategia_bitcoin(historico)  # gera os sinais de compra/venda da estratégia
        # Coleta dos saldos iniciais
        saldo_usd = float(cliente.get_asset_balance(asset='USDT')['free'])  # Resgata valor de unidades USDT
        saldo_ticker = float(cliente.get_asset_balance(asset=ticker[:3])['free'])  # Resgata valor de unidades BTC
        preco_ticker = float(cliente.get_avg_price(symbol=ticker)['price'])
        patrimonio = saldo_usd + (saldo_ticker * preco_ticker)
        saldos_iniciais = {'USD': saldo_usd, 'BTC': saldo_ticker, 'PatrimonioUSD': patrimonio}
        saldoBTCemUSD = saldo_ticker*preco_ticker
        filtros_btc = cliente.get_symbol_info(ticker)['filters']
        step_btc = float(filtros_btc[1]['minQty'])
        fatia = saldos_iniciais['PatrimonioUSD']/max_ordens
        carteira_full = max_ordens - round(saldoBTCemUSD/fatia)
        qtde = fatia/preco_ticker
        qtde = math.floor(qtde/step_btc)*step_btc
        # Se a carteira estiver cheia novamente, refaz o valor das fatias,
        # senão só segue para a análise dos sinais
        if carteira_full == max_ordens:
            fatia = saldos_iniciais['USD']/carteira_full
        else:
            pass
        # PROCESSAMENTO DE COMPRAS
        if historico.loc[(historico.shape[0]-1), 'sinal_est'] == 1:  # Sinal de Compra da estratégia
        # Verifica saldo em carteira. Se a carteira estiver vazia,
        # não tem recurso para comprar, então nem verifica os sinais
        # de compra. Se a carteira estiver cheia novamente, refaz o
        # valor das fatias
            if carteira_full == 0:
                print(f'\n   --> Sinal de compra, mas sem recursos para comprar mais nada\n')
                pass
            else:
                if carteira_full == max_ordens:
                    marcador += 1
                else:
                    pass
                ordem_compra(ticker=ticker, quantity=qtde)
                cv = 'compra'
#                status = 1
                ledger.append({'Data': datetime.datetime.now(),
                               'Semana': datetime.datetime.now().isocalendar()[1],
                               'Ativo': ticker[:3],
                               'CV': cv,
                               'Marcador': marcador,
                               'ValorUnitario': round(preco_ticker, 2),
                               'Quantia': '{:.5f}'.format(qtde),
                               'ValorNegociado': round(fatia, 2),
                               'PatrimonioTotal': round(patrimonio, 2)})
                email_compra(saldos_iniciais=saldos_iniciais,
                             saldo_usd=saldo_usd,
                             saldo_ticker=saldo_ticker,
                             preco_ticker=preco_ticker,
                             patrimonio=patrimonio,
                             qtde=qtde,
                             fatia=fatia)
                print(f'\n   --> Compra de US${round(fatia, 2)} equivalente a {'{:.5f}'.format(qtde)} {ticker[:3]+'s'} realizada!\n\n')
                pd.DataFrame(data=ledger).to_csv('livro_contabil.csv', index=False)
        # PROCESSAMENTO DE VENDAS
        elif historico.loc[(historico.shape[0]-1), 'sinal_est'] == -1:  # Sinal de Venda da estratégia
            if carteira_full == max_ordens:  # SE CARTEIRA 100% CHEIA DE GRANA, NÃO TEM O QUE VENDER
                pass
            else:
                ordem_venda(ticker=ticker, quantity=qtde)
                cv = 'venda'
                print(f'\n   --> Venda de {'{:.5f}'.format(qtde)} {ticker[:3]+'s'} realizada, equivalente a US${round(fatia, 2)}.')
                carteira_full += 1
                ledger.append({'Data': datetime.datetime.now(),
                               'Semana': datetime.datetime.now().isocalendar()[1],
                               'Ativo': ticker[:3],
                               'CV': cv,
                               'Marcador': marcador,
                               'ValorUnitario': round(preco_ticker, 2),
                               'Quantia': '{:.5f}'.format(qtde),
                               'ValorNegociado': round(fatia, 2),
                               'PatrimonioTotal': round(patrimonio, 2)})
                if carteira_full == 0:
                    print('\n\n   --> ***  Todas posições zeradas!  ***')
                    # O email não muda praticamente nada, só a informação de ativo zerado
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
#                status = -1
                pd.DataFrame(data=ledger).to_csv('livro_contabil.csv', index=False)
        else:
            print(f'\n   --> Estratégia sem sinais de compra ou venda para o período, esperando.\n')
            pass
        # ENVIO DO RELATÓRIO SEMANAL, SE MUDOU A SEMANA
        ledger_temp = pd.DataFrame(ledger)
        if len(ledger_temp) <= 2:
            pass
        else:
            if (ledger_temp.loc[ledger_temp.shape[0]-1, 'Semana'] - ledger_temp.loc[ledger_temp.shape[0]-2, 'Semana']) == 1:
                email_relatorio(temp=ledger_temp, patrimonio=patrimonio)
            else:
                pass
        time.sleep(60*15)  # Medida em segundos
    else:
        print('\n\n!!!! **** ATENÇÃO **** !!!!\n')
        print('!!!! BINANCE FORA DO AR !!!!\n')
        print('Não é possível seguir rodando.\n\n')
        smtp_server = 'smtp.gmail.com'  # início do protocolo de envio de e-mail quando Binance der erro
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
        print('E-mail enviado com sucesso.')  # final do protocolo de envio de e-mail quando Binance der erro


####################################################
#                                                  #
#            Trading Area a partir daqui           #
#                                                  #
####################################################
# Primeiro de tudo, capta as informações da Binance
carteira, cliente, infos = carteira_binance()
#
# O ticker é a moeda (ou o par de moedas, no caso da Binance) que está se negociando
ticker = 'BTCUSDT'  # Aqui, BTC adquirido/comprado com USDT
# Número máximo de ordens compradas ao mesmo tempo:
max_ordens = 3
#
touring(max_ordens=max_ordens, ticker=ticker)


####
# VERIFICAÇÕES diversas na Binance, caso necessárias:
###
carteira  # Contém os saldos
cliente  # API para chamar outras funções (como as ordens, por exemplo)
infos  # Dicionário com informações diversas

# Verifica as autorizações do cliente (trade/saque/depósito)
infos['canTrade']
infos['canWithdraw']
infos['canDeposit']

# Verifica a conta pela qual são feitas as negociações (margin/spot)
infos['accountType']

# Retorna o user ID na corretora
infos['uid']
