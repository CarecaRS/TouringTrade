import pandas as pd
import numpy as np
import binance.enums  # responsável pelo trading
from binance.client import Client
from keys import api_secret, api_key #  Importa a api do arquivo local 'keys.py'

###
# IDEIA1: pelo menos cinco indicadores recebendo os dados/calculando a cada segundo.
# - Quando pelo menos 4 indicadores derem sinal de compra, comprar (fatias de 20%).
# - Quando pelo menos 3 indicadores (2 para um viés mais conservador) derem sinal de venda, sair da posição.
# - Necessário: saldo inicial (já calcula as fatias de compra), quantidade inicial do ativo, quantidade atual do ativo


# Acesso ao sistema da Binance
cliente = Client(api_key, api_secret)

# Carrega as informações do usuário
infos = cliente.get_account()

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

# Recupera as informações da carteira do usuário
carteira = pd.DataFrame(infos['balances'])
numeros = ['free', 'locked']
carteira[numeros] = carteira[numeros].astype(float)  # transforma obj em float
mask = carteira[numeros][carteira[numeros] > 0] \
        .dropna(how='all').index  # filtro dos ativos com saldo
carteira = carteira.iloc[mask]  # mantem apenas os ativos com saldo

carteira

carteira.info()
